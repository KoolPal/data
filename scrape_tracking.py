from seleniumbase import Driver
import cloudscraper
import time
import os
import argparse
from datetime import datetime, timezone
import json

def get_current_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def get_with_selenium(url, debug=False):
    driver = Driver(
        browser="chrome",
        uc=True,
        headless2=False,  # Keep this false as it worked in the example
        incognito=True,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36 AVG/112.0.21002.139",
        do_not_track=True,
        undetectable=True
    )

    try:
        if debug:
            print(f"[{get_current_utc()}] Selenium: Starting navigation...")
        
        driver.get(url)
        
        if debug:
            print(f"[{get_current_utc()}] Selenium: Waiting for 20 seconds...")
        time.sleep(20)
        
        content = driver.page_source
        
        if debug:
            print(f"[{get_current_utc()}] Selenium: Retrieved content successfully")
            
        return content
        
    finally:
        if debug:
            print(f"[{get_current_utc()}] Selenium: Closing driver...")
        driver.quit()

def get_with_cloudscraper(url, debug=False):
    if debug:
        print(f"[{get_current_utc()}] Cloudscraper: Creating scraper...")
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'mobile': False,
            'platform': 'windows'
        },
        delay=10
    )

    if debug:
        print(f"[{get_current_utc()}] Cloudscraper: Making request...")

    # Add headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36 AVG/112.0.21002.139',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    response = scraper.get(url, headers=headers)
    
    if debug:
        print(f"[{get_current_utc()}] Cloudscraper: Status code {response.status_code}")
        print(f"[{get_current_utc()}] Cloudscraper: Response headers: {json.dumps(dict(response.headers), indent=2)}")
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to get content. Status code: {response.status_code}")

def get_tracking_info(tracking_number, debug=False):
    url = f"https://www.icarry.in/track-shipment?a={tracking_number}"
    
    if debug:
        print(f"[{get_current_utc()}] Starting tracking lookup for {tracking_number}")
        print(f"[{get_current_utc()}] URL: {url}")
    
    # Try both methods
    selenium_error = None
    cloudscraper_error = None
    
    # Try Selenium first
    try:
        if debug:
            print(f"[{get_current_utc()}] Attempting Selenium method...")
        content = get_with_selenium(url, debug)
        if "Shipment Tracking" in content:
            if debug:
                print(f"[{get_current_utc()}] Selenium method successful")
            return {'method': 'selenium', 'content': content}
    except Exception as e:
        selenium_error = str(e)
        if debug:
            print(f"[{get_current_utc()}] Selenium method failed: {selenium_error}")
    
    # Try Cloudscraper next
    try:
        if debug:
            print(f"[{get_current_utc()}] Attempting Cloudscraper method...")
        content = get_with_cloudscraper(url, debug)
        if "Shipment Tracking" in content:
            if debug:
                print(f"[{get_current_utc()}] Cloudscraper method successful")
            return {'method': 'cloudscraper', 'content': content}
    except Exception as e:
        cloudscraper_error = str(e)
        if debug:
            print(f"[{get_current_utc()}] Cloudscraper method failed: {cloudscraper_error}")
    
    # If we get here, both methods failed
    raise Exception(
        f"Both methods failed.\n"
        f"Selenium error: {selenium_error}\n"
        f"Cloudscraper error: {cloudscraper_error}"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    print(f"Current Date and Time (UTC): {get_current_utc()}")
    print(f"Current User's Login: {os.getenv('GITHUB_ACTOR', 'KoolPal')}")
    
    tracking_number = os.getenv('TRACKING_NUMBER', '347720741487')
    
    try:
        result = get_tracking_info(tracking_number, args.debug)
        print(f"\nSuccessfully retrieved content using {result['method']} method.")
        print("\nContent preview:")
        print(result['content'][:500] + "...")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
