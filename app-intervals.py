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
    parts = time_str.split(':')
    try:
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h, m, s = 0, parts[0], parts[1]
        else:
            raise ValueError("Invalid time format")
        seconds = int(h) * 3600 + int(m) * 60 + int(s)
        return seconds
    except ValueError as e:
        print(f"Error converting time string '{time_str}' to seconds: {e}")
        return None



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
        print(f"Error in trimming video for interval {start_time} to {end_time} ({output_filename}): {e}")


def load_intervals_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            raw_intervals = json.load(file)
        return [(start, end, f'Chapter {i}') for i, (start, end) in enumerate(raw_intervals, start=1)]
    except Exception as e:
        print(f"Error reading intervals file: {e}")
    return None

def load_intervals_from_json(file_path):
    try:
        with open(file_path, 'r') as file:
            intervals_json = json.load(file)
        return [(item['start'], item['end'], item['title']) for item in intervals_json]
    except Exception as e:
        print(f"Error reading intervals JSON file: {e}")
        return []

def setup_output_directory(video_title, custom_output_dir=None):
    if custom_output_dir:
        output_directory = os.path.abspath(custom_output_dir)
    else:
        sanitized_title = sanitize_filename(video_title)
        output_directory = os.path.join(os.getcwd(), sanitized_title)
        counter = 1
        while os.path.exists(output_directory):
            output_directory = os.path.join(os.getcwd(), f"{sanitized_title}_{counter}")
            counter += 1

    os.makedirs(output_directory, exist_ok=True)
    return output_directory

def process_videos(source, intervals, output_dir, video_duration, use_local=False, titles=None):
    source_file = source if use_local else download_video(source, output_dir)
    if not source_file:
        print("Source video could not be retrieved.")
        return

    if not intervals:
        print("No intervals to process. Exiting.")
        return
    
    print(f"Loaded intervals: {intervals}")
    for interval in intervals:
        if len(interval) != 3:
            print(f"Invalid interval format: {interval}")
            continue
        start, end, title = interval
        sanitized_title = sanitize_filename(title)
        output_filename = f"{sanitized_title}.mp4"
        trim_video(source_file, start, end, output_filename, output_dir, video_duration)


    if not use_local:
        print(f"Removing original downloaded file: {source_file}")
        os.remove(source_file)

def main():
    parser = argparse.ArgumentParser(description='Process YouTube videos or local videos based on intervals.')
    parser.add_argument('-url', type=str, help='URL of the YouTube video', required=False)
    parser.add_argument('-api_key', type=str, help='YouTube Data API key', required=False)
    parser.add_argument('-local_video', type=str, help='Path to the local video file', required=False)
    parser.add_argument('-intervals_file', type=str, help='Path to the intervals JSON file', required=False)
    parser.add_argument('-output_dir', type=str, help='Path for the output directory', required=False, default=None)
    args = parser.parse_args()

    # Check if local video processing is requested
    if args.local_video and args.intervals_file:
        intervals = load_intervals_from_json(args.intervals_file)
        output_directory = setup_output_directory("Local_Video", custom_output_dir=args.output_dir)
        process_videos(args.local_video, intervals, output_directory, None, use_local=True)
    elif args.url and args.api_key:
        video_description, video_title, video_duration = get_video_info(args.api_key, args.url)
        if video_duration is None:
            print("Video duration not available. Exiting.")
            return

        output_directory = setup_output_directory(video_title, custom_output_dir=args.output_dir)

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