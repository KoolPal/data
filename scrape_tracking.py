from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import time
import re
import os
import argparse

def extract_content(content, pattern):
    match = re.search(pattern, content)
    return match.group(1) if match else None

def create_driver(debug=False):
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    if not debug:
        options.add_argument('--headless')
    
    # Add additional headers to better mimic a real browser
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-blink-features')
    
    # Set custom user agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    return Driver(uc=True, 
                 options=options,
                 incognito=True,
                 headless=not debug,
                 servername='127.0.0.1',
                 port=9222)

def wait_for_cloudflare(driver, debug=False):
    try:
        if debug:
            print("Checking for Cloudflare challenge...")
        
        # Wait for potential Cloudflare challenge to pass
        for _ in range(30):  # 30 seconds max wait
            if "challenge-platform" in driver.page_source or "cf-" in driver.page_source:
                if debug:
                    print("Cloudflare detected, waiting...")
                time.sleep(1)
            else:
                if debug:
                    print("No Cloudflare challenge detected or challenge passed")
                break
            
        # Additional wait for page stabilization
        time.sleep(3)
        
    except Exception as e:
        if debug:
            print(f"Error during Cloudflare wait: {str(e)}")
        raise

def scrape_tracking_info(tracking_number, debug=False):
    driver = None
    max_retries = 3
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            if debug:
                print(f"Attempt {current_retry + 1} of {max_retries}")
            
            driver = create_driver(debug)
            
            url = f"https://www.icarry.in/track-shipment?a={tracking_number}"
            if debug:
                print(f"Navigating to: {url}")
            
            driver.get(url)
            wait_for_cloudflare(driver, debug)
            
            if debug:
                print("Waiting for status element...")
            
            wait = WebDriverWait(driver, 20)
            status_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//b[contains(text(),'Status:')]/following-sibling::span"))
            )
            
            if debug:
                print("Status element found!")
            
            page_content = driver.page_source
            
            # Basic validation of page content
            if "Shipment Tracking" not in page_content:
                raise Exception("Invalid page content - missing expected elements")
            
            # Extract information
            courier_name = extract_content(page_content, r'Courier Name\s*:</td>\s*<td>(.*?)</td>')
            status = extract_content(page_content, r'Status:\s*</b>\s*<span[^>]*>(.*?)</span>')
            estimated_delivery = extract_content(page_content, r'Estimated Delivery:\s*</b>\s*<span[^>]*>(.*?)</span>')
            destination = extract_content(page_content, r'Destination:\s*</b>\s*<span[^>]*>(.*?)</span>')
            
            if not any([courier_name, status, estimated_delivery, destination]):
                raise Exception("Failed to extract tracking information")
            
            print("\n=== Tracking Results ===")
            print(f"Tracking Number: {tracking_number}")
            print(f"Courier: {courier_name}")
            print(f"Status: {status}")
            print(f"Estimated Delivery: {estimated_delivery}")
            print(f"Destination: {destination}")
            
            tracking_rows = driver.find_elements(By.XPATH, "//table[.//b[contains(text(),'Date')]]/tbody/tr")
            
            print("\n=== Tracking Timeline ===")
            for row in tracking_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    print(f"{cells[0].text} | {cells[1].text} | {cells[2].text}")
            
            break  # Success - exit retry loop
            
        except Exception as e:
            current_retry += 1
            if debug:
                print(f"Error occurred: {str(e)}")
                if driver:
                    print(f"Driver capabilities: {driver.capabilities}")
                    print(f"Current URL: {driver.current_url}")
                    print(f"Page source preview: {driver.page_source[:500]}...")
            
            if current_retry < max_retries:
                print(f"Retrying... ({current_retry + 1}/{max_retries})")
                time.sleep(5)  # Wait before retry
            else:
                print("Maximum retries reached. Failed to scrape tracking information.")
                raise
        
        finally:
            if driver:
                if debug:
                    print("Closing browser...")
                try:
                    driver.quit()
                except:
                    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    tracking_number = os.getenv('TRACKING_NUMBER', '347720741487')
    scrape_tracking_info(tracking_number, debug=args.debug)
