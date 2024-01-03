# sel_chapters.py
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys
import json

def format_timestamp(timestamp):
    parts = timestamp.split(":")
    if len(parts) == 2:
        return "00:" + timestamp
    return timestamp

def get_youtube_chapters(url):
    service = FirefoxService(executable_path='./geckodriver.exe')
    driver = webdriver.Firefox(service=service)
    driver.get(url)

    try:
        # Click 'Reject all' button for cookies
        try:
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Reject the use of cookies and other data for the purposes described']"))
            )
            reject_button.click()
        except TimeoutException:
            print("No 'Reject all' button found or not clickable.")

        # Wait for overlay to disappear
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element((By.CSS_SELECTOR, "tp-yt-iron-overlay-backdrop.opened"))
        )

        # Scroll to and expand the description section by clicking the '...more' button
        more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tp-yt-paper-button#expand"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", more_button)
        driver.execute_script("arguments[0].click();", more_button)

        # Click the "View all" button in the chapters section
        view_all_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='View all']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", view_all_button)
        driver.execute_script("arguments[0].click();", view_all_button)

        # Scroll through the chapters list to ensure all chapters are loaded
        chapters_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#contents.ytd-macro-markers-list-renderer"))
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", chapters_container)

        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", chapters_container)
            time.sleep(1)
            new_height = driver.execute_script("return arguments[0].scrollHeight", chapters_container)
            if new_height == last_height:
                break
            last_height = new_height

        # Find all chapter elements and extract title and timestamp
        chapters = driver.find_elements(By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-macro-markers-list-item-renderer")
        chapters_list = []
        for chapter in chapters:
            try:
                title_element = chapter.find_element(By.CSS_SELECTOR, "h4.macro-markers")
                timestamp_element = chapter.find_element(By.CSS_SELECTOR, "div#time")
                title = title_element.text if title_element else "No title"
                timestamp = timestamp_element.text if timestamp_element else "No timestamp"
                if title and timestamp:
                    formatted_timestamp = format_timestamp(timestamp)  # Format timestamp
                    chapters_list.append({"timestamp": formatted_timestamp, "title": title})
            except NoSuchElementException:
                continue

        driver.quit()
        with open('chapters_output.json', 'w') as file:
            json.dump(chapters_list, file)

    except TimeoutException as e:
        print(f"Timeout occurred while loading the page: {e}")
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        get_youtube_chapters(url)
    else:
        print("Error: No URL provided.")
        sys.exit(1)