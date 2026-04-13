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

print('Fetching product reviews page...')
response = requests.get(proxy_url, timeout=60)
soup = BeautifulSoup(response.text, 'lxml')

# Find "Verified Purchase" elements
verified_tags = soup.find_all(string=re.compile("Verified", re.I))
print(f'Found {len(verified_tags)} "Verified Purchase" elements\n')

if verified_tags:
    # Analyze the first review completely
    verified_tag = verified_tags[0]
    parent = verified_tag.parent
    
    print("Walking up the DOM from 'Verified Purchase':\n")
    for level in range(25):
        if parent is None:
            break
        if parent.name == 'div':
            classes = parent.get('class', [])
            text_len = len(parent.get_text(strip=True))
            id_attr = parent.get('id', 'N/A')
            print(f"Level {level}: <div> id='{id_attr}' class='{' '.join(classes)}' - text_length={text_len}")
            
            # Found likely review container when text is substantial  
            if 300 < text_len < 5000:
                print(f"  >>> LIKELY REVIEW CONTAINER <<<")
                print(f"\nFirst 2000 chars of content:")
                print(parent.get_text()[:2000])
                print(f"\nHTML structure (first 3000 chars):")
                print(str(parent)[:3000])
                break
        
        parent = parent.parent
