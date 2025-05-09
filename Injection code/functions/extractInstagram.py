import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

def initialize_driver(headless=True):

    # Set up Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Initialize the driver
    print("AUEN")
    service = Service(ChromeDriverManager().install())
    

    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver = webdriver.Chrome(options=chrome_options)
    print("BBB")
    
    # Navigate to Google and handle cookie consent if needed
    driver.get("https://www.google.com")
    try:
        print("AAAAAAAAA")
        cookie_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree')]"))
        )
        cookie_button.click()
        time.sleep(1)
    except TimeoutException:
        # Cookie prompt might not appear, so we can continue
        pass
    
    return driver

def search_name_address(driver, name, address, wait_time=10):

    # Format the search query with quotes around name and address
    search_query = f'"{name}" "{address}"'
    
    try:
        # Find the search input and enter the query
        search_input = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_input.clear()
        search_input.send_keys(search_query)
        search_input.submit()
        
        # Wait for results to load
        time.sleep(3)
        
        # Find all g-link elements
        g_links = []
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "g-link"))
            )
            g_links = driver.find_elements(By.TAG_NAME, "g-link")
        except TimeoutException:
            print(f"No g-link elements found for {name}, {address}")
        
        # Extract href links from <a> tags inside <g-link> tags
        results = []
        for g_link in g_links:
            try:
                # Find all <a> tags within this g-link
                a_tags = g_link.find_elements(By.TAG_NAME, "a")
                for a_tag in a_tags:
                    href = a_tag.get_attribute("href")
                    if href:
                        # Clean the URL (remove Google redirects if present)
                        if "google.com/url?" in href:
                            # Extract the actual URL from Google's redirect
                            import urllib.parse
                            parsed_url = urllib.parse.urlparse(href)
                            url_params = urllib.parse.parse_qs(parsed_url.query)
                            if 'url' in url_params:
                                href = url_params['url'][0]
                        
                        results.append(href)
            except Exception as e:
                print(f"Error extracting link for {name}, {address}: {e}")
        
        return results
        
    except Exception as e:
        print(f"Error searching for {name}, {address}: {e}")
        return []

def close_driver(driver):
    """
    Safely close the WebDriver instance.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance to close
    """
    try:
        driver.quit()
    except Exception as e:
        print(f"Error closing driver: {e}")

# Example usage with your CSV data
if __name__ == "__main__":
    column_headers = ['businessID', 'gmapsURL', 'address', 'category', 
                     'categoryGeneral', 'name', 'phone', 'website', 'instagram', 'blank1', 'blank2', 'blank3']
    
    df = pd.read_csv('instas.csv', header=None, names=column_headers)
    
    # Initialize the driver once
    driver = initialize_driver(headless=True)
    
    try:
        # Process each row
        results = {}
        for row in df.itertuples():
            print(f"Searching for: {row.name}, {row.address}")
            found_links = search_name_address(driver, row.name, row.address)
            results[row.businessID] = found_links
            print(f"Found {len(found_links)} links")
            
            # Optional: add a delay between searches to avoid rate limiting
            time.sleep(2)
    
    finally:
        # Make sure to close the driver when done
        close_driver(driver)
    
    # Now you can process the results
    print(f"Completed searches for {len(results)} businesses")