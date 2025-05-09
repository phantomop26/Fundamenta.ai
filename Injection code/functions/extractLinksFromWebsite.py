
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import json

def extractLinksFromWebsite(url):
    """
    Extract external links from a webpage using requests and BeautifulSoup.
    This approach doesn't require a browser instance.
    """
    # Set a user agent to avoid being blocked
    
    
    try:
        # Get the page content
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the domain of the target page
        target_domain = urlparse(url).netloc
        
        # Initialize a set to store unique external links
        external_links = set()
        
        # 1. Extract from regular <a> tags
        for a_tag in soup.find_all('a', href=True):

            href = a_tag['href']
            # print(href)
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(url, href)
            
            # Check if it's an external link
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc and parsed_url.netloc != target_domain and parsed_url.scheme in ('http', 'https'):
                external_links.add(absolute_url)
        print("BEOFREEEE", external_links)
        
        # 2. Extract from onclick attributes (JavaScript-based links)
        for element in soup.find_all(attrs={'onclick': True}):
            onclick = element['onclick']
            # Look for common JavaScript navigation patterns
            url_matches = re.findall(r"window\.open\(['\"](https?://[^'\"]+)['\"]", onclick)
            url_matches += re.findall(r"location\.href\s*=\s*['\"](https?://[^'\"]+)['\"]", onclick)
            
            for match in url_matches:
                parsed_url = urlparse(match)
                if parsed_url.netloc and parsed_url.netloc != target_domain:
                    print("HERE")
                    external_links.add(match)
        
        # 3. Extract from data attributes
        for data_attr in ['data-href', 'data-url', 'data-link']:
            for element in soup.find_all(attrs={data_attr: True}):
                data_url = element[data_attr]
                absolute_url = urljoin(url, data_url)
                
                parsed_url = urlparse(absolute_url)
                if parsed_url.netloc and parsed_url.netloc != target_domain and parsed_url.scheme in ('http', 'https'):
                    print("HERE2")

                    external_links.add(absolute_url)
        
        # 4. Extract from meta redirects
        for meta in soup.find_all('meta', attrs={'http-equiv': 'refresh'}):
            if 'content' in meta.attrs:
                match = re.search(r'url=(https?://[^\'"\s>]+)', meta['content'], re.IGNORECASE)
                if match:
                    redirect_url = match.group(1)
                    parsed_url = urlparse(redirect_url)
                    if parsed_url.netloc and parsed_url.netloc != target_domain:
                        print("HERE3")

                        external_links.add(redirect_url)
        
        # 5. Extract from inline JavaScript
        scripts = soup.find_all('script')
        js_content = ' '.join([script.string for script in scripts if script.string])
        
        # Look for URLs in JavaScript
        js_urls = re.findall(r'https?://[^\s\'"()<>]+', js_content)
        for js_url in js_urls:
            parsed_url = urlparse(js_url)
            if parsed_url.netloc and parsed_url.netloc != target_domain:
                # Clean up the URL (remove trailing punctuation)
                clean_url = re.sub(r'[.,;:\'"<>)\]}]+$', '', js_url)
                print("HERE4", clean_url)
                external_links.add(clean_url)
        
        pattern = re.compile(r"https?://(?:www\.)?instagram\.com/[^/]+/?")

        return [x for x in external_links if pattern.match(x)]  
        # return external_links  
    except Exception as e:
        print(f"Error extracting links: {str(e)}")
        return []


# target_url = 'https://gassaga.com'  # Replace with your target URL
# target_url = 'https://prestaprenda.com/'
# target_url = 'https://dazujo.com/'
target_url = 'https://www.loscompadres.mx/contacto.html'
external_links = extractLinksFromWebsite(target_url)
print('-'*50)
print(external_links)

# Optionally save to JSON file
# with open('external_links.json', 'w') as f:
#     json.dump({"url": target_url, "external_links": external_links}, f, indent=2)

#!/usr/bin/env python3

# #!/usr/bin/env python3
# import time
# import json
# import re
# import os
# import sys
# import traceback
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
# from urllib.parse import urlparse

# def extract_facebook_external_links(page_url, use_headless=True, debug_mode=True):
#     """
#     Advanced method to extract external links from a Facebook page using
#     full browser rendering with additional anti-detection measures.
    
#     Parameters:
#     - page_url: Facebook page URL or username
#     - use_headless: Whether to use headless mode (may help with some driver issues)
#     - debug_mode: Whether to print additional debugging information
#     """
#     # Process the URL to ensure it's in the correct format
#     if 'facebook.com' not in page_url:
#         if '/' in page_url:
#             page_url = page_url.split('/')[-1]
#         page_url = f'https://www.facebook.com/{page_url}'
    
#     print(f"Starting extraction from: {page_url}")
    
#     # Configure Chrome with stealth settings
#     options = Options()
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')
    
#     if use_headless:
#         print("Using headless mode")
#         options.add_argument('--headless=new')  # Use the newer headless mode
#     else:
#         # If not headless, use a small window
#         options.add_argument('--window-size=1366,768')
    
