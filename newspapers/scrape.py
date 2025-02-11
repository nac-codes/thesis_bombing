from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import json
import time
import os
import re
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("scraping.log", mode='a')])

def extract_image_urls(search_results_file):
    with open(search_results_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    image_urls = []
    for a in soup.find_all('a', href=re.compile(r'/image/\d+')):
        image_number = re.search(r'/image/(\d+)', a['href']).group(1)
        full_url = f"https://newscomwc.newspapers.com{a['href']}"
        # check if url is already in the list
        if full_url not in [url for _, url in image_urls]:
            image_urls.append((image_number, full_url))
    
    return image_urls

def scrape_with_cookies(url, output_folder, cookies_file):
    # Load the cookies from the file
    with open(cookies_file, 'r') as file:
        cookies_list = json.load(file)
    
    # Set up Firefox options
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # Run in headless mode
    
    # Set up the Firefox driver
    gecko_driver_path = "/Applications/geckodriver"
    driver = webdriver.Firefox(
        service=Service(gecko_driver_path),
        options=firefox_options
    )
    
    # Go to the website first (this is needed to set cookies)
    driver.get("https://newscomwc.newspapers.com")
    
    # Add the cookies to the driver
    for cookie in cookies_list:
        cookie_dict = {k: v for k, v in cookie.items() if k in ['name', 'value', 'domain', 'path', 'expiry', 'secure', 'httpOnly']}
        if 'sameSite' in cookie:
            cookie_dict['sameSite'] = cookie['sameSite'].capitalize()
        
        try:
            driver.add_cookie(cookie_dict)
        except Exception as e:
            logging.warning(f"Failed to add a cookie: {str(e)}")
    
    # Now navigate to the actual URL
    driver.get(url)
    
    # Wait for the page to load and for desc element to have a text length greater than 8
    time.sleep(.4)
    
    # Get the page source after JavaScript has run
    logging.info("Getting page source")
    page_source = driver.page_source

    # check if the page source contains: <div class="jumbotron container-login"> .. if it does then exit the program
    if '<div class="jumbotron container-login">' in page_source:
        logging.error("Login page detected. waiting for 60 seconds")
        time.sleep(60)
        return False
    
    # Save the page source as HTML
    with open(os.path.join(output_folder, 'page_source.html'), 'w', encoding='utf-8') as file:
        file.write(page_source)

    try:
        # find "page_name :" take the text after it in that line
        page_name = re.search(r'page_name : (.*)', page_source).group(1)

        with open(os.path.join(output_folder, 'info.txt.met'), 'w', encoding='utf-8') as f:
            f.write(page_name)
    except Exception as e:
        logging.error(f"Error getting page name: {str(e)}")

    try:
        # find <desc>  and take the text between it and the next </desc>
        content = re.search(r'<desc>(.*?)</desc>', page_source, re.DOTALL).group(1)
        # Save the extracted information
                
        with open(os.path.join(output_folder, 'content.txt'), 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Content saved in {output_folder}")
    except Exception as e:
        logging.error(f"Error getting content: {str(e)}")
    
    # Close the browser
    driver.quit()
    return True

def scrape_with_retry(url, output_folder, cookies_file, max_retries=3):
    for attempt in range(max_retries):
        if scrape_with_cookies(url, output_folder, cookies_file):
            return True
        logging.warning(f"Attempt {attempt + 1} failed for {url}. Retrying...")
        time.sleep(5)  # Wait 5 seconds before retrying
    logging.error(f"All {max_retries} attempts failed for {url}")
    return False

def main():
    output_base_folder = "newspaper_articles"
    cookies_file = "cookies_newspapers.json"

    # Extract image URLs
    image_urls = []
    for file in os.listdir('.'):
        if file.startswith('search_results') and file.endswith('.html'):
            image_urls.extend(extract_image_urls(file))
    
    logging.info(f"Found {len(image_urls)} image URLs")
    
    # Count remaining items
    remaining_urls = []
    for image_number, url in image_urls:
        output_folder = os.path.join(output_base_folder, f"IMG_{image_number}")
        if not os.path.exists(output_folder) or not os.path.exists(os.path.join(output_folder, 'content.txt')):
            remaining_urls.append((image_number, url))
    
    total_remaining = len(remaining_urls)
    logging.info(f"Remaining images to process: {total_remaining}")

    # Process remaining items with accurate progress bar
    with tqdm(total=total_remaining, desc="Processing images") as pbar:
        for image_number, url in remaining_urls:
            output_folder = os.path.join(output_base_folder, f"IMG_{image_number}")
            os.makedirs(output_folder, exist_ok=True)
            
            logging.info(f"Processing {url}")
            logging.info(f"Image number: {image_number}")
            
            if not scrape_with_retry(url, output_folder, cookies_file):
                logging.error(f"Failed to scrape {url} after multiple attempts")
            
            pbar.update(1)
            time.sleep(0.1)

if __name__ == "__main__":
    main()