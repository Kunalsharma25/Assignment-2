# AI Engineer Intern — Assignment 2: Review Analyzer

A Python-based application that scrapes product reviews from Best Buy, cleans and chunks them for LLM processing, and generates sentiment/summary analysis using an OpenAI-compatible API.

## Chosen Product URL
- **Product:** Apple Watch Ultra 2 (2024)
- **URL:** [Best Buy Product Page](https://www.bestbuy.com/product/apple-watch-ultra-2-gps-cellular-49mm-titanium-case-with-black-ocean-band-black-2024/JJGCQ3FLGQ)
- **Why:** This is a premium, high-volume product with diverse and detailed customer reviews, perfect for testing sentiment analysis and summarization.

## Setup Instructions

1.  **Clone the Repository**
2.  **Activate Virtual Environment** (e.g., `conda activate asg2_env`)
3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**
    Copy `.env.example` to `.env` and fill in your OpenAI-compatible API key.
    ```bash
    copy .env.example .env
    ```

## How to Run

Execute the pipeline using `main.py`:

```bash
python main.py --url "https://www.bestbuy.com/product/apple-watch-ultra-2-gps-cellular-49mm-titanium-case-with-black-ocean-band-black-2024/JJGCQ3FLGQ" --max-pages 2
```

### CLI Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | (Required) | The Best Buy product or reviews URL. |
| `--max-pages` | `3` | Maximum number of review pages to scrape. |
| `--output-dir` | `output` | Directory for output CSV/JSON files. |
| `--log-level` | `INFO` | Verbosity (DEBUG, INFO, WARNING, ERROR). |

## Output Files

After a successful run, the following files will be created in the `output/` directory:

- `processed_reviews.csv`: A structured CSV with columns: `author`, `date`, `rating`, `verified`, `title`, `body`, `sentiment`, `summary`, `url`.
- `processed_reviews.json`: The same data in JSON format for easy programmatic ingestion.
- `run.log`: A detailed execution log for troubleshooting and verification.

## Design Choices

1.  **Modular Architecture**: Isolated modules for scraping, preprocessing, LLM client, and storage to ensure testability and extensibility.
2.  **OpenAI-Compatible Abstraction**: Uses the standard OpenAI SDK, allowing easy swapping of providers (OpenAI, Groq, Ollama) via environment variables.
3.  **Token-Aware Chunking**: Uses `tiktoken` to split long reviews into manageable overlapping chunks to stay within model context windows and preserve context.
4.  **Exponential Backoff**: Robust API call logic that handles rate limits (429) and server errors (5xx) with automatic retries.
5.  **Robust Scraper**: Implements User-Agent rotation and randomized delays to minimize bot detection.

## Limitations

- **Bot Detection**: Retail sites like Best Buy aggressively block automated scrapers. If the site layout changes, CSS selectors may need updates.
- **Review Content**: Currently focuses on text-based reviews. media/images and Q&A sections are excluded.
- **API Costs**: Each review analyzed incurs token costs from your LLM provider.
