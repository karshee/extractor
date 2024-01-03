#!/usr/bin/env python3

import requests
import os
import argparse
import json
import re
import yt_dlp
from moviepy.editor import VideoFileClip

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

def get_video_info(api_key, video_url):
    try:
        video_id = video_url.split("=")[-1]
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_id}&key={api_key}"
        response = requests.get(url)
        response_json = response.json()

        if "items" in response_json and response_json["items"]:
            video_description = response_json["items"][0]["snippet"]["description"]
            video_title = response_json["items"][0]["snippet"]["title"]
            video_duration = manually_parse_duration(response_json["items"][0]["contentDetails"]["duration"])
            return video_description, video_title, video_duration
    except Exception as e:
        print(f"Error retrieving video info: {e}")
    return None, None, None

def load_intervals_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            raw_intervals = json.load(file)
        return [(start, end, f'Chapter {i}') for i, (start, end) in enumerate(raw_intervals, start=1)]
    except Exception as e:
        print(f"Error reading intervals file: {e}")
    return None

def download_video(url, output_dir='.'):
    print(f"Starting to download video from {url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, 'downloaded_video.%(ext)s'),
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(output_dir, 'downloaded_video.mp4')

def convert_time_str_to_seconds(time_str):
    if time_str == 'end':
        return None
    h, m, s = [int(part) for part in time_str.split(':')]
    return h * 3600 + m * 60 + s

def trim_video(source_file, start_time, end_time, output_filename, output_dir, video_duration):
    output_path = os.path.join(output_dir, output_filename)

    if os.path.exists(output_path):
        print(f"File '{output_path}' already exists. Skipping.")
        return

    try:
        start_seconds = convert_time_str_to_seconds(start_time)
        end_seconds = convert_time_str_to_seconds(end_time) if end_time else video_duration

        with VideoFileClip(source_file) as video:
            trimmed_video = video.subclip(start_seconds, end_seconds)
            trimmed_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            print(f"Video trimmed successfully: {output_filename}")
    except Exception as e:
        print(f"Error in trimming video: {e}")

def load_intervals_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            raw_intervals = json.load(file)
        return [(start, end, f'Chapter {i}') for i, (start, end) in enumerate(raw_intervals, start=1)]
    except Exception as e:
        print(f"Error reading intervals file: {e}")
    return None

def setup_output_directory(video_title):
    sanitized_title = sanitize_filename(video_title)
    output_directory = os.path.join(os.getcwd(), sanitized_title)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    return output_directory

def process_videos(source, intervals, output_dir, video_duration, use_local=False, titles=None):
    source_file = source if use_local else download_video(source, output_dir)
    if not source_file:
        print("Source video could not be retrieved.")
        return

    if not intervals:
        print("No intervals to process. Exiting.")
        return

    for interval in intervals:
        if len(interval) != 3:
            print(f"Invalid interval format: {interval}")
            continue
        start, end, _ = interval
        title = sanitize_filename(interval[2])  # Use the third element of the interval as the title
        output_filename = f"{title}.mp4"
        trim_video(source_file, start, end, output_filename, output_dir, video_duration)

    if not use_local:
        print(f"Removing original downloaded file: {source_file}")
        os.remove(source_file)

def main():
    print("Script started.")
    parser = argparse.ArgumentParser(description='Download and optionally segment YouTube videos.')
    parser.add_argument('-url', type=str, help='URL of the YouTube video', required=True)
    parser.add_argument('-api_key', type=str, help='YouTube Data API key', required=True)
    parser.add_argument('-intervals_path', type=str, help='Path to the JSON file containing time intervals', required=False)
    parser.add_argument('-download_only', action='store_true', help='Download the video without processing intervals')
    args = parser.parse_args()

    video_description, video_title, video_duration = get_video_info(args.api_key, args.url)
    if video_duration is None:
        print("Video duration not available. Exiting.")
        return

    output_directory = setup_output_directory(video_title)

    if args.download_only:
        download_video(args.url, output_directory)
        print(f"Video downloaded to {output_directory}")
    else:
        if args.intervals_path:
            intervals = load_intervals_from_file(args.intervals_path)
            if not intervals:
                print("Error loading intervals. Exiting.")
                return
            process_videos(args.url, intervals, output_directory, video_duration, use_local=False, titles=None)
        else:
            print("No intervals path provided. Exiting.")
            return

if __name__ == "__main__":
    main()