# example https://dzen.ru/tourister?tab=articles

# Setup Selenium

# Extract Cookie from Chrome
# Use Chrome Cookie

# Return:
# channel title, channel image url, channel description, links to the all the articles(array)

# Grab og: title, og: image, og: description

# Look for divs with id="zen-row-xxx", like id="zen-row-17", "id="zen-row-22"
# Scroll down
# Until there are no longer more divs like this for 20 seconds

# For each divs fetch the href inside (there might be 2 but they are the same)
# URL like this: https://dzen.ru/a/Z5Cu0mfrv2sfBDOi?feed_exp...
# Clean the URL: https://dzen.ru/a/Z5Cu0mfrv2sfBDOi is enough

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def extract_dzen_channel_data(url):
    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # First navigate to the page
        driver.get(url)
        time.sleep(2)  # Wait for the page to fully load
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Extract channel information using meta tags
        channel_title = driver.find_element(By.XPATH, "//meta[@property='og:title']").get_attribute("content")
        channel_image = driver.find_element(By.XPATH, "//meta[@property='og:image']").get_attribute("content")
        
        try:
            channel_description = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute("content")
        except:
            channel_description = ""
            
        # List to store all article links
        article_links = []
        
        # Set to keep track of unique article IDs
        unique_article_ids = set()
        
        # Function to extract article links
        def extract_articles():
            # Find all zen-row-xxx divs
            zen_rows = driver.find_elements(By.CSS_SELECTOR, 'div[id^="zen-row-"]')
            
            new_links_found = 0
            
            for row in zen_rows:
                row_id = row.get_attribute('id')
                if row_id not in unique_article_ids:
                    unique_article_ids.add(row_id)
                    
                    # Find article links within the row
                    links = row.find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        href = link.get_attribute('href')
                        if href and 'dzen.ru/a/' in href:
                            # Clean the URL
                            clean_url = re.sub(r'(https://dzen\.ru/a/[^/?]+).*', r'\1', href)
                            if clean_url not in article_links:
                                article_links.append(clean_url)
                                new_links_found += 1
            
            return new_links_found
            
        # Scroll and extract articles
        no_new_links_counter = 0
        max_attempts = 10  # Maximum attempts without finding new links
        
        while no_new_links_counter < max_attempts:
            # Get current scroll position
            previous_height = driver.execute_script("return document.body.scrollHeight")
            
            # Extract articles in the current viewport
            new_links = extract_articles()
            
            if new_links == 0:
                no_new_links_counter += 1
            else:
                no_new_links_counter = 0
            
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for page to load new content
            try:
                time.sleep(2)  # Short wait for content to load
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return document.body.scrollHeight") > previous_height
                )
            except TimeoutException:
                # If scroll height doesn't change, we may have reached the end
                no_new_links_counter += 1
                
        return {
            "channel_title": channel_title,
            "channel_image_url": channel_image,
            "channel_description": channel_description,
            "article_links": article_links
        }
        
    finally:
        driver.quit()

# Example usage
if __name__ == "__main__":
    channel_url = "https://dzen.ru/tourister?tab=articles"
    result = extract_dzen_channel_data(channel_url)
    
    print(f"Channel Title: {result['channel_title']}")
    print(f"Channel Image URL: {result['channel_image_url']}")
    print(f"Channel Description: {result['channel_description']}")
    print(f"Total Articles Found: {len(result['article_links'])}")
    print("\nFirst 5 Article Links:")
    for link in result['article_links'][:5]:
        print(link)
