import subprocess

def run_extraction(api_key, script_path, urls_file):
    with open(urls_file, 'r') as file:
        urls = file.readlines()

    if not urls:
        print("No URLs found in the file.")
        return

    for index, url in enumerate(urls, start=1):
        url = url.strip()
        if url:
            config_file = f"config-{index}.json"
            print(f"Processing {url} with {config_file}")
            try:
                subprocess.run(["python", script_path, "-url", url, "-api_key", api_key, "-intervals_path", config_file], check=True)
                print(f"Finished processing {url}")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {url}: {e}")

def main():
    API_KEY = "AIzaSyDuVhGtC3xGZtMqyBA0ZsQ1sF0ctvUDrWs"  # Your API key
    SCRIPT_PATH = "app.py"  # Your script path
    URLS_FILE = "urls.txt"  # Your URLs file

    run_extraction(API_KEY, SCRIPT_PATH, URLS_FILE)

if __name__ == "__main__":
    main()