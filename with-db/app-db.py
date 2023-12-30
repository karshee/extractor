#!/usr/bin/env python3

import requests
import os
import argparse
import json
import re
import psycopg2
from moviepy.editor import VideoFileClip
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

def add_video(youtube_url, title, total_duration):
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Video (YouTubeURL, Title, TotalDuration) VALUES (%s, %s, %s) RETURNING VideoID', 
                   (youtube_url, title, total_duration))
    video_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return video_id

def add_chapter(video_id, chapter_title, start_time, end_time):
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Chapter (VideoID, ChapterTitle, StartTime, EndTime) VALUES (%s, %s, %s, %s)', 
                   (video_id, chapter_title, start_time, end_time))
    conn.commit()
    cursor.close()
    conn.close()

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)  # Replace any non-alphanumeric character with an underscore


def get_video_description(api_key, video_url):
    video_id = video_url.split("=")[-1]
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    response = requests.get(url)
    response_json = response.json()

    if "items" in response_json and response_json["items"]:
        video_description = response_json["items"][0]["snippet"]["description"]
        video_title = response_json["items"][0]["snippet"]["title"]
        return video_description, video_title
    else:
        print("No items found in API response.")
        return None, None


def download_video(url, resolution=None, output_dir='.'):
    print(f"Starting to download video from {url}")

    try:
        yt = YouTube(url)
        if resolution:
            stream = yt.streams.filter(progressive=True, res=resolution).first()
            if not stream:
                print(f"Requested resolution {resolution} not available. Attempting default resolution.")
        if not resolution or not stream:
            stream = yt.streams.filter(progressive=True, res='720p').first()
            if not stream:
                print("720p resolution not available, falling back to 480p.")
                stream = yt.streams.filter(progressive=True, res='480p').first()
            if not stream:
                raise Exception("Neither 720p nor 480p resolutions are available.")
        output_path = os.path.join(output_dir, 'downloaded_video.mp4')
        stream.download(filename=output_path)
        print(f"Video downloaded successfully at resolution {stream.resolution}.")
        return output_path
    except AgeRestrictedError:
        print(f"Video {url} is age restricted, skipping.")
        return None
    except Exception as e:
        print(f"Error in downloading video: {e}")
        raise


def trim_video(source_file, start_time, end_time, output_filename, output_dir):
    output_path = os.path.join(output_dir, output_filename)

    # Check if file already exists
    if os.path.exists(output_path):
        print(f"File '{output_path}' already exists. Skipping.")
        return

    # Proceed with trimming if the file does not exist
    try:
        with VideoFileClip(source_file) as video:
            trimmed_video = video.subclip(start_time, end_time)
            trimmed_video.write_videofile(output_path)
        print(f"Video trimmed successfully: {output_filename}")
    except Exception as e:
        print(f"Error in trimming video: {e}")


def process_videos(source, intervals, resolution, output_dir, use_local=False, titles=None):
    source_file = source if use_local else download_video(source, resolution, output_dir)
    for i, interval in enumerate(intervals):
        start, end = interval[:2]
        title = titles[i] if titles else f'trimmed_video_{i}'
        output_filename = f"{sanitize_filename(title)}.mp4"
        trim_video(source_file, start, end, output_filename, output_dir)
    if not use_local:
        print(f"Removing original downloaded file: {source_file}")
        os.remove(source_file)


def extract_segments(api_key, url):
    description, video_title = get_video_description(api_key, url)
    
    if not description:
        print("No description available for video.")
        return None, None, None

    pattern = re.compile(r'(\d{1,2}:\d{2})\s*-?\s*(.*?)\s*(?=\d{1,2}:\d{2}|\Z)')
    matches = pattern.findall(description)

    if not matches:
        print("No segments found in the description.")
        return None, None, None

    timestamps = [match[0] for match in matches]
    titles = [match[1] for match in matches]

    intervals = []
    video_duration = None

    for i in range(len(timestamps)):
        start_time = timestamps[i]
        end_time = timestamps[i + 1] if i + 1 < len(timestamps) else None
        title = titles[i]

        if end_time is None and video_duration is not None:
            # Use the video duration as the end time for the last segment
            end_time = f"{int(video_duration//60):02}:{int(video_duration%60):02}"
        
        intervals.append((start_time, end_time, title))
    
    return intervals, titles, video_title

def main():
    parser = argparse.ArgumentParser(description='Download and trim YouTube videos.')
    parser.add_argument('-url', type=str, help='URL of the YouTube video', required=True)
    parser.add_argument('-api_key', type=str, help='YouTube Data API key', required=True)
    parser.add_argument('-resolution', type=str, default=None, help='Resolution of the video (e.g., 720p, 1080p). If not specified, defaults to 720p, then 480p.')
    parser.add_argument('-extract_segments', action='store_true', help='Extract video segments from the video description and use them as intervals.')
    args = parser.parse_args()

    # Create the database and tables
    create_database()

    description, video_title = get_video_description(args.api_key, args.url)
    if not description:
        print("No description available for video.")
        return

    # Assuming you have a way to fetch the total duration of the video
    # total_duration = get_video_total_duration(args.api_key, args.url)  # Implement this function
    total_duration = 0  # Placeholder, replace with actual duration

    # Store video information and get the generated video ID
    video_id = add_video(args.url, video_title, total_duration)

    if args.extract_segments:
        intervals, titles, _ = extract_segments(args.api_key, args.url)
        if not intervals:
            print("No valid intervals extracted. Exiting the script.")
            return

        # Store chapter information
        for i, (start_time, end_time, title) in enumerate(intervals):
            add_chapter(video_id, title, start_time, end_time)
    else:
        print("Chapter extraction not enabled. Exiting.")
        return

    sanitized_title = sanitize_filename(video_title)
    output_directory = os.path.join(os.getcwd(), sanitized_title)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    process_videos(args.url, intervals, args.resolution, output_directory, titles=titles)

if __name__ == "__main__":
    main()
