import pytest
from src.scraper import BestBuyScraper

@pytest.fixture
def scraper():
    return BestBuyScraper()

def test_extract_id_skuid(scraper):
    url = "https://www.bestbuy.com/site/apple-watch-ultra-2/6321398.p?skuId=6321398"
    assert scraper._extract_id(url) == "6321398"

def test_extract_id_p(scraper):
    url = "https://www.bestbuy.com/site/apple-watch-ultra-2/6321398.p"
    assert scraper._extract_id(url) == "6321398"

def test_extract_id_product(scraper):
    url = "https://www.bestbuy.com/product/apple-watch-ultra-2-gps-cellular-49mm-titanium-case-with-black-ocean-band-black-2024/JJGCQ3FLGQ"
    assert scraper._extract_id(url) == "JJGCQ3FLGQ"

def test_extract_id_invalid(scraper):
    url = "https://www.google.com"
    with pytest.raises(ValueError):
        scraper._extract_id(url)
