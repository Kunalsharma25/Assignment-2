import os
import re
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('SCRAPER_API_KEY')

import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup

url = 'https://www.flipkart.com/kreo-owl-2-mp-hd-webcam-built-in-microphone-usb-connectivity/product-reviews/itm54f9eb7aea317?pid=ACCGSUTCPGSCZSFF&lid=LSTACCGSUTCPGSCZSFFDSGC3Q&marketplace=FLIPKART'
params = {'api_key': api_key, 'url': url, 'country_code': 'in', 'render': 'true'}
proxy_url = 'https://api.scraperapi.com/?' + urlencode(params)

print('Fetching Flipkart product reviews page...')
response = requests.get(proxy_url, timeout=60)
soup = BeautifulSoup(response.text, 'lxml')

# Strategy: Find "Verified Purchase" and examine the container structure
verified_tags = soup.find_all(string=re.compile("Verified", re.I))
print(f'Found {len(verified_tags)} "Verified Purchase" elements\n')

if verified_tags:
    print("Analyzing structure of first 3 review containers:\n")
    for idx, verified_tag in enumerate(verified_tags[:3]):
        print(f"--- Review {idx+1} ---")
        
        # Find all parent divs and their structures
        current = verified_tag.parent
        for level in range(15):
            if current is None:
                break
            if current.name == 'div' and 'class' in current.attrs:
                text_content = current.get_text(strip=True)[:150]
                classes = current.get('class', [])
                print(f"Level {level}: {current.name} - Classes: {classes}")
                print(f"  Text preview: {text_content}...")
                
                if 'Verified' in text_content:
                    print(f"  ^ This contains review content")
                    # Save this div's HTML for inspection
                    div_html = str(current)[:2000]
                    print(f"  HTML preview:\n{div_html}\n")
                    break
            current = current.parent
        print()

# Try to extract individual fields from the structure
print("\n" + "="*60)
print("Attempting to extract review fields:")
print("="*60)

# Look for review content nested under parent containing Verified Purchase
for idx, verified_tag in enumerate(verified_tags[:1]):
    # Go up to find the main review container
    parent = verified_tag.parent
    for _ in range(10):
        parent = parent.parent
        if parent is None:
            break
        text_len = len(parent.get_text(strip=True))
        if 500 < text_len < 3000:  # Likely a full review
            print(f"\nFound likely review container at level {_}")
            
            review_text = parent.get_text()
            print(f"Full text ({len(review_text)} chars):")
            print(review_text[:500])
            
            # Try to find rating (look for numbers followed by stars)
            rating_match = re.search(r'(\d+(?:\.\d)?)\s*(?:★|⭐)', review_text)
            if rating_match:
                print(f"\nRating found: {rating_match.group(1)} stars")
            
            # Look for all span and p elements
            print("\nElements in this container:")
            for elem in parent.find_all(['span', 'p'], recursive=True, limit=20):
                text = elem.get_text(strip=True)
                if text and 5 < len(text) < 200:
                    print(f"  - {text[:80]}")
            break
