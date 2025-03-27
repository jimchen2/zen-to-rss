from flask import Flask, Response, request
import xml.etree.ElementTree as ET
from datetime import datetime
import crawl_accounts
import crawl_one_article
import concurrent.futures

app = Flask(__name__)

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

@app.route('/')
def rss_feed():
    try:
        # Get URL from query parameter
        channel_url = request.args.get('url')
        
        if not channel_url:
            return Response("Error: Missing 'url' parameter", status=400, mimetype="text/plain")
        
        # Add ?tab=articles if not already present
        if "?tab=articles" not in channel_url:
            channel_url = channel_url + ("&" if "?" in channel_url else "?") + "tab=articles"
        
        # Get channel data and article links
        channel_data = crawl_accounts.extract_dzen_channel_data(channel_url)
        
        # Get article details in parallel
        articles_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Map returns results in the order of the input iterable
            futures = list(executor.map(fetch_article_data, channel_data["article_links"]))
            
            # Filter out None results and add to articles_data
            articles_data = [article for article in futures if article is not None]
        
        # Generate and return RSS feed
        rss_content = generate_rss(channel_data, articles_data)
        return Response(rss_content, mimetype="application/rss+xml")
    
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype="text/plain")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
