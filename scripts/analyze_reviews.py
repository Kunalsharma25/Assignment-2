import os
import re
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('SCRAPER_API_KEY')

import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup

url = 'https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ&lid=LSTACCH28H2F69RKYQZVLDFGX&marketplace=FLIPKART'
params = {'api_key': api_key, 'url': url, 'country_code': 'in', 'render': 'true'}
proxy_url = 'https://api.scraperapi.com/?' + urlencode(params)

print('Fetching page with JavaScript rendering...')
response = requests.get(proxy_url, timeout=60)
soup = BeautifulSoup(response.text, 'lxml')

# Find all text nodes containing "Verified"
verified_tags = soup.find_all(string=re.compile("Verified", re.I))
print(f'\nFound {len(verified_tags)} "Verified Purchase" tags\n')

if verified_tags:
    # Get the first few review containers
    review_containers = []
    for tag in verified_tags[:5]:
        # Walk up the DOM to find the container
        parent = tag.parent
        for _ in range(10):  # Go up max 10 levels
            if parent is None:
                break
            parent = parent.parent
            if parent and 'class' in parent.attrs:
                classes = ' '.join(parent.get('class', []))
                if len(classes) > 0 and len(parent.get_text()) < 2000:  # Reasonable size
                    review_containers.append(parent)
                    break
    
    # Print structure
    print("Sample review HTML structure:")
    if review_containers:
        sample = review_containers[0]
        print(f"Container tag: {sample.name}")
        print(f"Container classes: {sample.get('class', [])}")
        print(f"Container HTML (first 1000 chars):\n{str(sample)[:1000]}\n")
        
        # Find all divs within
        divs = sample.find_all('div', limit=20)
        print(f"Number of divs in first container: {len(divs)}")
        
        # Try to find rating
        rating_text = sample.get_text()
        rating_match = re.search(r'(\d+(?:\.\d+)?)\s*★', rating_text)
        if rating_match:
            print(f"Found rating: {rating_match.group(1)}")
            
        # Find text elements
        spans = sample.find_all('span', limit=30)
        print(f"\nSpan elements in container:")
        for i, sp in enumerate(spans[:10]):
            text = sp.get_text(strip=True)
            if text and len(text) < 100:
                print(f"  {i}: {text}")

# Save full HTML for inspection
with open('d:\\Assigment_2\\full_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
    print(f"\nSaved full HTML to full_page.html ({len(response.text)} chars)")
