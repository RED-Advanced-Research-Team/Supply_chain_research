import requests
import json
import asyncio
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import time
import logging
import sys
import warnings

# Setup logging
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Disable warnings (consider the security implications of this in a real-world application)
warnings.filterwarnings("ignore")

# Proxy configuration
proxies = {
    'http': 'socks5h://127.0.0.1:9150',
    'https': 'socks5h://127.0.0.1:9150'
}

# Regular expression for URL extraction
url_pattern = re.compile(r"(?:https?:\/\/|ftps?:\/\/|www\.)(?:(?![.,?!;:()]*(?:\s|$))[^\s]){2,}")

def fetch_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def write_urls_to_file(file_path, urls):
    with open(file_path, 'a') as file:
        for url in urls:
            file.write(url + "\n")

def extract_urls_from_text(text):
    return [url for url in url_pattern.findall(text) if not "svg" in url]

def make_request(url, headers=None, retry_on_429=True):
    try:
        response = requests.get(url, verify=False, headers=headers or {}, proxies=proxies)
        if response.status_code == 429 and retry_on_429:
            time.sleep(13)
            return make_request(url, headers, False)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.error(f"Error making request to {url}: {e}")
        return None

def parse_github_directory(url):
    response = make_request(url)
    if not response:
        return []

    try:
        res_dict = response.json()
        urls = []

        for item in res_dict['payload']['tree']['items']:
            name = item['name']
            if item['contentType'] == 'directory':
                urls.extend(parse_github_directory(url + "/" + name))
            else:
                file_url = (f"https://raw.githubusercontent.com/{res_dict['payload']['repo']['ownerLogin']}/"
                            f"{res_dict['payload']['repo']['name']}/{res_dict['payload']['repo']['defaultBranch']}"
                            f"/{item['path']}")
                file_response = make_request(file_url)
                if file_response:
                    urls.extend(extract_urls_from_text(file_response.text))
        return urls
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {url}: {e}")
        return []

def parse_github_repository(url):
    if "github" not in url:
        return []
    
    response = make_request(url)
    if not response:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        centered_elements = soup.find(class_='Box mb-3').find_all(class_='js-navigation-open Link--primary')
        urls = []

        for element in centered_elements:
            href = element['href']
            if "blob" in href:
                file_url = f"https://github.com/{href}?raw=true"
                file_response = make_request(file_url)
                if file_response:
                    urls.extend(extract_urls_from_text(file_response.text))
            else:
                urls.extend(parse_github_directory(f"https://github.com/{href}"))

        return urls
    except AttributeError:
        return []

async def start_parsing(list_urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        futures = [loop.run_in_executor(executor, parse_github_repository, url) for url in list_urls]
        for future in asyncio.as_completed(futures):
            urls = await future
            write_urls_to_file("return_git.txt", urls)

if __name__ == "__main__":
    list_urls = fetch_urls_from_file("MY_rep.txt")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_parsing(list_urls))

