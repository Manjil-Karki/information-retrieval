import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


SOURCES = [
    {'name': 'BBC Business', 'cat': 'Business', 'url': 'http://feeds.bbci.co.uk/news/business/rss.xml'},
    {'name': 'Guardian Business', 'cat': 'Business', 'url': 'https://www.theguardian.com/uk/business/rss'},
    
    {'name': 'BBC Entertainment', 'cat': 'Entertainment', 'url': 'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'},
    {'name': 'CNN Entertainment', 'cat': 'Entertainment', 'url': 'http://rss.cnn.com/rss/edition_entertainment.rss'},
    {'name': 'Sky Entertainment', 'cat': 'Entertainment', 'url': 'https://feeds.skynews.com/feeds/rss/entertainment.xml'},
    
    {'name': 'BBC Health', 'cat': 'Health', 'url': 'http://feeds.bbci.co.uk/news/health/rss.xml'},
    {'name': 'CNN Health', 'cat': 'Health', 'url': 'http://rss.cnn.com/rss/cnn_health.rss'},

]

def scrape_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
        full_text = " ".join(paragraphs)
        
        return full_text if len(full_text) > 400 else None
    except:
        return None

def collect_dataset(docs_per_cat=50):
    final_data = []
    counts = {'Business': 0, 'Entertainment': 0, 'Health': 0}
    
    print(f" Goal: Collect {docs_per_cat} documents per category (Total: {docs_per_cat * 3})")

    for source in SOURCES:
        category = source['cat']
        if counts[category] >= docs_per_cat:
            continue
            
        print(f"\n📡 Crawling {source['name']}...")
        try:
            res = requests.get(source['url'], timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            items = soup.find_all('item')
            
            for item in items:
                # Stop if category is full
                if counts[category] >= docs_per_cat:
                    break
                    
                link = item.link.text
                title = item.title.text
                
                body = scrape_content(link)
                if body:
                    final_data.append({
                        'category': category,
                        'source': source['name'],
                        'title': title,
                        'text': body
                    })
                    counts[category] += 1
                    print(f"[{counts[category]}/{docs_per_cat}] {category}: {title[:40]}...")
                    
        except Exception as e:
            print(f"Error: {e}")

    return pd.DataFrame(final_data)
    


if __name__ == "__main__":
    df = collect_dataset(docs_per_cat=100)
    df_balanced = (
        df.groupby('category')
        .apply(lambda x: x.sample(int(df["category"].value_counts().min()), random_state=42))
        .reset_index(drop=True)
    )
    df_balanced.to_csv("news_classifier/scraped_v1.csv", index=False, encoding='utf-8')