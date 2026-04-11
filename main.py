import sys
import argparse
import logging
import os
from config import load_config
from src.scraper import BestBuyScraper
from src.preprocessor import Preprocessor
from src.llm_client import LLMClient
from src.storage import StorageManager

def setup_logging(log_level="INFO", output_dir="output"):
    """Configures logging for both stdout and file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Root logger
    logging.basicConfig(level=log_level, format=log_format)
    
    # File handler
    file_handler = logging.FileHandler(os.path.join(output_dir, "run.log"))
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)
    
    # Reduce noise from requests and urllib3
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description="AI Engineer Intern — Review Analyzer CLI")
    parser.add_argument("--url", required=True, help="Best Buy product or reviews URL")
    parser.add_argument("--max-pages", type=int, default=3, help="Max review pages to scrape")
    parser.add_argument("--output-dir", default="output", help="Output directory for results")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Verbosity level")
    
    args = parser.parse_args()
    
    # 1. Setup logging
    setup_logging(args.log_level, args.output_dir)
    logger = logging.getLogger("main")
    logger.info("Starting Review Analyzer Pipeline...")
    
    # 2. Load configuration
    config = load_config()
    
    try:
        # 3. Scraper
        scraper = BestBuyScraper(delay=config["request_delay"])
        reviews = scraper.scrape(args.url, max_pages=args.max_pages)
        
        if not reviews:
            logger.warning("No reviews were found or scraped. Exiting.")
            sys.exit(0)
            
        logger.info(f"Successfully scraped {len(reviews)} reviews. Proceeding to analysis...")

        # 4. Processing and LLM Analysis
        preprocessor = Preprocessor(max_tokens=config["max_tokens_per_chunk"])
        
        # Initialize LLMClient if API key exists
        llm = None
        if config["api_key"] and config["api_key"] != "your_api_key_here":
            llm = LLMClient(
                api_key=config["api_key"],
                base_url=config["base_url"],
                model=config["model"],
                max_retries=config["max_retries"]
            )
        else:
            logger.warning("LLM Analysis will be skipped or return placeholders because API_KEY is missing.")

        for i, review in enumerate(reviews, 1):
            logger.info(f"Processing review {i}/{len(reviews)} by {review.author}")
            try:
                # Cleaning and Chunking
                chunks = preprocessor.process(review.body)
                
                if not chunks:
                    review.sentiment = "Error"
                    review.summary = "Empty body after preprocessing."
                    continue
                
                # LLM Analysis (if available)
                if llm:
                    analysis = llm.analyze(chunks)
                    review.sentiment = analysis.get("sentiment", "Unknown")
                    review.summary = analysis.get("summary", "")
                else:
                    review.sentiment = "Skipped"
                    review.summary = "(API key missing) Original text: " + (review.body[:100] + "...")
            except Exception as e:
                logger.error(f"Failed to analyze review {i}: {e}")
                review.sentiment = "Error"
                review.summary = str(e)[:200]

        # 5. Storage
        storage = StorageManager(output_dir=args.output_dir)
        paths = storage.save_all(reviews, base_name="processed_reviews")
        
        # 6. Final Summary
        logger.info("Pipeline Complete!")
        logger.info(f"Total reviews: {len(reviews)}")
        logger.info(f"CSV saved to: {paths['csv']}")
        logger.info(f"JSON saved to: {paths['json']}")
        logger.info(f"Log file: {os.path.join(args.output_dir, 'run.log')}")

    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
