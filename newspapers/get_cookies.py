import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
RESOLVER_URL = "https://resolver.library.columbia.edu/clio16968631"
NEWSPAPERS_URL = "https://newscomwc.newspapers.com"
COOKIES_NEWSPAPERS_FILE = "cookies_newspapers.json"
GECKO_DRIVER_PATH = "/Applications/geckodriver"  # Update this path as needed

def setup_driver(headless=False, debug=False):
    options = Options()
    if headless and not debug:
        options.add_argument("--headless")
    return webdriver.Firefox(service=Service(GECKO_DRIVER_PATH), options=options)

def save_cookies(driver, file_name):
    cookies = driver.get_cookies()
    with open(file_name, 'w') as f:
        json.dump(cookies, f)
    logging.info(f"Saved {len(cookies)} cookies to {file_name}")

def attempt_login(driver, debug=False):
    username = os.environ.get('CLIO_USER')
    password = os.environ.get('CLIO_PASS')
    
    if not username or not password:
        logging.error("CLIO_USER or CLIO_PASS environment variables not set")
        return False
    
    try:
        logging.info("Attempting login")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn-submit[name='submit'][value='LOGIN']"))
        )

        if debug:
            input("Please confirm the login fields are filled in and press Enter...")

        login_button.click()

        # wait a few seconds for the page to load then save the page source for debugging
        if debug:
            time.sleep(5)
            with open("page_source_login.html", "w") as f:
                f.write(driver.page_source)

        logging.info("Waiting for Duo iframe")
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "duo_iframe"))
        )

        if debug:
            time.sleep(5)
            with open("page_source_duo.html", "w") as f:
                f.write(driver.page_source)

        # Wait for Duo Push button to appear
        logging.info("Waiting for Duo Push button")
        duo_push_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Send Me a Push')]"))
        )
        
        if duo_push_button:
            logging.info("Clicking Duo Push button")
            duo_push_button.click()
        else:
            logging.error("Duo Push button not found")
            return False

        # Wait for authentication to complete
        logging.info("Waiting for Duo Push authentication to complete...")
        try:
            WebDriverWait(driver, 24*60*60).until(  # 1-day timeout
                EC.url_changes(driver.current_url)
            )
            logging.info("Duo Push authentication completed successfully")
        except TimeoutException:
            logging.error("Duo Push authentication timed out after 5 minutes")
            return False

        if debug:
            input("Please confirm the login and Duo Push authentication are complete and press Enter...")
        
        return True
    except Exception as e:
        logging.error(f"Login attempt failed: {str(e)}")
        return False

def update_cookies(debug=False):
    driver = setup_driver(headless=not debug, debug=debug)
    
    try:
        # Navigate to resolver URL
        logging.info("Navigating to resolver URL")
        driver.get(RESOLVER_URL)

        # Check if redirected to login page
        if "cas.columbia.edu/cas/login" in driver.current_url:
            logging.info("Redirected to login page, attempting login")
            if not attempt_login(driver, debug):
                logging.warning("Login failed, proceeding anyway")

        # Wait for newspapers.com URL
        logging.info("Waiting for newspapers.com URL")
        WebDriverWait(driver, 60).until(EC.url_contains("newspapers.com"))

        # Save newspapers.com cookies
        save_cookies(driver, COOKIES_NEWSPAPERS_FILE)

    finally:
        if debug:
            input("Press Enter to close the browser...")
        driver.quit()

def main():
    update_interval = 25*60  # 25 minutes
    debug = False
    
    while True:
        update_cookies(debug)
        if not debug:
            logging.info(f"Sleeping for {update_interval} seconds")
            time.sleep(update_interval)
        else:
            input("Press Enter to continue...")
            time.sleep(1)

if __name__ == "__main__":
    main()