#!/usr/bin/env python3

import requests
import os
import argparse
import json
import re
from moviepy.editor import VideoFileClip
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)

def manually_parse_duration(duration_str):
    try:
        match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration_str)
        hours, minutes, seconds = 0, 0, 0
        if match.group(1):
            hours = int(match.group(1)[:-1])
        if match.group(2):
            minutes = int(match.group(2)[:-1])
        if match.group(3):
            seconds = int(match.group(3)[:-1])
        return hours * 3600 + minutes * 60 + seconds
    except Exception as e:
        print(f"Error in manually parsing duration: {e}")
        return None

def get_video_description(api_key, video_url):
    video_id = video_url.split("=")[-1]
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_id}&key={api_key}"
    response = requests.get(url)
    response_json = response.json()

    if "items" in response_json and response_json["items"]:
        video_description = response_json["items"][0]["snippet"]["description"]
        video_title = response_json["items"][0]["snippet"]["title"]
        video_duration = manually_parse_duration(response_json["items"][0]["contentDetails"]["duration"])
        return video_description, video_title, video_duration
    else:
        print("No items found in API response.")
        return None, None, None

def download_video(url, resolution=None, output_dir='.'):
    print(f"Starting to download video from {url}")

    try:
        yt = YouTube(url)
        stream = None

        if resolution:
            # Filter for streams that include both video and audio
            stream = yt.streams.filter(progressive=True, file_extension='mp4', res=resolution).first()

        # If the specific resolution is not found, try the best resolution available
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if not stream:
            raise Exception("No suitable stream found.")

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

    if os.path.exists(output_path):
        print(f"File '{output_path}' already exists. Skipping.")
        return

    try:
        with VideoFileClip(source_file) as video:
            trimmed_video = video.subclip(start_time, end_time)
            # Ensure audio is included in the output
            trimmed_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            print(f"Video trimmed successfully: {output_filename}")
    except Exception as e:
        print(f"Error in trimming video: {e}")


def process_videos(source, intervals, resolution, output_dir, total_duration, use_local=False, titles=None):
    source_file = source if use_local else download_video(source, resolution, output_dir)
    for i, interval in enumerate(intervals):
        start, end = interval[:2]
        title = titles[i] if titles else f'trimmed_video_{i}'
        output_filename = f"{sanitize_filename(title)}.mp4"
        # Removed total_duration from the function call
        trim_video(source_file, start, end, output_filename, output_dir)
    if not use_local:
        print(f"Removing original downloaded file: {source_file}")
        os.remove(source_file)


def extract_segments(api_key, url):
    description, video_title, video_duration = get_video_description(api_key, url)
    
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
    for i in range(len(timestamps)):
        start_time = timestamps[i]
        end_time = None if i + 1 == len(timestamps) else timestamps[i + 1]
        title = titles[i]
        intervals.append((start_time, end_time, title))

    return intervals, titles, video_title, video_duration

def main():
    print("Script started.")
    parser = argparse.ArgumentParser(description='Download and trim YouTube videos.')
    parser.add_argument('-url', type=str, help='URL of the YouTube video', required=True)
    parser.add_argument('-api_key', type=str, help='YouTube Data API key', required=True)
    parser.add_argument('-resolution', type=str, default=None, help='Resolution of the video (e.g., 720p, 1080p). If not specified, defaults to 720p, then 480p.')
    parser.add_argument('-extract_segments', action='store_true', help='Extract video segments from the video description and use them as intervals.')
    args = parser.parse_args()

    titles = None
    video_duration = None
    if args.extract_segments:
        intervals, titles, video_title, video_duration = extract_segments(args.api_key, args.url)
        if not intervals:
            print("No valid intervals extracted. Exiting the script.")
            return
    else:
        try:
            with open(args.intervals, 'r') as file:
                intervals = json.load(file)
            print("Intervals loaded successfully.")
        except Exception as e:
            print(f"Error reading intervals file: {e}")
            return

    if video_duration is None:
        print("Video duration not available. Exiting.")
        return

    sanitized_title = sanitize_filename(video_title)
    output_directory = os.path.join(os.getcwd(), sanitized_title)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    process_videos(args.url, intervals, args.resolution, output_directory, video_duration, titles=titles)

if __name__ == "__main__":
    main()