#     # Set a realistic user agent
#     options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
#     # Disable automation flags that Facebook can detect
#     options.add_argument('--disable-blink-features=AutomationControlled')
#     options.add_experimental_option('excludeSwitches', ['enable-automation'])
#     options.add_experimental_option('useAutomationExtension', False)
    
#     # For debugging - log all console output
#     if debug_mode:
#         options.add_experimental_option('excludeSwitches', ['enable-logging'])
#         options.add_argument('--verbose')
#         options.add_argument('--log-level=0')
    
#     # Initialize WebDriver
#     print("Initializing browser...")
#     driver = None
    
#     try:
#         # Try different methods to initialize the driver
#         try:
#             # Method 1: Direct initialization
#             driver = webdriver.Chrome(options=options)
#             print("Successfully initialized Chrome using default method")
#         except WebDriverException as e:
#             print(f"Default initialization failed: {e}")
            
#             try:
#                 # Method 2: Try with explicit service but no path
#                 service = Service()
#                 driver = webdriver.Chrome(service=service, options=options)
#                 print("Successfully initialized Chrome with Service object")
#             except WebDriverException as e:
#                 print(f"Service initialization failed: {e}")
                
#                 # Method 3: Try to find ChromeDriver in the current directory
#                 chrome_driver_path = None
#                 for file in os.listdir('.'):
#                     if 'chromedriver' in file.lower():
#                         chrome_driver_path = os.path.abspath(file)
#                         break
                
#                 if chrome_driver_path:
#                     print(f"Found ChromeDriver at: {chrome_driver_path}")
#                     service = Service(executable_path=chrome_driver_path)
#                     driver = webdriver.Chrome(service=service, options=options)
#                     print("Successfully initialized Chrome with local ChromeDriver")
#                 else:
#                     raise Exception("Could not find ChromeDriver in the current directory")
        
#         if not driver:
#             raise Exception("Failed to initialize Chrome driver")
        
#         # Set the script to hide automation
#         driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
#         external_links = set()
        
#         # First, load the main page - with verbose logging
#         print("Loading page...")
#         if debug_mode:
#             print(f"Current URL before navigation: {driver.current_url}")
        
#         driver.get(page_url)
        
#         if debug_mode:
#             print(f"URL after navigation: {driver.current_url}")
#             print(f"Page title: {driver.title}")
        
#         # Wait for the page to load
#         time.sleep(7)
        
#         if debug_mode:
#             print(f"URL after waiting: {driver.current_url}")
#             print(f"Page title after waiting: {driver.title}")
#             print(f"Page source length: {len(driver.page_source)}")
        
#         # Check if we need to dismiss any dialogs
#         try:
#             cookie_buttons = driver.find_elements(By.XPATH, 
#                 "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Cookie')]")
#             if cookie_buttons:
#                 cookie_buttons[0].click()
#                 time.sleep(2)
#         except Exception as e:
#             print(f"Note: Couldn't handle cookie dialog: {e}")
                
#         # Get page source after JS has executed
#         page_source = driver.page_source
        
#         # Debugging: Check if we landed on a login page
#         if "log in" in page_source.lower() or "sign up" in page_source.lower():
#             print("WARNING: It appears we've landed on a login page. Facebook may be blocking the scraping attempt.")
        
#         # Scan the main page content for links
#         print("Scanning main page for external links...")
#         scan_and_extract_links(driver, page_source, external_links, page_url)
        
#         # Now try to navigate to the About page which often has the website link
#         try:
#             print("Attempting to visit About page...")
#             # Different possible XPATHs for the About link
#             about_link_xpaths = [
#                 "//a[contains(@href, '/about')]",
#                 "//span[text()='About']/ancestor::a",
#                 "//a[contains(text(), 'About')]",
#                 "//a[contains(@aria-label, 'About')]"
#             ]
            
#             for xpath in about_link_xpaths:
#                 try:
#                     about_links = driver.find_elements(By.XPATH, xpath)
#                     if about_links:
#                         about_links[0].click()
#                         print("Clicked About page link")
#                         time.sleep(5)
#                         about_page_source = driver.page_source
#                         scan_and_extract_links(driver, about_page_source, external_links, page_url)
#                         break
#                 except Exception as e:
#                     continue
#         except Exception as e:
#             print(f"Could not access About page: {e}")
        
#         # Save the results
#         results = {
#             "facebook_page": page_url,
#             "external_links": list(external_links),
#             "count": len(external_links)
#         }
        
#         # Generate filename from the URL
#         page_name = urlparse(page_url).path.strip('/').replace('/', '_')
#         if not page_name:
#             page_name = "facebook_page"
            
#         filename = f"{page_name}_links.json"
#         with open(filename, 'w') as f:
#             json.dump(results, f, indent=2)
            
#         print(f"\nFound {len(external_links)} external links")
#         print(f"Results saved to {filename}")
        
#         return list(external_links)
    
#     except Exception as e:
#         print("\n===== ERROR DETAILS =====")
#         print(f"Error during extraction: {e}")
#         traceback.print_exc()
#         print("=========================\n")
#         return []
    
