import os
import json
import logging
import pandas as pd
from dataclasses import asdict
from typing import List, Dict

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

    def convert_to_df(self, reviews: List[object]) -> pd.DataFrame:
        """Converts a list of Review objects to a Pandas DataFrame."""
        records = [asdict(r) for r in reviews]
        df = pd.DataFrame(records)
        # Reorder columns as requested
        cols = ['author', 'date', 'rating', 'verified', 'title', 'body', 'sentiment', 'summary', 'url']
        # Only reorder if columns exist
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols]

    def save_csv(self, reviews: List[object], filename: str) -> str:
        """Saves reviews to CSV."""
        df = self.convert_to_df(reviews)
        path = os.path.join(self.output_dir, filename)
        if not path.endswith(".csv"):
            path += ".csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(reviews)} reviews to {path}")
        return path

    def save_json(self, reviews: List[object], filename: str) -> str:
        """Saves reviews to JSON."""
        records = [asdict(r) for r in reviews]
        path = os.path.join(self.output_dir, filename)
        if not path.endswith(".json"):
            path += ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(reviews)} reviews to {path}")
        return path

    def save_all(self, reviews: List[object], base_name: str = "reviews") -> Dict[str, str]:
        """Saves both CSV and JSON."""
        csv_path = self.save_csv(reviews, f"{base_name}.csv")
        json_path = self.save_json(reviews, f"{base_name}.json")
        return {"csv": csv_path, "json": json_path}
