#!/usr/bin/env python3
"""
Collect WeChat articles from a URL list file.

Reads article URLs from a text file (one per line, # for comments),
fetches content from each WeChat article page, and outputs normalized JSON.

WeChat article pages (mp.weixin.qq.com/s/...) are publicly accessible.
Uses a Chinese mobile browser User-Agent to avoid bot detection.

Input:  wechat_urls.txt (or any file via --urls)
Output: .tmp/raw_wechat.json
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install requests beautifulsoup4")
    sys.exit(1)

# Add parent directory to path for shared utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.utils import clean_text

# WeChat mobile browser User-Agent to avoid bot detection
WECHAT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.50"
)


def load_urls(urls_file: str) -> list:
    """
    Read URLs from a text file. Skips blank lines and lines starting with #.

    Args:
        urls_file: Path to text file with one URL per line

    Returns:
        List of URL strings (deduplicated, preserving order)
    """
    if not os.path.exists(urls_file):
        print(f"ERROR: URL file not found: {urls_file}")
        print("Create a file with one WeChat article URL per line.")
        print("Lines starting with # are treated as comments.")
        sys.exit(1)

    seen = set()
    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith('#'):
                continue
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def fetch_wechat_article(url: str, timeout: int = 15) -> dict:
    """
    Fetch a WeChat article page and extract title, date, and content.

    WeChat article HTML structure:
      - Title:   <h1 class="rich_media_title"> or <h2 id="activity-name">
      - Date:    <em id="publish_time"> or <span id="publish_time">
      - Content: <div id="js_content"> or <div class="rich_media_content">

    Args:
        url: WeChat article URL (mp.weixin.qq.com/s/...)
        timeout: Request timeout in seconds

    Returns:
        Dict with keys: title, description, url, published_at, content, source
        Returns partial dict on failure (always includes url and source).
    """
    headers = {
        'User-Agent': WECHAT_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.5',
        'Referer': 'https://mp.weixin.qq.com/',
    }

    article = {
        'source': 'WeChat',
        'title': '',
        'description': '',
        'url': url,
        'published_at': '',
        'content': '',
        'raw': {}
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extract title ---
        title_elem = (
            soup.find('h1', class_='rich_media_title') or
            soup.find('h2', id='activity-name') or
            soup.find('h1') or
            soup.find('title')
        )
        if title_elem:
            article['title'] = clean_text(title_elem.get_text())

        # --- Extract publish date ---
        date_elem = (
            soup.find('em', id='publish_time') or
            soup.find('span', id='publish_time') or
            soup.find('em', class_='publish_time')
        )
        if date_elem:
            date_text = clean_text(date_elem.get_text())
            # WeChat dates are like "2026年03月10日" or "2026-03-10"
            article['published_at'] = parse_wechat_date(date_text)

        # --- Extract content ---
        content_elem = (
            soup.find('div', id='js_content') or
            soup.find('div', class_='rich_media_content') or
            soup.find('div', id='page-content') or
            soup.find('article')
        )

        if content_elem:
            # Remove embedded scripts, images alt text noise
            for tag in content_elem.find_all(['script', 'style', 'img']):
                tag.decompose()
            content_text = content_elem.get_text(separator='\n')
        else:
            # Fallback: full body text
            body = soup.body
            if body:
                for tag in body.find_all(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                content_text = body.get_text(separator='\n')
            else:
                content_text = soup.get_text(separator='\n')

        # Clean up whitespace
        lines = [line.strip() for line in content_text.splitlines()]
        content_text = '\n'.join(line for line in lines if line)
        article['content'] = content_text[:8000]  # Limit to avoid token overflow

        # Use first 200 chars of content as description
        article['description'] = content_text[:200].replace('\n', ' ')

    except requests.exceptions.Timeout:
        print(f"  WARNING: Timeout fetching {url}")
    except requests.exceptions.HTTPError as e:
        print(f"  WARNING: HTTP {e.response.status_code} for {url}")
    except Exception as e:
        print(f"  WARNING: Failed to fetch {url}: {e}")

    return article


def parse_wechat_date(date_text: str) -> str:
    """
    Parse WeChat date strings into ISO 8601 format.

    Handles formats like:
      "2026年03月10日"  →  "2026-03-10T00:00:00"
      "2026-03-10"     →  "2026-03-10T00:00:00"
      "03月10日"       →  uses current year

    Args:
        date_text: Raw date string from WeChat page

    Returns:
        ISO 8601 date string, or empty string if parsing fails
    """
    import re

    # Try Chinese format: 2026年03月10日 or 2026年3月10日
    m = re.search(r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日', date_text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00"

    # Try ISO-like: 2026-03-10 or 2026/03/10
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00"

    # Try month/day only: 03月10日 (no year)
    m = re.search(r'(\d{1,2})月\s*(\d{1,2})日', date_text)
    if m:
        year = datetime.now().year
        return f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}T00:00:00"

    return ''


def collect_wechat(urls_file: str, output_file: str = '.tmp/raw_wechat.json', delay: float = 1.0):
    """
    Main collection function.

    Args:
        urls_file: Path to file with WeChat article URLs
        output_file: Path to write output JSON
        delay: Seconds to wait between requests (be polite)
    """
    urls = load_urls(urls_file)
    print(f"Loaded {len(urls)} URLs from {urls_file}")

    if not urls:
        print("No URLs to process.")
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    articles = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Fetching: {url[:80]}...")
        article = fetch_wechat_article(url)

        if article['title']:
            print(f"  Title: {article['title'][:60]}")
        else:
            print(f"  WARNING: Could not extract title")

        if article['published_at']:
            print(f"  Date:  {article['published_at'][:10]}")

        articles.append(article)

        if i < len(urls):
            time.sleep(delay)  # Polite delay between requests

    # Save output
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Collected {len(articles)} articles → {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Collect WeChat articles from URL list')
    parser.add_argument('--urls', default='wechat_urls.txt',
                        help='Text file with WeChat article URLs (default: wechat_urls.txt)')
    parser.add_argument('--output', default='.tmp/raw_wechat.json',
                        help='Output JSON file (default: .tmp/raw_wechat.json)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Seconds between requests (default: 1.0)')
    args = parser.parse_args()

    collect_wechat(args.urls, args.output, args.delay)


if __name__ == '__main__':
    main()
