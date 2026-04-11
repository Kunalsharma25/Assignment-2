import requests
import random
import time
import re
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, ConnectionError, Timeout

# Configure logger locally for this module
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

class BestBuyScraper:
    def __init__(self, delay: float = 2.0, proxies: Optional[dict] = None):
        self.delay = delay
        self.proxies = proxies
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]

    def _extract_id(self, url: str) -> str:
        """Extracts SKU or Product ID from Best Buy URL."""
        if "bestbuy.com" not in url.lower():
            raise ValueError(f"Not a Best Buy URL: {url}")
            
        # Try finding skuId parameter
        match = re.search(r'skuId=(\d+)', url)
        if match:
            return match.group(1)
        
        # Try finding trailing .p id
        match = re.search(r'/(\d+)\.p', url)
        if match:
            return match.group(1)
        
        # Try finding the product code at the end for /product/ style URLs
        match = re.search(r'/product/[^/]+/([^/?#]+)', url)
        if match:
            return match.group(1)
            
        raise ValueError(f"Could not extract product ID from URL: {url}")

    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Sends GET request and returns BeautifulSoup object."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            logger.debug(f"Fetching URL: {url}")
            response = self.session.get(url, headers=headers, proxies=self.proxies, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, "lxml")
        except (HTTPError, ConnectionError, Timeout) as e:
            logger.error(f"Error fetching page {url}: {e}")
            raise

    def _parse_reviews(self, soup: BeautifulSoup, page_url: str) -> List[Review]:
        """Parses reviews from a Best Buy page."""
        reviews_list = []
        # Best Buy review containers are often identified by 'review-item' or 'ugc-review-item'
        containers = soup.select("li.review-item, .ugc-review-item")
        
        for container in containers:
            try:
                author = container.select_one(".review-author, .ugc-author-name")
                author = author.get_text(strip=True) if author else "Anonymous"

                rating_elem = container.select_one(".review-rating, [data-testid='review-rating']")
                rating = None
                if rating_elem:
                    rating_match = re.search(r'(\d+(\.\d+)?)', rating_elem.get_text())
                    if rating_match:
                        rating = float(rating_match.group(1))

                date = container.select_one(".review-date, .ugc-review-date")
                date = date.get_text(strip=True) if date else "Unknown Date"

                title = container.select_one(".review-title, .ugc-review-title")
                title = title.get_text(strip=True) if title else ""

                body = container.select_one(".review-content, .ugc-review-body")
                body = body.get_text(strip=True) if body else ""

                verified = bool(container.select_one(".verified-purchase, .ugc-verified-badge"))

                if not body:
                    continue

                reviews_list.append(Review(
                    author=author,
                    rating=rating,
                    date=date,
                    title=title,
                    body=body,
                    verified=verified,
                    url=page_url
                ))
            except Exception as e:
                logger.warning(f"Failed to parse a review on {page_url}: {e}")
                continue
        
        return reviews_list

    def _get_next_page(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Finds next page URL."""
        # Common pagination patterns
        next_btn = soup.select_one("a.next-page-link, .pagination-next-button a")
        if next_btn and next_btn.has_attr('href'):
            next_url = next_btn['href']
            if next_url.startswith('/'):
                next_url = "https://www.bestbuy.com" + next_url
            return next_url
        return None

    def scrape(self, url: str, max_pages: int = 3) -> List[Review]:
        """Main scraping loop."""
        product_id = self._extract_id(url)
        logger.info(f"Detected Product ID: {product_id}")
        
        # Best Buy reviews are often at /site/reviews/{product_id}
        # or can be accessed by appending ?skuId={product_id} to the reviews page
        if "/reviews/" not in url:
            # Construct a probable reviews URL
            reviews_url = f"https://www.bestbuy.com/site/reviews/{product_id}"
        else:
            reviews_url = url

        all_reviews = []
        current_url = reviews_url
        
        for page in range(1, max_pages + 1):
            logger.info(f"Scraping page {page}: {current_url}")
            try:
                soup = self._fetch_page(current_url)
                page_reviews = self._parse_reviews(soup, current_url)
                all_reviews.extend(page_reviews)
                logger.info(f"Found {len(page_reviews)} reviews on page {page}.")
                
                # Check pagination
                current_url = self._get_next_page(soup, current_url)
                if not current_url:
                    break
                
                # Jitter delay
                time.sleep(self.delay + random.uniform(0.5, 1.5))
                
            except Exception as e:
                logger.error(f"Failed to scrape page {page}: {e}")
                break
        
        logger.info(f"Total reviews scraped: {len(all_reviews)}")
        return all_reviews
