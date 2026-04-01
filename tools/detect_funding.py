#!/usr/bin/env python3
"""
Detect funding events and classify articles

Strategy:
1. Load all raw JSON files from .tmp/
2. Apply funding keyword matching
3. Extract funding details (company, series, amount, investors)
4. Classify articles as is_funding: true/false
5. Output classified articles + structured funding events

Outputs:
- .tmp/classified_articles.json (all articles with classification)
- .tmp/funding_events.json (structured funding data)
"""

import os
import sys
import json
import argparse
import re
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.utils import clean_text, deduplicate_articles

# Funding keywords
FUNDING_KEYWORDS = [
    'raised', 'raises', 'raising', 'funding', 'investment', 'invested',
    'series a', 'series b', 'series c', 'series d', 'series e',
    'seed round', 'pre-seed', 'venture capital', 'vc', 'valuation',
    'funding round', 'investors', 'ipo', 'acquisition', 'acquires',
    'acquired', 'm&a', 'merger', 'buyout', 'angel investment',
    'led by', 'backed by', 'capital raise'
]

# Regex patterns for extraction
SERIES_PATTERN = r'(pre-seed|seed|series [A-F]|Series [A-F]|ipo|IPO)'
AMOUNT_PATTERN = r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B|m|b)'
COMPANY_PATTERN = r'^([A-Z][a-zA-Z0-9\s&\'\-\.]+?)(?:\s+raises|\s+raised|\s+secures|\s+secured|\s+announces|\s+announced|\s+gets|\s+closes)'


def is_funding_article(text: str) -> bool:
    """
    Determine if article is about funding

    Args:
        text: Combined title + description + content

    Returns:
        Boolean indicating if it's funding-related
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FUNDING_KEYWORDS)


def extract_series(text: str) -> str:
    """
    Extract funding series from text

    Args:
        text: Article text

    Returns:
        Series string (e.g., 'Series A') or 'N/A'
    """
    match = re.search(SERIES_PATTERN, text, re.IGNORECASE)
    if match:
        series = match.group(1)
        # Normalize capitalization
        if series.lower() in ['ipo', 'pre-seed', 'seed']:
            return series.capitalize()
        else:
            return 'Series ' + series.split()[-1].upper()
    return 'N/A'


def extract_amount(text: str) -> str:
    """
    Extract funding amount from text

    Args:
        text: Article text

    Returns:
        Amount string (e.g., '$50M') or 'N/A'
    """
    match = re.search(AMOUNT_PATTERN, text)
    if match:
        value = match.group(1)
        unit = match.group(2).upper()

        # Normalize unit
        if unit in ['BILLION', 'B']:
            return f"${value}B"
        else:
            return f"${value}M"

    return 'N/A'


def extract_company(text: str) -> str:
    """
    Extract company name from text

    Args:
        text: Article text (title or first paragraph)

    Returns:
        Company name or 'Unknown'
    """
    # Try pattern matching
    match = re.search(COMPANY_PATTERN, text)
    if match:
        company = match.group(1).strip()
        # Remove trailing punctuation
        company = re.sub(r'[,;:\.]$', '', company)
        return company

    # Fallback: extract first capitalized phrase before funding keyword
    for keyword in ['raises', 'raised', 'secures', 'secured']:
        if keyword in text.lower():
            parts = text.split(keyword)[0].strip()
            # Take last capitalized phrase
            words = parts.split()
            company_words = []
            for word in reversed(words):
                if word and word[0].isupper():
                    company_words.insert(0, word)
                else:
                    break
            if company_words:
                return ' '.join(company_words)

    return 'Unknown'


def extract_investors(text: str) -> List[str]:
    """
    Extract investor names from text

    Args:
        text: Article text

    Returns:
        List of investor names
    """
    investors = []

    # Look for "led by" or "backed by" patterns
    patterns = [
        r'led by ([^\.]+)',
        r'backed by ([^\.]+)',
        r'investors include ([^\.]+)',
        r'from ([A-Z][a-zA-Z\s&]+(?:Capital|Ventures|Partners|Fund|Investments))',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            investor_text = match.group(1)
            # Split by common delimiters
            parts = re.split(r',|\sand\s', investor_text)
            for part in parts:
                part = part.strip()
                if part and len(part) > 2:
                    investors.append(part)

    # Deduplicate
    investors = list(set(investors))

    return investors if investors else ['N/A']


def extract_funding_details(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all funding details from article

    Args:
        article: Article dictionary

    Returns:
        Dictionary with funding details
    """
    # Combine all text for analysis
    full_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"

    # Extract details
    company = extract_company(article.get('title', '') + ' ' + article.get('description', ''))
    series = extract_series(full_text)
    amount = extract_amount(full_text)
    investors = extract_investors(full_text)

    return {
        'date': article.get('published_at', ''),
        'company': company,
        'summary': article.get('description', '')[:200],  # Truncate to 200 chars
        'series': series,
        'amount': amount,
        'investors': investors,
        'url': article.get('url', ''),
        'source': article.get('source', '')
    }


def classify_articles(input_dir: str = '.tmp') -> tuple:
    """
    Classify all articles and extract funding events

    Args:
        input_dir: Directory containing raw JSON files

    Returns:
        Tuple of (classified_articles, funding_events)
    """
    # Load all raw articles
    all_articles = []

    raw_files = [
        'raw_techcrunch.json',
        'raw_tldr_ai.json',
        'raw_tldr_main.json',
        'raw_substack.json'
    ]

    for filename in raw_files:
        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            print(f"Loading {filename}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                all_articles.extend(articles)
                print(f"  Loaded {len(articles)} articles")
        else:
            print(f"WARNING: {filepath} not found, skipping")

    print(f"\nTotal articles loaded: {len(all_articles)}")

    # Deduplicate
    print("Deduplicating articles...")
    all_articles = deduplicate_articles(all_articles)
    print(f"After deduplication: {len(all_articles)} articles")

    # Classify and extract funding
    print("\nClassifying articles...")
    funding_events = []
    classified_articles = []

    for article in all_articles:
        # Combine text for analysis
        full_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"

        # Check if funding-related
        is_funding = is_funding_article(full_text)

        # Add classification to article
        article['is_funding'] = is_funding
        classified_articles.append(article)

        # Extract funding details if applicable
        if is_funding:
            funding_event = extract_funding_details(article)
            funding_events.append(funding_event)

    print(f"✓ Classified {len(classified_articles)} articles")
    print(f"✓ Found {len(funding_events)} funding events")

    return classified_articles, funding_events


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Detect funding events and classify articles')
    parser.add_argument('--input_dir', default='.tmp', help='Input directory with raw JSON files')
    parser.add_argument('--output_dir', default='.tmp', help='Output directory')
    args = parser.parse_args()

    # Classify articles
    classified_articles, funding_events = classify_articles(args.input_dir)

    # Save outputs
    os.makedirs(args.output_dir, exist_ok=True)

    classified_output = os.path.join(args.output_dir, 'classified_articles.json')
    with open(classified_output, 'w', encoding='utf-8') as f:
        json.dump(classified_articles, f, ensure_ascii=False, indent=2)

    funding_output = os.path.join(args.output_dir, 'funding_events.json')
    with open(funding_output, 'w', encoding='utf-8') as f:
        json.dump(funding_events, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved classified articles to {classified_output}")
    print(f"✓ Saved funding events to {funding_output}")


if __name__ == "__main__":
    main()
