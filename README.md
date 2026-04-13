# AI Engineer Intern — Assignment 2: Review Analyzer

A Python-based application that scrapes product reviews from Flipkart, cleans and chunks them for LLM processing, and generates sentiment/summary analysis using an OpenAI-compatible API.

## Chosen Product URL
- **Product:** HP 320 5MP HD Webcam
- **URL:** [Flipkart Product Page](https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ)
- **Why:** High-volume consumer electronics with diverse customer reviews, ideal for testing sentiment analysis and summarization.

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
python main.py --url "https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ" --max-reviews 10
```

### CLI Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | (Required) | The Flipkart product URL. |
| `--max-reviews` | `10` | Maximum number of reviews to scrape. |
| `--output-dir` | `output` | Directory for output CSV/JSON files. |
| `--log-level` | `INFO` | Verbosity (DEBUG, INFO, WARNING, ERROR). |

## Output Files

After a successful run, the following files will be created in the `output/` directory:

- `processed_reviews.csv`: A structured CSV with columns: `author`, `date`, `rating`, `verified`, `title`, `body`, `sentiment`, `summary`, `url`.
- `processed_reviews.json`: The same data in JSON format for easy programmatic ingestion.
- `final_verdict.json`: A high-level LLM-generated analysis of the overall product quality, strengths, and weaknesses.
- `run.log`: A detailed execution log for troubleshooting and verification.

## Design Choices

1.  **Modular Architecture**: Isolated modules for scraping, preprocessing, LLM client, and storage to ensure testability and extensibility.
2.  **OpenAI-Compatible Abstraction**: Uses the standard OpenAI SDK, allowing easy swapping of providers (OpenAI, Groq, Ollama) via environment variables.
3.  **Token-Aware Chunking**: Uses `tiktoken` to split long reviews into manageable overlapping chunks to stay within model context windows and preserve context.
4.  **Exponential Backoff**: Robust API call logic that handles rate limits (429) and server errors (5xx) with automatic retries.
5.  **Robust Scraper**: Implements User-Agent rotation and randomized delays to minimize bot detection.

## Scraping Ethics & Robots.txt

This project is built with ethical data collection in mind:

1.  **Robots.txt Compliance**: We acknowledge that Flipkart's `robots.txt` prohibits the crawling of specific review pagination and details pages. This application is designed for **single-page educational analysis** and should not be used for high-frequency or large-scale scraping.
2.  **Request Throttling**: The scraper includes a configurable `REQUEST_DELAY_SECONDS` (default: 2s) to ensure we do not overwhelm the host servers.
3.  **User-Agent Rotation**: Random User-Agents are used to simulate diverse browser environments and avoid being flagged as a malicious bot.
4.  **Limited Scope**: The tool focuses only on public customer reviews and does not attempt to access any private or protected data.

## Limitations

- **Bot Detection**: Retail sites like Flipkart aggressively block automated scrapers. ScraperAPI proxy helps, but CSS selectors may need updates if site layout changes.
- **Review Content**: Currently focuses on text-based reviews. media/images and Q&A sections are excluded.
- **API Costs**: Each review analyzed incurs token costs from your LLM provider.
