
# YouTube Video Segment Processor

This Python application, `app.py`, is designed to download YouTube videos, optionally extract segments based on video chapters or a specified configuration, and process these segments into separate video files.

## Requirements

- Python 3
- Required Python libraries: `requests`, `yt_dlp`, `moviepy`
- YouTube Data API Key

## Setup

1. Clone the repository or download `app.py` to your local machine.
2. Install the required Python libraries:
   ```
   pip install requests yt_dlp moviepy
   ```
3. Obtain a YouTube Data API key. [Follow these instructions](https://developers.google.com/youtube/registering_an_application) to get an API key.

## Usage

The script can be used in two modes:

1. **Extract Segments Mode**: Extracts video segments based on the chapters described in the video's description.
2. **Custom Configuration Mode**: Uses a `config.json` file to define the segments to be extracted.

### Extract Segments Mode

To run the script in extract segments mode, use the following command:

```bash
python app.py -url [youtube_video_url] -api_key [your_youtube_api_key] -extract_segments
```

Example:

```bash
python app.py -url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -api_key "YOUR_API_KEY" -extract_segments
```

### Custom Configuration Mode

To run the script with a specific `config.json` file:

1. Create a `config.json` file with the following format:

   ```json
   [
       ["00:00:00", "00:10:10"],
       ["00:10:11", "00:23:33"],
       ["00:23:34", "00:35:48"]
   ]
   ```

2. Run the script using the command:

   ```bash
   python app.py -url [youtube_video_url] -api_key [your_youtube_api_key] -intervals_path [path_to_config.json]
   ```

   Example:

   ```bash
   python app.py -url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -api_key "YOUR_API_KEY" -intervals_path "/path/to/config.json"
   ```

## Running in a Docker Container

To run this application in a Docker container, follow these steps:

### Dockerfile

Create a file named `Dockerfile` in the same directory as `app.py` with the following content:

```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir requests yt_dlp moviepy

# Run app.py when the container launches
CMD ["python", "./app.py"]
```

### Build and Run the Docker Container

1. Build the Docker image:

   ```bash
   docker build -t youtube-video-processor .
   ```

2. Run the container:

   - For Extract Segments Mode:

     ```bash
     docker run -e YOUTUBE_URL=[youtube_video_url] -e API_KEY=[your_youtube_api_key] -e MODE=extract_segments youtube-video-processor
     ```

   - For Custom Configuration Mode:

     First, you need to ensure that the `config.json` file is available inside the container. This can be done by mounting the directory containing `config.json` into the container.

     ```bash
     docker run -v /path/to/config_folder:/usr/src/app/config -e YOUTUBE_URL=[youtube_video_url] -e API_KEY=[your_youtube_api_key] -e CONFIG_PATH=config/config.json youtube-video-processor
     ```

Replace `[youtube_video_url]`, `[your_youtube_api_key]`, and `/path/to/config_folder` with the appropriate values. Note that in the Docker environment, the script will be looking for environment variables for configuration.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
