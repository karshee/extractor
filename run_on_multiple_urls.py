import subprocess

def run_extraction(api_key, script_path, urls_file):
    with open(urls_file, 'r') as file:
        for url in file:
            url = url.strip()
            if url:
                print(f"Processing {url}")
                subprocess.run(["python", script_path, "-url", url, "-extract_segments", "-api_key", api_key])
                print(f"Finished processing {url}")

def main():
    API_KEY = "AIzaSyDuVhGtC3xGZtMqyBA0ZsQ1sF0ctvUDrWs"  # Replace with your actual API key
    SCRIPT_PATH = "app-resolution.py"  # Path to your Python script
    URLS_FILE = "urls.txt"  # File containing YouTube URLs, one per line

    run_extraction(API_KEY, SCRIPT_PATH, URLS_FILE)

if __name__ == "__main__":
    main()