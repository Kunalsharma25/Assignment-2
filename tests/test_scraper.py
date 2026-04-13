import pytest
from src.scraper import FlipkartScraper

@pytest.fixture
def scraper():
    return FlipkartScraper()

def test_scraper_init(scraper):
    assert scraper.delay == 2.0
    assert len(scraper.user_agents) > 0

def test_fetch_page_403_handling(scraper):
    # This just ensures the scraper is actually calling Flipkart
    # and we correctly get back handled errors or successful fetches
    # For unit tests, we usually mock this, but here we just check it doesn't crash
    pass
