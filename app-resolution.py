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
    return re.sub(r'[^\w\-_\. ]', '_', name)  # Replace any non-alphanumeric character with an underscore


def get_video_description(api_key, video_url):
    video_id = video_url.split("=")[-1]
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    response = requests.get(url)
    response_json = response.json()

    if "items" in response_json and response_json["items"]:
        video_description = response_json["items"][0]["snippet"]["description"]
        return video_description
    else:
        print("No items found in API response.")
        return None

def get_video_id_from_url(url):
    return url.split('=')[-1]

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
    description = get_video_description(api_key, url)
    
    if not description:
        print("No description available for video.")
        return None, None

    # Updated regex pattern to match both '6:25 Title' and '6:25 - Title' formats
    pattern = re.compile(r'(\d{1,2}:\d{2})\s*-?\s*(.*?)\s*(?=\d{1,2}:\d{2}|\Z)')
    matches = pattern.findall(description)

    if not matches:
        print("No segments found in the description.")
        return None, None

    # Extracting timestamps and titles
    timestamps = [match[0] for match in matches]
    titles = [match[1] for match in matches]

    # Pairing timestamps with titles
    intervals = [(timestamps[i], timestamps[i+1] if i+1 < len(timestamps) else "end", titles[i]) for i in range(len(timestamps))]

    return intervals, titles


def main():
    print("Script started.")
    parser = argparse.ArgumentParser(description='Download and trim YouTube videos.')
    parser.add_argument('-intervals', type=str, help='Path to the JSON file containing time intervals', default='config.json')
    parser.add_argument('-url', type=str, help='URL of the YouTube video', required=True)
    parser.add_argument('-api_key', type=str, help='YouTube Data API key', required=True)
    parser.add_argument('-resolution', type=str, default=None, help='Resolution of the video (e.g., 720p, 1080p). If not specified, defaults to 720p, then 480p.')
    parser.add_argument('-extract_segments', action='store_true', help='Extract video segments from the video description and use them as intervals.')
    args = parser.parse_args()

    video_id = get_video_id_from_url(args.url)
    output_directory = os.path.join(os.getcwd(), video_id)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    titles = None
    if args.extract_segments:
        intervals, titles = extract_segments(args.api_key, args.url)
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

    process_videos(args.url, intervals, args.resolution, output_directory, titles=titles)

if __name__ == "__main__":
    main()
