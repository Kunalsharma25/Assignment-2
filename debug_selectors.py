import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('SCRAPER_API_KEY')

import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup

url = 'https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ&lid=LSTACCH28H2F69RKYQZVLDFGX&marketplace=FLIPKART'
params = {'api_key': api_key, 'url': url, 'country_code': 'in', 'render': 'true'}
proxy_url = 'https://api.scraperapi.com/?' + urlencode(params)

print('Fetching with JavaScript rendering...')
response = requests.get(proxy_url, timeout=60)

soup = BeautifulSoup(response.text, 'lxml')

# Try to find review containers
print('Looking for review containers...')
res1 = soup.select('div.col._2wY_9c')
print(f'Found div.col._2wY_9c: {len(res1)}')

res2 = soup.select('div._27M-N_')
print(f'Found div._27M-N_: {len(res2)}')

# Look for text that says Verified Purchase
verified = soup.find_all(string=lambda text: text and 'Verified' in text)
print(f'Found Verified Purchase tags: {len(verified)}')

# Try broader selectors
divs_with_verified = []
for tag in soup.find_all(string=lambda text: text and 'Verified Purchase' in text):
    parent = tag.find_parent('div')
    if parent:
        divs_with_verified.append(parent)

print(f'Parent divs containing Verified Purchase: {len(divs_with_verified)}')
if divs_with_verified:
    classes = divs_with_verified[0].get('class')
    print(f'First parent div classes: {classes}')

# Save a sample of the HTML to inspect
with open('d:\\Assigment_2\\sample_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text[:5000])
    print('Saved first 5000 chars to sample_page.html')