#     finally:
#         # Clean up
#         try:
#             if driver:
#                 if debug_mode:
#                     print(f"Final URL before quitting: {driver.current_url}")
#                 driver.quit()
#         except:
#             pass

# def scan_and_extract_links(driver, page_source, external_links, base_url):
#     """Extract external links from page source and add them to the set"""
#     base_domain = urlparse(base_url).netloc
    
#     # 1. Extract all regular <a> links from the page
#     try:
#         links = driver.find_elements(By.TAG_NAME, 'a')
#         print(f"Found {len(links)} <a> tags on the page")
        
#         for link in links:
#             try:
#                 href = link.get_attribute('href')
#                 if href and href.startswith('http') and base_domain not in href and 'facebook.com' not in href:
#                     external_links.add(href)
#             except:
#                 continue
#     except Exception as e:
#         print(f"Error extracting <a> tags: {e}")
    
#     # 2. Use regex to find links in the page source
#     # Look for website URLs in the Facebook page source
#     patterns = [
#         r'"website":"(https?://[^"]+)"',                      # Website in JSON data
#         r'"externalUrl":"(https?://[^"]+)"',                  # External URL in JSON data
#         r'href="(https?://(?!(?:www\.)?facebook\.com)[^"]+)"', # Regular href links
#         r'target="_blank" href="(https?://[^"]+)"',            # External links with target _blank
#     ]
    
#     for pattern in patterns:
#         matches = re.findall(pattern, page_source)
#         if matches:
#             print(f"Found {len(matches)} matches with pattern: {pattern}")
#         for match in matches:
#             if 'facebook.com' not in match and 'fbcdn.net' not in match:
#                 external_links.add(match)
    
#     # 3. Check specific Facebook elements that might contain URLs
#     # About section often contains business details
#     business_info_sections = [
#         "//div[contains(text(), 'Website')]/following-sibling::*//a",
#         "//div[contains(text(), 'Contact')]/following-sibling::*//a",
#         "//span[contains(text(), 'Website')]/following-sibling::*//a",
#         "//div[contains(@aria-label, 'Website') or contains(@aria-label, 'Contact')]//a"
#     ]
    
#     for section in business_info_sections:
#         try:
#             elements = driver.find_elements(By.XPATH, section)
#             if elements:
#                 print(f"Found {len(elements)} elements with XPath: {section}")
#             for element in elements:
#                 href = element.get_attribute('href')
#                 if href and href.startswith('http') and base_domain not in href and 'facebook.com' not in href:
#                     external_links.add(href)
#         except:
#             continue

# def main():
#     print("Facebook External Link Extractor")
#     print("================================")
    
#     # Check if chromedriver is in the path
#     print("Environment check:")
#     if os.environ.get("PATH"):
#         path_dirs = os.environ["PATH"].split(os.pathsep)
#         chrome_driver_found = False
#         for dir in path_dirs:
#             if os.path.exists(dir):
#                 for file in os.listdir(dir):
#                     if "chromedriver" in file.lower():
#                         print(f"- ChromeDriver found in PATH: {os.path.join(dir, file)}")
#                         chrome_driver_found = True
#         if not chrome_driver_found:
#             print("- No ChromeDriver found in PATH")
#     else:
#         print("- PATH environment variable not accessible")
    
#     # Check if Chrome is installed
#     chrome_paths = [
#         # Windows
#         "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
#         "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
#         # Mac
#         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
#         # Linux
#         "/usr/bin/google-chrome",
#         "/usr/bin/google-chrome-stable"
#     ]
    
#     chrome_found = False
#     for path in chrome_paths:
#         if os.path.exists(path):
#             print(f"- Chrome browser found at: {path}")
#             chrome_found = True
#             break
    
#     if not chrome_found:
#         print("- Chrome browser not found in common locations")
    
#     print("\nRunning in headless mode by default")
#     print("This may help with some WebDriver initialization issues")
    
#     # Get the Facebook page URL from user input
#     page_url = input("Enter Facebook page username or URL (or leave empty for default): ").strip()
#     if not page_url:
#         page_url = "cellfixsaltillo"  # Default for testing
#         print(f"Using default: {page_url}")
    
#     # Run the extraction
#     links = extract_facebook_external_links(page_url, use_headless=True, debug_mode=True)
    
#     # Display the results
#     if links:
#         print("\nExternal links found:")
#         for link in links:
#             print(f"  - {link}")
#     else:
#         print("\nNo external links found or an error occurred. This could be because:")
#         print("  1. The Facebook page doesn't have any external links")
#         print("  2. Facebook's anti-scraping mechanisms blocked the extraction")
#         print("  3. There's an issue with WebDriver initialization")
#         print("  4. The page requires logging in to view content")
#         print("\nTroubleshooting:")
#         print("  1. Make sure Chrome is installed")
#         print("  2. Download the correct ChromeDriver version for your Chrome:")
#         print("     https://chromedriver.chromium.org/downloads")
#         print("  3. Place the ChromeDriver in the same directory as this script")
#         print("  4. Try running without headless mode by editing the script")
#         print("  5. Consider using selenium-wire or playwright as alternatives to Selenium")

# if __name__ == "__main__":
#     main()