# Flipkart Review Analyzer & Sentiment Engine 🚀

A high-performance Python application designed to scrape, preprocess, and analyze e-commerce product reviews. This system uses a sophisticated **multi-layer heuristic scraper** to bypass dynamic DOM structures and leverages **Groq-powered LLMs** to generate sentimental analysis and final product verdicts.

## ✨ Key Features

- **Layered Heuristic Scraper**: Robust parsing logic using CSS selectors and a unique **Sequence-Aware Walker** to handle fragmented React layouts.
- **Bypass Bot Detection**: Integrated with **ScraperAPI** for proxy rotation and automated browser rendering.
- **LLM Intelligence**: Powered by OpenAI-compatible APIs (Groq/OpenAI) to generate concise summaries and sentiment classifications.
- **Automatic Final Verdict**: Aggregates all scraped reviews to provide a high-level recommendation (Strengths, Weaknesses, and Recommendation status).
- **Token-Aware Chunking**: Efficiently handles long reviews by chunking text based on token counts to stay within model limits.

---

## 🛠️ Setup Instructions

### 1. Environment Configuration
Clone the repository and install the dependencies:
```bash
conda activate asg2_env
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the root directory (or update the existing one):
```env
# LLM Configuration
OPENAI_API_KEY=your_groq_or_openai_key
BASE_URL=https://api.groq.com/openai/v1  # Example for Groq
MODEL=llama3-70b-8192

# Scraping Configuration
SCRAPER_API_KEY=your_scraper_api_key
REQUEST_DELAY=2.0
```

---

## 🚀 Usage

Execute the pipeline for any Flipkart product using the CLI:

```bash
python main.py --url "https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0" --max-reviews 20
```

### CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| `--url` | (Required) | The Flipkart product or review page URL. |
| `--max-reviews` | `20` | Total number of reviews to extract. |
| `--output-dir` | `output` | Directory where results will be saved. |

---

## 📊 Outputs

The analyzer produces structured data in the `output/` directory:

- 📄 `flipkart_reviews.csv`: Tabular data with ratings, authors, and sentiment.
- 📄 `flipkart_reviews.json`: Structured JSON for programmatic use.
- 📄 `final_verdict.json`: The LLM-generated summary and purchase recommendation.
- 📄 `run.log`: Detailed execution history for verification.

---

## 🛡️ Scraping Logic & Ethics

This project is built for educational purposes and implements several best practices:
1.  **Throttling**: Randomized delays to ensure respectful request volume.
2.  **User-Agent Rotation**: Simulates diverse browser environments.
3.  **Proxying**: Uses ScraperAPI to ensure stability and bypass aggressive bot detection while adhering to reasonable usage limits.

## 📝 Limitations
- Requires a valid ScraperAPI key for live scraping.
- LLM outputs depend on the quality and specificity of the user-provided reviews.
