import xml.etree.ElementTree as ET
from datetime import datetime
import crawl_accounts
import crawl_one_article
import concurrent.futures
import sys
import os

def fetch_article_data(article_url):
    article_data = crawl_one_article.scrape_dzen_article(article_url)
    if article_data:
        article_data["url"] = article_url  # Add URL to article data
        return article_data
    return None

def generate_rss(channel_data, articles_data):
    # Create RSS root
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    # Channel metadata
    ET.SubElement(channel, "title").text = channel_data["channel_title"]
    ET.SubElement(channel, "link").text = f"https://dzen.ru/{channel_data['channel_title']}"
    ET.SubElement(channel, "description").text = channel_data["channel_description"]
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    # Add articles as items
    for article_data in articles_data:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = article_data["title"]
        ET.SubElement(item, "link").text = article_data["url"]
        ET.SubElement(item, "description").text = article_data["content_html"]
        ET.SubElement(item, "pubDate").text = datetime.strptime(
            article_data["date"], "%Y-%m-%d"
        ).strftime("%a, %d %b %Y %H:%M:%S GMT")
        ET.SubElement(item, "guid").text = article_data["url"]
    
    # Convert to string with proper XML declaration
    return ET.tostring(rss, encoding="utf-8", method="xml", xml_declaration=True)

def create_rss_feed(channel_url, output_file="feed.xml"):
    try:
        # Add ?tab=articles if not already present
        if "?tab=articles" not in channel_url:
            channel_url = channel_url + ("&" if "?" in channel_url else "?") + "tab=articles"
        
        print(f"Fetching channel data from {channel_url}...")
        
        # Get channel data and article links
        channel_data = crawl_accounts.extract_dzen_channel_data(channel_url, article_limit=15)
        
        print(f"Found {len(channel_data['article_links'])} articles. Fetching details...")
        
        # Get article details in parallel
        articles_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for url in channel_data["article_links"]:
                print(f"Queuing article: {url}")
                futures.append(executor.submit(fetch_article_data, url))
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    articles_data.append(result)
                    print(f"Processed article: {result['title']}")
        
        print(f"Successfully fetched {len(articles_data)} articles")
        
        # Generate RSS feed
        rss_content = generate_rss(channel_data, articles_data)
        
        # Write to file
        with open(output_file, "wb") as f:
            f.write(rss_content)
        
        print(f"RSS feed was successfully generated and saved to {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        channel_url = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "feed.xml"
        create_rss_feed(channel_url, output_file)
    else:
        print("Usage: python script.py <dzen_channel_url> [output_filename]")
        print("Example: python script.py https://dzen.ru/channel_name feed.xml")
