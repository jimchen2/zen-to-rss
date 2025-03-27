# example https://dzen.ru/a/Z9khBocwVgufmUKF

# Setup Selenium
# Need Russian IP, or else Blocked

# Return:
# article title, article date, article text(html)

# Title: og: title
# Date: something like this:  <meta itemprop="datePublished" content="2024-01-15">
# Find the meta tag with datePublished

# Text HTML:
# Find the tag <div ... aria-label="Статья 1" ...
# Inside the tag find <div... itemprop="articleBody" ...
# Grab it and re-process the images blocks, tags like <div ... data-block-type="image"...
# For images find the <img tag inside it and just use it
# Save the HTML as article text

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def scrape_dzen_article(url):
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        driver.get(url)
        time.sleep(3)  # Allow page to load fully
        
        # Get article title from og:title meta tag
        title_element = driver.find_element(By.XPATH, "//meta[@property='og:title']")
        title = title_element.get_attribute("content")
        
        # Get publication date from meta tag
        date_element = driver.find_element(By.XPATH, "//meta[@itemprop='datePublished']")
        date = date_element.get_attribute("content")
        
        # Find the article content
        article_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Статья 1']"))
        )
        
        # Find the article body within the article div
        article_body = article_div.find_element(By.XPATH, ".//div[@itemprop='articleBody']")
        
        # Get HTML content
        html_content = article_body.get_attribute('outerHTML')
        
        # Process the HTML to handle images correctly
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process image blocks
        image_blocks = soup.find_all('div', attrs={'data-block-type': 'image'})
        for img_block in image_blocks:
            img_tag = img_block.find('img')
            if img_tag:
                # Keep only the img tag, remove any wrappers
                img_block.clear()
                img_block.append(img_tag)
        
        # Get the processed HTML
        processed_html = str(soup)
        driver.quit()
        
        return {
            'title': title,
            'date': date,
            'content_html': processed_html
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
# Example usage
if __name__ == "__main__":
    url = "https://dzen.ru/a/Z9khBocwVgufmUKF"
    article_data = scrape_dzen_article(url)
    

    if article_data:
        print("Title:", article_data['title'])
        print("Date:", article_data['date'])
        # print("HTML:", article_data['content_html'])
        # with open('article_content.html', 'w', encoding='utf-8') as f:
        #     f.write(article_data['content_html'])
