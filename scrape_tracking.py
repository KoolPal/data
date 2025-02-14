from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os
import argparse

def extract_content(content, pattern):
    match = re.search(pattern, content)
    return match.group(1) if match else None

def scrape_tracking_info(tracking_number, debug=False):
    driver = Driver(uc=True,
                   headless=not debug,  # Run in headed mode if debug is True
                   agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                   incognito=True)
    
    try:
        url = f"https://www.icarry.in/track-shipment?a={tracking_number}"
        if debug:
            print(f"Navigating to: {url}")
            
        driver.get(url)
        
        if debug:
            print("Waiting for page load and potential Cloudflare bypass...")
        time.sleep(5)
        
        wait = WebDriverWait(driver, 20)
        status_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//b[contains(text(),'Status:')]/following-sibling::span"))
        )
        
        if debug:
            print("Page loaded successfully!")
            
        page_content = driver.page_source
        
        # Extract information
        courier_name = extract_content(page_content, r'Courier Name\s*:</td>\s*<td>(.*?)</td>')
        status = extract_content(page_content, r'Status:\s*</b>\s*<span[^>]*>(.*?)</span>')
        estimated_delivery = extract_content(page_content, r'Estimated Delivery:\s*</b>\s*<span[^>]*>(.*?)</span>')
        destination = extract_content(page_content, r'Destination:\s*</b>\s*<span[^>]*>(.*?)</span>')
        
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
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if debug:
            print(f"Driver capabilities: {driver.capabilities}")
            print(f"Current URL: {driver.current_url}")
    
    finally:
        if debug:
            print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    tracking_number = os.getenv('TRACKING_NUMBER', '347720741487')
    scrape_tracking_info(tracking_number, debug=args.debug)
