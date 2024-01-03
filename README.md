# YouTube Video Segment Processor

This Python application suite includes two scripts, `app-intervals.py` and `app-chapters.py`, designed to download YouTube videos and optionally extract segments based on video chapters, descriptions, or a specified configuration. 

## Requirements

- Python 3
- Required Python libraries: `requests`, `yt_dlp`, `moviepy`
- YouTube Data API Key
- Docker (optional for containerized execution)

## Setup

1. Clone the repository or download the scripts to your local machine.
2. Install the required Python libraries:
   ```bash
   pip install requests yt_dlp moviepy
3. a YouTube Data API key. Follow these instructions to get an API key.

## Usage
The scripts can be used in different modes:

## `app-intervals.py`
This script uses a config.json file to define segments for extraction.

Custom Configuration Mode
To run `app-intervals.py` with a specific `config.json` file:

Create a `config.json` file with the desired intervals:
   ```json
   [
       ["00:00:00", "00:10:10"],
       ["00:10:11", "00:23:33"],
       ["00:23:34", "00:35:48"]
   ]
   ```

Run the script using the command:

   ```bash
   python app.py -url [youtube_video_url] -api_key [your_youtube_api_key] -intervals_path [path_to_config.json]
   ```

   Example:

   ```bash
   python app.py -url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -api_key "YOUR_API_KEY" -intervals_path "/path/to/config.json"
   ```

Download Only Mode

To only download the video without segmenting:
   ```bash
   python app.py -url [youtube_video_url] -api_key [your_youtube_api_key] -download_only
   ```


## `app-chapters.py`
This script extracts video segments based on chapters described in the video's description or using sel_chapters.py for automated chapter extraction.

Run the script using the command:

   ```bash
    python app-chapters.py -url [youtube_video_url] -api_key [your_youtube_api_key] -extract_segments
   ```

   Example:

   ```bash
    python app-chapters.py -url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -api_key "YOUR_API_KEY" -extract_segments

   ```

### Build and Run the Docker Container

1. Build the Docker image:

   ```bash
   docker build -t youtube-video-processor .
   ```


2. Run the container:

   - For app-intervals.py with Download Only Mode:
     ```bash
    docker run -v ${PWD}:/usr/src/app youtube-video-processor python ./app-intervals.py -url [youtube_video_url] -api_key [your_youtube_api_key] -download_only
     ```

   - For app-intervals.py with Custom Configuration Mode:
     ```bash
    docker run -v ${PWD}:/usr/src/app youtube-video-processor python ./app-intervals.py -url [youtube_video_url] -api_key [your_youtube_api_key] -intervals_path [path_to_config.json]
     ```
     
   - For app-chapters.py:
     ```bash
    docker run -v ${PWD}:/usr/src/app youtube-video-processor python ./app-chapters.py -url [youtube_video_url] -api_key [your_youtube_api_key] -extract_segments
     ```

Replace [youtube_video_url], [your_youtube_api_key], and [path_to_config.json] with the appropriate values.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
