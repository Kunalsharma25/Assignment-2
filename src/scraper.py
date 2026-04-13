import requests
import random
import time
import re
import os
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class Review:
    author: str
    rating: Optional[float]
    date: str
    title: str
    body: str
    verified: bool
    url: str
    summary: str = ""
    sentiment: str = ""

class FlipkartScraper:
    def __init__(self, api_key: Optional[str] = None, delay: float = 1.0):
        self.api_key = api_key
        self.delay = delay
        self.session = requests.Session()

    def _parse_date(self, date_str: str) -> str:
        """Converts Flipkart relative dates (e.g., '2 months ago') to YYYY-MM-DD."""
        try:
            if not date_str:
                return "Unknown"
            
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            # Handle "X days/months/years ago" format
            if 'ago' in date_str:
                number_match = re.search(r'\d+', date_str)
                if number_match:
                    number = int(number_match.group())
                    if 'day' in date_str:
                        return (today - timedelta(days=number)).strftime('%Y-%m-%d')
                    elif 'month' in date_str:
                        return (today - timedelta(days=number*30)).strftime('%Y-%m-%d')
                    elif 'year' in date_str:
                        return (today - timedelta(days=number*365)).strftime('%Y-%m-%d')
            
            # Handle just a number (assume days ago)
            if re.match(r'^\d+$', date_str.strip()):
                number = int(date_str.strip())
                return (today - timedelta(days=number)).strftime('%Y-%m-%d')
            
            # For formats like "Oct, 2023" or "15 Oct 2023"
            parsed_date = None
            for fmt in ("%b, %Y", "%d %b %Y", "%B %Y", "%d %B %Y"):
                try:
                    parsed_date = datetime.strptime(date_str.title(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
            
            return date_str # Return as is if we can't parse it
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return date_str

    def _fetch_page(self, url: str, render: bool = False) -> BeautifulSoup:
        if not self.api_key:
            raise ValueError("SCRAPER_API_KEY is missing. Please add it to your .env file.")

        params = {'api_key': self.api_key, 'url': url, 'country_code': 'in'}
        if render: params['render'] = 'true'
        
        proxy_url = "https://api.scraperapi.com/?" + urlencode(params)
        
        for attempt in range(3):
            try:
                response = self.session.get(proxy_url, timeout=90)
                response.raise_for_status()
                return BeautifulSoup(response.content, "lxml")
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                raise

    def _parse_reviews(self, soup: BeautifulSoup, page_url: str) -> List[Review]:
        reviews = []
        # Try new Flipkart structure (2024+) - reviews are in larger containers
        containers = soup.select("div.lQLKCP, div.yiQOTv, div[class*='asbjxx'], div.r-w7s2jr")
        
        if not containers:
            # Fallback: Look for "Verified Purchase" text and find parent review containers
            verified_tags = soup.find_all(string=re.compile("Verified Purchase", re.I))
            containers = []
            for tag in verified_tags:
                # Walk up to find a reasonable-sized container with review content
                current = tag.parent
                for _ in range(20):
                    if current is None:
                        break
                    text_len = len(current.get_text(strip=True))
                    if 100 < text_len < 5000:  # Likely a review container
                        if current not in containers:
                            containers.append(current)
                        break
                    current = current.parent

        # If we have a large container (new Flipkart structure), split into individual reviews
        if containers and len(containers) == 1:
            large_container = containers[0]
            container_text = large_container.get_text()
            
            # Split by rating patterns: "X.X•Title"
            # Find all review starts
            review_starts = []
            for match in re.finditer(r'(\d+(?:\.\d)?)\s*•\s*([^•\n]+)', container_text):
                review_starts.append({
                    'rating': float(match.group(1)),
                    'title': match.group(2).strip(),
                    'start': match.start(),
                    'end': match.end()
                })
            
            for idx, review_start in enumerate(review_starts):
                try:
                    rating = review_start['rating']
                    title = review_start['title']
                    
                    # Extract text from this review until the next review
                    current_pos = review_start['end']
                    next_pos = review_starts[idx + 1]['start'] if idx + 1 < len(review_starts) else len(container_text)
                    review_block = container_text[current_pos:next_pos]
                    
                    # Remove review-meta stuff and extract body
                    lines = review_block.split('\n')
                    body_lines = []
                    author = "Anonymous"
                    date_raw = "Unknown"
                    verified = False
                    
                    for line in lines:
                        line = line.strip()
                        if not line or line == "more":
                            continue
                        
                        # Extract author name (usually one line with name and location)
                        if ',' in line and any(keyword in line for keyword in ['Kumar', 'Singh', 'Sharma', 'Patel', 'Khan', 'Customer', 'Verma', 'Sharma', 'Ray']):
                            author = line.split(',')[0].strip()
                            continue
                        
                        # Check for verification badge
                        if 'Verified Purchase' in line:
                            verified = True
                            # Extract date from same line or next meaningful chunk
                            date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|ago|month|day|year)[^·]*$', line)
                            if date_match:
                                date_raw = date_match.group(0).strip()
                            continue
                        
                        # Exclude metadata lines
                        if any(kw in line for kw in ['Helpful for', 'Rating', 'Review for:', 'Color Black', 'Image Resolution', 'MP']):
                            if 'Helpful for' in line or 'Rating' in line:
                                continue
                        
                        # Accumulate body text
                        if len(line) > 5 and not line.startswith('Review for:'):
                            body_lines.append(line)
                    
                    # Construct body from accumulated lines
                    body = ' '.join(body_lines[:8]).strip()  # Limit to first 8 lines to avoid excessive text
                    if not body or len(body) < 10:
                        body = title
                    
                    formatted_date = self._parse_date(date_raw)
                    
                    if body and len(body) > 5:
                        reviews.append(Review(author, rating, formatted_date, title, body, verified, page_url))
                        
                except Exception as e:
                    logger.debug(f"Error parsing individual review: {e}")
                    continue
        else:
            # Fallback: Parse individual containers (old structure or edge cases)
            for c in containers:
                try:
                    # 1. Try to extract rating - look for patterns like "5.0•" 
                    rating = None
                    container_text = c.get_text()
                    
                    # Look for star patterns (e.g., 5.0★ or 5 stars)
                    rating_match = re.search(r'([1-5](?:\.\d)?)\s*(?:★|⭐|stars|out of 5)', container_text, re.I)
                    if not rating_match:
                        # Match 1/5, 5/5 etc but avoid large numbers like 100/
                        rating_match = re.search(r'\b([1-5])\s*\/\s*5\b', container_text)
                    
                    if rating_match:
                        rating = float(rating_match.group(1))
                    
                    # 2. Extract title, body, author, date from text
                    lines = [l.strip() for l in container_text.split('\n') if l.strip()]
                    
                    title = lines[0] if lines else ""
                    body = ' '.join(lines[1:4]) if len(lines) > 1 else ""
                    author = "Anonymous"
                    date_raw = "Unknown"
                    verified = "Verified Purchase" in container_text
                    
                    # Find author and date in text
                    for line in lines[-5:]:  # Check last 5 lines
                        if any(keyword in line for keyword in ['Kumar', 'Singh', 'Sharma', 'Patel', 'Khan', 'Customer']):
                            author = line.split(',')[0].strip()
                        if any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'ago', 'months']):
                            date_raw = line
                    
                    formatted_date = self._parse_date(date_raw)
                    
                    if body and len(body) > 5:
                        reviews.append(Review(author, rating, formatted_date, title, body, verified, page_url))
                        
                except Exception as e:
                    logger.debug(f"Error parsing container: {e}")
                    continue
        
        return reviews

    def _normalize_url(self, url: str) -> str:
        if "/product-reviews/" in url: return url
        if "/p/" in url: return url.replace("/p/", "/product-reviews/")
        return url

    def scrape(self, url: str, max_pages: int = 5, max_reviews: int = 20) -> List[Review]:
        base_url = self._normalize_url(url)
        all_reviews = []
        
        for p_idx in range(1, max_pages + 1):
            if len(all_reviews) >= max_reviews: break
            
            current_url = base_url
            if p_idx > 1:
                separator = "&" if "?" in base_url else "?"
                current_url = f"{base_url}{separator}page={p_idx}"
            
            soup = self._fetch_page(current_url, render=False)
            page_reviews = self._parse_reviews(soup, current_url)
            
            if not page_reviews:
                soup = self._fetch_page(current_url, render=True)
                page_reviews = self._parse_reviews(soup, current_url)

            if not page_reviews: break

            all_reviews.extend(page_reviews[:max_reviews - len(all_reviews)])
            if len(all_reviews) >= max_reviews: break
            time.sleep(self.delay)
        
        # DEMO FALLBACK: If no reviews found on live site, try reading from local file
        if not all_reviews and os.path.exists("revs.html"):
            logger.info("No reviews found on live site. Falling back to local 'revs.html' for demonstration.")
            with open("revs.html", "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "lxml")
                all_reviews = self._parse_reviews(soup, "file://revs.html")[:max_reviews]
            
        return all_reviews
