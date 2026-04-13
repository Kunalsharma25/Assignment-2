import sys
import argparse
import logging
import os
from config import load_config
from src.scraper import FlipkartScraper
from src.preprocessor import Preprocessor
from src.llm_client import LLMClient
from src.storage import StorageManager

def setup_logging(log_level="INFO", output_dir="output"):
    """Configures logging for both stdout and file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=log_level, format=log_format)
    
    file_handler = logging.FileHandler(os.path.join(output_dir, "run.log"))
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)
    
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description="Flipkart Review Analyzer CLI")
    parser.add_argument("--url", required=True, help="Flipkart product reviews URL")
    parser.add_argument("--max-reviews", type=int, default=20, help="Max reviews to scrape (default 20)")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--log-level", default="INFO", help="Verbosity level")
    
    args = parser.parse_args()
    setup_logging(args.log_level, args.output_dir)
    logger = logging.getLogger("main")
    
    config = load_config()
    
    try:
        # 1. Scraper
        scraper = FlipkartScraper(api_key=config["scraper_api_key"], delay=config["request_delay"])
        reviews = scraper.scrape(args.url, max_pages=20, max_reviews=args.max_reviews)
        
        if not reviews:
            logger.warning("No reviews scraped. Check URL or site structure.")
            sys.exit(0)
            
        # 2. Preprocessing and Analysis
        preprocessor = Preprocessor(max_tokens=config["max_tokens_per_chunk"])
        llm = None
        if config["api_key"] and config["api_key"] != "your_api_key_here":
            llm = LLMClient(config["api_key"], config["base_url"], config["model"])
        else:
            logger.warning("No valid API Key found. Analysis will return placeholders.")

        for i, review in enumerate(reviews, 1):
            logger.info(f"Processing review {i}/{len(reviews)}")
            chunks = preprocessor.process(review.body)
            if not chunks:
                review.sentiment, review.summary = "Error", "Empty body."
                continue
            
            if llm:
                analysis = llm.analyze(chunks)
                review.sentiment = analysis.get("sentiment", "Unknown")
                review.summary = analysis.get("summary", "")
            else:
                review.sentiment = "Skipped"
                review.summary = review.body[:100] + "..."

        # 2b. Generate Final Verdict
        final_verdict = {}
        if llm and reviews:
            logger.info("\n" + "="*60)
            logger.info("GENERATING FINAL PRODUCT VERDICT...")
            logger.info("="*60)
            final_verdict = llm.generate_final_verdict(reviews)
            logger.info("\n[ANALYSIS] FINAL VERDICT:")
            logger.info(f"   Overall Sentiment: {final_verdict.get('overall_sentiment', 'Unknown')}")
            logger.info(f"   Strengths: {final_verdict.get('strengths', 'N/A')}")
            logger.info(f"   Weaknesses: {final_verdict.get('weaknesses', 'N/A')}")
            logger.info(f"   Verdict: {final_verdict.get('verdict', 'N/A')}")
            logger.info(f"   RECOMMENDED: {final_verdict.get('recommendation', 'Unknown').upper()}")
            logger.info("="*60 + "\n")

        # 3. Storage
        storage = StorageManager(output_dir=args.output_dir)
        paths = storage.save_all(reviews, base_name="flipkart_reviews")
        
        # Save final verdict to file
        if final_verdict:
            import json
            verdict_path = os.path.join(args.output_dir, "final_verdict.json")
            with open(verdict_path, 'w', encoding='utf-8') as f:
                json.dump(final_verdict, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved final verdict to {verdict_path}")
        
        logger.info(f"Pipeline Complete! Scraped {len(reviews)} reviews.")
        logger.info(f"Saved to {paths['csv']} and {paths['json']}")

    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
