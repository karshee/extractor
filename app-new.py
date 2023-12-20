#!/usr/bin/env python3

from pytube import YouTube
from moviepy.editor import VideoFileClip
import os
import argparse
import json

def download_video(url):
    print(f"Starting to download video from {url}")
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download(filename='downloaded_video.mp4')
        print("Video downloaded successfully.")
        return 'downloaded_video.mp4'
    except Exception as e:
        print(f"Error in downloading video: {e}")
        raise

def trim_video(source_file, start_time, end_time, output_filename):
    print(f"Trimming video from {start_time} to {end_time}, saving as {output_filename}")
    try:
        with VideoFileClip(source_file) as video:
            trimmed_video = video.subclip(start_time, end_time)
            trimmed_video.write_videofile(output_filename)
        print(f"Video trimmed successfully: {output_filename}")
    except Exception as e:
        print(f"Error in trimming video: {e}")
        raise

def process_videos(source, intervals, use_local=False):
    source_file = source if use_local else download_video(source)

    for i, (start, end) in enumerate(intervals):
        output_filename = f'trimmed_video_{i}.mp4'
        trim_video(source_file, start, end, output_filename)

    if not use_local:
        print(f"Removing original downloaded file: {source_file}")
        os.remove(source_file)

def main():
    print("Script started.")
    parser = argparse.ArgumentParser(description='Download and trim YouTube videos.')
    parser.add_argument('-intervals', type=str, help='Path to the JSON file containing time intervals')
    parser.add_argument('-url', type=str, help='URL of the YouTube video')
    args = parser.parse_args()

    if args.intervals:
        try:
            with open(args.intervals, 'r') as file:
                intervals = json.load(file)
            print("Intervals loaded successfully.")
        except Exception as e:
            print(f"Error reading intervals file: {e}")
            raise
    else:
        print("Intervals file is required.")
        raise ValueError("Intervals file is required.")

    if args.url:
        process_videos(args.url, intervals)
    else:
        print("URL is required.")
        raise ValueError("URL is required.")

if __name__ == "__main__":
    main()
