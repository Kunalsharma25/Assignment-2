"""
Module for scraping product reviews from Flipkart using ScraperAPI and BeautifulSoup.
Provides the Review dataclass and the FlipkartScraper class.
"""
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
    """
    Represents a single scraped review.
    """
    author: str
    rating: Optional[float]
    date: str
    title: str
    body: str
    verified: bool
    url: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None

class FlipkartScraper:
    def __init__(self, api_key: Optional[str] = None, delay: float = 2.0):
        self.api_key = api_key
        self.delay = delay
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]

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
        
        headers = {'User-Agent': random.choice(self.user_agents)}
        
        for attempt in range(3):
            try:
                response = self.session.get(proxy_url, headers=headers, timeout=90)
                
                if response.status_code == 401:
                    logger.error("SCRAPER_API_KEY is invalid or unauthorized (401). Please check your .env file.")
                    return None
                if response.status_code == 403:
                    logger.error("SCRAPER_API_KEY has no credits or is blocked (403).")
                    return None
                if response.status_code == 429:
                    logger.warning("ScraperAPI rate limit reached (429). Retrying after delay...")
                    time.sleep(self.delay * 2)
                    continue

                response.raise_for_status()
                return BeautifulSoup(response.content, "lxml")
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                raise

    def _parse_reviews(self, soup: BeautifulSoup, page_url: str) -> List[Review]:
        """
        Parses review data from the provided soup object using a tiered heuristic approach:
        1. Explicit Selector Layer: Targets specific known Flipkart CSS classes.
        2. Sequence-Aware Walker: Identifies metadata (Author, Date, Verification) by analyzing 
           textual sequences relative to the 'Verified Purchase' badge.
        """
        reviews = []
        
        # --- LAYER 1: Explicit Selector Layer (Fastest) ---
        # Look for known review containers (2024-2025 structures)
        selectors = [
            "div.lQLKCP", "div.yiQOTv", "div.r-w7s2jr", "div.col._2wYq0G", 
            "div[class*='asbjxx']", "div.EKm096", "div.row._3879fbc", "div.css-g5y9jx.r-w7s2jr"
        ]
        containers = soup.select(", ".join(selectors))
        logger.debug(f"Layer 1: Found {len(containers)} containers via selectors.")
        
        # --- LAYER 2: Keyword-based Walker Layer (Robustness) ---
        if len(containers) < 3:
            # Look for "Verified Purchase" or "Certified Buyer" tags
            identity_tags = soup.find_all(string=re.compile(r"Verified Purchase|Certified Buyer", re.I))
            logger.debug(f"Layer 2: Found {len(identity_tags)} identity tags.")
            new_containers = []
            for tag in identity_tags:
                # Walk up to find a container with a reasonable length
                current = tag.parent
                for _ in range(15):
                    if current is None: break
                    t = current.get_text(strip=True)
                    # Review blocks are usually 150-3000 chars in this structure
                    if 150 < len(t) < 3000:
                        if current not in new_containers:
                            new_containers.append(current)
                        break
                    current = current.parent
            
            if len(new_containers) > len(containers):
                logger.debug(f"Layer 2: Upgraded to {len(new_containers)} containers via walking.")
                containers = new_containers
        
        # --- LAYER 3: Parsing Found Containers ---
        logger.info(f"Parsing {len(containers)} potential review containers.")
        
        for c in containers:
            try:
                # 1. Extract All Text Pieces in Sequence
                # This is the most robust way to handle React's fragmented structure
                pieces = [p.strip() for p in c.get_text("\n").split("\n") if p.strip()]
                if not pieces: continue
                full_text_joined = " ".join(pieces)

                # 2. Extract Rating
                rating = None
                # Method A: Search for star pattern (e.g. 5★)
                rating_match = re.search(r'([1-5](?:\.\d)?)\s*(?:★|⭐|stars|out of 5)', full_text_joined, re.I)
                if rating_match:
                    rating = float(rating_match.group(1))
                else:
                    # Method B: Search for standalone digit line (1-5)
                    for p in pieces[:5]:
                        if re.match(r'^[1-5]$', p):
                            rating = float(p)
                            break
                    
                    if not rating:
                        # Method C: Find color-coded rating label classes
                        labels = c.find_all(class_=re.compile(r"_3LWZlK|_1738d9f|rating|r-1h7g6bg", re.I))
                        for label in labels:
                            label_match = re.search(r'^([1-5](\.\d)?)$', label.get_text().strip())
                            if label_match:
                                rating = float(label_match.group(1))
                                break

                # 3. Sequence-Aware Metadata Extraction (Author, Date, Verified)
                author = "Anonymous"
                date_raw = "Unknown"
                verified = any("Verified" in p or "Certified Buyer" in p for p in pieces)
                
                # Find the index of the verification badge
                v_idx = -1
                for i, p in enumerate(pieces):
                    if "Verified Purchase" in p or "Certified Buyer" in p:
                        v_idx = i
                        break
                
                if v_idx != -1:
                    # The author is usually 1-3 positions before the badge
                    # Pattern: [Name] [,] [Location] [Count] [Count] [Verified]
                    # We look for the first piece that isn't a comma or numbers
                    for i in range(max(0, v_idx - 5), v_idx):
                        if (i + 1 < len(pieces) and pieces[i+1].startswith(',')) or pieces[i].startswith(','):
                             # This is likely the author piece (the one before the comma)
                             author_cand = pieces[i] if not pieces[i].startswith(',') else pieces[max(0,i-1)]
                             if len(author_cand) > 2 and not any(kw in author_cand for kw in ['Verified', 'Certified', 'Buyer']):
                                 author = author_cand
                                 break
                    
                    # Date is usually immediately AFTER the badge or in the same piece
                    for i in range(v_idx, min(len(pieces), v_idx + 3)):
                        if any(m in pieces[i] for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'ago']):
                            date_raw = pieces[i]
                            break
                
                # 4. Extract Title & Body
                title = pieces[0]
                # If title is just a rating number, shift to next
                if re.match(r'^[1-5]$', title) and len(pieces) > 1:
                    title = pieces[1]
                
                # Filter out summary blocks (e.g. "659 ratings and 86 reviews")
                if "ratings" in title.lower() and "reviews" in title.lower():
                    continue
                if "sorted by" in title.lower():
                    continue
                
                # Body is usually the longest piece that isn't metadata
                body_candidates = [p for p in pieces if len(p) > 20 and p != title and "Review for:" not in p]
                body = max(body_candidates, key=len) if body_candidates else title

                formatted_date = self._parse_date(date_raw)
                
                if body and len(body) > 10:
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
        
        return all_reviews
