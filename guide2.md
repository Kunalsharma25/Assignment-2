# AI Engineer Intern — Assignment 2: Build Guide
### LLM Interaction & Data Processing — Complete Step-by-Step Instructions

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Design](#2-architecture--design)
3. [Repository Structure](#3-repository-structure)
4. [Environment Setup](#4-environment-setup)
5. [Step 1 — Web Scraper Module](#5-step-1--web-scraper-module)
6. [Step 2 — Data Preprocessing Module](#6-step-2--data-preprocessing-module)
7. [Step 3 — LLM Integration Module](#7-step-3--llm-integration-module)
8. [Step 4 — Data Storage Module](#8-step-4--data-storage-module)
9. [Step 5 — Error Handling & Rate Limiting](#9-step-5--error-handling--rate-limiting)
10. [Step 6 — Main Application Entrypoint](#10-step-6--main-application-entrypoint)
11. [Step 7 — Configuration & Environment Variables](#11-step-7--configuration--environment-variables)
12. [Step 8 — Dependencies](#12-step-8--dependencies)
13. [Step 9 — README.md](#13-step-9--readmemd)
14. [Step 10 — Testing & Validation](#14-step-10--testing--validation)
15. [Step 11 — GitHub Repository Setup](#15-step-11--github-repository-setup)
16. [Step 12 — Demo Video Guide](#16-step-12--demo-video-guide)

---

## 1. Project Overview

This project is a Python application that:

- Accepts a product page URL (e.g., from Amazon or Best Buy) as CLI input
- Scrapes all available customer reviews along with metadata (rating, date, author)
- Preprocesses review text (cleaning, encoding fixes, token-safe chunking)
- Sends each review to an OpenAI-compatible LLM API for sentiment/summary generation
- Saves all data (original review + metadata + LLM output) to structured CSV and JSON files
- Handles network errors, API failures, and rate limits gracefully

**Chosen Product URL:** `https://www.amazon.com/dp/B08N5WRWNW` *(Amazon Echo Dot 4th Gen — a popular, review-rich product)*

> **Note:** Amazon actively blocks scrapers. The scraper must use rotating User-Agent headers and optional proxy support. For guaranteed results during evaluation, include a static HTML fixture of the reviews page for offline testing.

---

## 2. Architecture & Design

The application follows a linear pipeline with four distinct stages:

**User Input (URL) → Scraper → Preprocessor → LLM Client → Storage**

- The **Scraper** uses `requests` and `BeautifulSoup` to fetch raw review HTML
- The **Preprocessor** cleans, decodes, and chunks the text into LLM-safe segments
- The **LLM Client** calls an OpenAI-compatible API and returns a summary and sentiment
- The **Storage Module** writes the final enriched records to CSV and JSON

**Key Design Decisions:**

- **Modular structure:** Each concern (scraping, preprocessing, LLM, storage) is isolated in its own module, making each independently testable and replaceable.
- **OpenAI-compatible API:** The LLM client abstracts the API call so any compatible provider (OpenAI, Groq, Mistral, local Ollama) can be swapped in by changing environment variables alone — no code changes needed.
- **Token-aware chunking:** Use `tiktoken` to split long reviews so they never exceed the model's context window.
- **Exponential backoff:** Rate limit errors from the API must trigger automatic retries with increasing wait times (2s → 4s → 8s).
- **Environment variables only:** No secrets are ever hardcoded in source files.

---

## 3. Repository Structure

Create this exact folder layout before writing any code:

```
review-analyzer/
│
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Web scraping logic
│   ├── preprocessor.py     # Text cleaning & chunking
│   ├── llm_client.py       # OpenAI-compatible API wrapper
│   └── storage.py          # CSV/JSON output
│
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_preprocessor.py
│   └── fixtures/
│       └── sample_reviews.html   # Static HTML for offline testing
│
├── output/                 # Auto-created at runtime; stores results
│
├── main.py                 # CLI entrypoint
├── config.py               # Loads and validates env variables
├── requirements.txt
├── .env.example            # Template — never commit actual .env
├── .gitignore
└── README.md
```

Create the `src/` and `tests/` packages by adding an empty `__init__.py` file inside each. Create the `tests/fixtures/` directory manually. The `output/` directory should be created automatically at runtime by the storage module.

---

## 4. Environment Setup

### 4.1 Prerequisites

Ensure the following are installed before starting:

- Python 3.10 or higher
- pip (Python package installer)
- A terminal / command prompt
- An OpenAI API key (or a compatible provider key such as Groq or Mistral)
- Git

### 4.2 Create the Project Directory

Create a new directory named `review-analyzer` and navigate into it.

### 4.3 Create and Activate a Virtual Environment

Create a virtual environment named `venv` inside the project directory. Activate it using the appropriate command for your operating system (macOS/Linux vs. Windows) before installing any packages.

### 4.4 Create the .env File

Copy `.env.example` to a new file named `.env`. Edit `.env` and fill in the following values:

- `OPENAI_API_KEY` — your API key (required)
- `OPENAI_BASE_URL` — the API base URL (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` — the model name to use (default: `gpt-3.5-turbo`)
- `MAX_TOKENS_PER_CHUNK` — maximum tokens per review chunk sent to the LLM (default: `1000`)
- `REQUEST_DELAY_SECONDS` — wait time between scraper page requests (default: `2`)
- `MAX_RETRIES` — number of retry attempts on API failure (default: `3`)

> **Critical:** The `.env` file must be listed in `.gitignore`. Never commit it to version control.

### 4.5 Create .gitignore

Create a `.gitignore` file at the project root that excludes at minimum: the virtual environment folder (`venv/`), the `.env` file, Python cache directories (`__pycache__/`, `*.pyc`), the `output/` directory, and OS-specific files like `.DS_Store`.

### 4.6 Install Dependencies

After creating `requirements.txt` (see Step 8), run `pip install -r requirements.txt` with the virtual environment active.

---

## 5. Step 1 — Web Scraper Module

**File:** `src/scraper.py`

### 5.1 Purpose

This module fetches the Amazon product review page and parses it into structured Python objects.

### 5.2 Data Model

Define a `Review` dataclass with the following fields: `author` (str), `rating` (float or None), `date` (str), `title` (str), `body` (str), `verified` (bool), `url` (str), `summary` (str, default empty), and `sentiment` (str, default empty). The `summary` and `sentiment` fields are left empty here and filled in later by the LLM client.

### 5.3 Scraper Class

Implement an `AmazonScraper` class that:

- Accepts a `delay` (seconds between page requests) and an optional `proxies` dict in its constructor
- Maintains a `requests.Session` for connection reuse
- Has a pool of at least 3 realistic browser User-Agent strings and selects one randomly per request to reduce bot detection

### 5.4 ASIN Extraction

Implement a method that extracts the 10-character ASIN from an Amazon product URL using a regular expression. It should support both `/dp/ASIN` and `/gp/product/ASIN` URL patterns. Raise a descriptive `ValueError` if the ASIN cannot be found.

### 5.5 Page Fetching

Implement a private method that takes a URL, sends an HTTP GET request with randomized headers and a 15-second timeout, and returns a `BeautifulSoup` object of the parsed HTML. It must catch and re-raise `HTTPError`, `ConnectionError`, and `Timeout` exceptions with descriptive log messages.

### 5.6 Review Parsing

Implement a private method that takes a `BeautifulSoup` object and the current URL, locates all review containers using the CSS selector `div[data-hook='review']`, and extracts the following from each:

- **Author:** the element with class `a-profile-name`
- **Rating:** the `i[data-hook='review-star-rating']` span text, parsed to a float
- **Date:** the `span[data-hook='review-date']` text
- **Title:** the `a[data-hook='review-title']` span text
- **Body:** the `span[data-hook='review-body']` span text, joined with spaces
- **Verified:** presence of `span[data-hook='avp-badge']`

Skip any review whose body is empty. Wrap each review's extraction in a try/except block so a single malformed review does not abort the whole page.

### 5.7 Pagination

Implement a private method that looks for a non-disabled "Next page" link (`li.a-last:not(.a-disabled) a`) and returns its full absolute URL, or `None` if no next page exists.

### 5.8 Main Scrape Method

Implement a public `scrape(url, max_pages)` method that:

1. Extracts the ASIN and constructs the reviews URL with `pageNumber=1&sortBy=recent`
2. Loops through pages up to `max_pages`, calling the fetch and parse methods on each
3. Waits `delay + random jitter (0.5–1.5s)` between page requests
4. Logs the page number, URL, and review count for each page
5. Returns the full list of `Review` objects collected across all pages

---

## 6. Step 2 — Data Preprocessing Module

**File:** `src/preprocessor.py`

### 6.1 Purpose

This module cleans raw review text and splits it into token-safe chunks for LLM input.

### 6.2 Preprocessor Class

Implement a `Preprocessor` class that accepts `max_tokens` (int, default 1000) and `overlap_tokens` (int, default 50) in its constructor. On initialization, load the `cl100k_base` tiktoken encoding. If tiktoken is unavailable, fall back gracefully to a word-count approximation (1 token ≈ 4 characters / ~3 words).

### 6.3 Text Cleaning Method

Implement a `clean(text)` method that applies the following steps in order:

1. Unescape HTML entities using `html.unescape()` (converts `&amp;` → `&`, etc.)
2. Strip residual HTML tags using a regex that removes anything matching `<[^>]+>`
3. Normalize Unicode to NFC form using `unicodedata.normalize` to fix mojibake artifacts
4. Remove non-printable control characters (keep tabs, newlines, and standard printable Unicode)
5. Collapse multiple consecutive whitespace characters into a single space
6. Strip leading and trailing whitespace

Return an empty string if the input is empty or whitespace-only.

### 6.4 Token Counting Method

Implement a `count_tokens(text)` method that returns the number of tokens in a string using the loaded tiktoken encoding, or the character-length approximation as a fallback.

### 6.5 Chunking Method

Implement a `chunk(text)` method that:

- Returns `[text]` unchanged if `count_tokens(text) <= max_tokens`
- Otherwise splits into overlapping chunks at token boundaries (preferred) or word boundaries (fallback)
- Each chunk overlaps the previous by `overlap_tokens` to preserve context across boundaries
- Logs the number of chunks produced

### 6.6 Main Process Method

Implement a public `process(text)` method that calls `clean()` then `chunk()` and returns the list of processed chunks. Return an empty list and log a warning if the cleaned text is empty.

---

## 7. Step 3 — LLM Integration Module

**File:** `src/llm_client.py`

### 7.1 Purpose

This module sends cleaned review text to an OpenAI-compatible API and parses the structured response.

### 7.2 Prompt Design

Design two prompts:

- **System prompt:** Instructs the model to act as a product review analyst and respond **only** with a valid JSON object containing exactly two keys: `"sentiment"` (one of `"Positive"`, `"Negative"`, or `"Neutral"`) and `"summary"` (a concise 1–2 sentence summary). Make clear that no text outside the JSON object is acceptable.
- **User prompt template:** Presents the review text wrapped in triple quotes and asks for a JSON-only response.

### 7.3 LLM Client Class

Implement an `LLMClient` class that accepts `api_key`, `base_url`, `model`, `max_retries` (default 3), and `initial_backoff` (default 2.0 seconds) in its constructor. Initialize an `openai.OpenAI` client with the provided key and base URL.

### 7.4 API Call with Retry Logic

Implement a private `_call_api(review_text)` method that:

1. Sends a `chat.completions.create` request with `temperature=0.2` and `max_tokens=300`
2. On `RateLimitError` (HTTP 429): log a warning, wait `backoff` seconds, double the backoff, and retry
3. On `APIStatusError` with status ≥ 500: apply the same backoff-and-retry strategy
4. On `APIConnectionError`: apply the same backoff-and-retry strategy
5. On `APIStatusError` with status < 500 (e.g., 400, 401): log the error and raise immediately — do not retry
6. After exhausting all retries: raise a `RuntimeError` with a descriptive message

### 7.5 Response Parsing

Implement a private `_parse_llm_response(content)` method that:

- Strips markdown code fences if present
- Parses the remaining text as JSON
- Returns a dict with `"sentiment"` and `"summary"` keys
- On `JSONDecodeError`: log a warning and return `{"sentiment": "Unknown", "summary": <truncated raw content>}`

### 7.6 Multi-Chunk Analysis

Implement a public `analyze(chunks)` method that:

- Returns a default unknown result if `chunks` is empty
- Calls `_call_api` once if there is only one chunk
- For multiple chunks: calls `_call_api` on each chunk individually, collects the per-chunk summaries, joins them, and makes one final `_call_api` call on the combined summaries to produce a single coherent result

---

## 8. Step 4 — Data Storage Module

**File:** `src/storage.py`

### 8.1 Purpose

This module converts the list of enriched `Review` objects into persistent output files.

### 8.2 StorageManager Class

Implement a `StorageManager` class that accepts an `output_dir` string (default `"output"`) and creates that directory on initialization, including any missing parent directories, without raising an error if it already exists.

### 8.3 DataFrame Conversion

Implement a method that converts a list of `Review` objects to a Pandas DataFrame using `dataclasses.asdict()`. Reorder the columns as: `author`, `date`, `rating`, `verified`, `title`, `body`, `sentiment`, `summary`, `url`.

### 8.4 CSV Output

Implement a `save_csv(reviews, filename)` method that saves the DataFrame to a CSV file using `utf-8-sig` encoding for Excel compatibility. Log the number of records saved and return the output path.

### 8.5 JSON Output

Implement a `save_json(reviews, filename)` method that serializes the list of review dicts to a JSON file with `ensure_ascii=False` and `indent=2` for human readability. Log the number of records saved and return the output path.

### 8.6 Save All

Implement a `save_all(reviews, base_name)` method that calls both `save_csv` and `save_json`, naming the files `{base_name}.csv` and `{base_name}.json`. Return a dict with keys `"csv"` and `"json"` mapping to the respective output paths as strings.

---

## 9. Step 5 — Error Handling & Rate Limiting

Error handling must be distributed across all modules according to the following rules:

### 9.1 Network Errors (Scraper)

- `ConnectionError` and `Timeout` from `requests` must be caught, logged with the URL, and re-raised to the caller.
- `HTTPError` must be caught, logged with the status code, and re-raised.
- In `main.py`, wrap the entire scrape call in a try/except that prints a clear error message and exits with a non-zero code rather than printing a raw traceback.

### 9.2 API Rate Limits (LLM Client)

- HTTP 429 `RateLimitError` and server-side 5xx errors trigger exponential backoff: wait 2s after the first failure, 4s after the second, 8s after the third.
- After all retries are exhausted, the error is raised and caught in `main.py`. That specific review is stored with `sentiment="Error"` and a truncated error message as the summary, so the output file remains complete.

### 9.3 Per-Review Parse Errors (Scraper)

- Each review block's extraction is wrapped in try/except. A failed review logs a warning and is skipped; scraping continues with the remaining reviews on the page.

### 9.4 LLM Response Parse Errors

- If the LLM returns malformed JSON, log a warning including the raw response (truncated to 300 characters) and return a fallback dict rather than crashing.

### 9.5 Encoding Issues (Preprocessor)

- Unicode normalization (NFC) and HTML unescaping handle the vast majority of encoding artifacts automatically. The control-character regex acts as a final safety net for any remaining non-printable bytes.

---

## 10. Step 6 — Main Application Entrypoint

**File:** `main.py`

### 10.1 Purpose

`main.py` is the CLI entrypoint that wires all modules together and runs the full pipeline.

### 10.2 Argument Parsing

Use `argparse` to accept the following CLI arguments:

- `--url` (required): the Amazon product page URL
- `--max-pages` (optional, default 3): maximum number of review pages to scrape
- `--output-dir` (optional, default `"output"`): directory for output files
- `--log-level` (optional, default `"INFO"`, choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`): logging verbosity

### 10.3 Logging Setup

Configure logging with two handlers: a `StreamHandler` writing to stdout and a `FileHandler` writing to `output/run.log`. Use the format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.

### 10.4 Pipeline Orchestration

Implement a `main()` function that runs the following steps in order:

1. Parse CLI arguments and set up logging
2. Load configuration from environment variables via `config.py`
3. Instantiate `AmazonScraper` and call `scrape(url, max_pages)` — exit cleanly on failure
4. Exit with a warning message if no reviews were returned
5. Instantiate `Preprocessor` and `LLMClient`
6. Loop through every review: call `preprocessor.process(review.body)`, then `llm.analyze(chunks)`, and assign the returned `sentiment` and `summary` back to the review object. Catch any exception per review, log it, and store `sentiment="Error"` rather than crashing the whole run.
7. Instantiate `StorageManager` and call `save_all(reviews)`
8. Print a final summary to stdout showing: total reviews processed, count of each sentiment label, and the paths to the CSV and JSON output files

---

## 11. Step 7 — Configuration & Environment Variables

**File:** `config.py`

### 11.1 Purpose

Centralizes all configuration loading and validates that required values are present before the application starts.

### 11.2 Implementation

Implement a `load_config()` function that:

1. Calls `load_dotenv()` from the `python-dotenv` library to load `.env` into environment variables
2. Reads `OPENAI_API_KEY` and raises `EnvironmentError` with a clear message if it is missing or empty
3. Reads all other variables with sensible defaults (base URL, model name, token limit, delay, retries)
4. Returns all values as a single dictionary

**File:** `.env.example`

Create this file as a template with all required variable names listed, each set to a placeholder value. Add a comment at the top instructing the developer to copy it to `.env` and fill in real values, and to never commit `.env` itself.

---

## 12. Step 8 — Dependencies

**File:** `requirements.txt`

List the following packages with pinned versions:

- `requests` — HTTP client for web scraping
- `beautifulsoup4` — HTML parsing
- `lxml` — fast HTML/XML parser backend for BeautifulSoup
- `openai` — official OpenAI Python SDK (v1.x)
- `tiktoken` — token counting for OpenAI models
- `pandas` — DataFrame creation and CSV export
- `numpy` — numerical support (pandas dependency)
- `python-dotenv` — loads `.env` files into environment variables

Pin each to a specific version to ensure reproducibility. After creating the file, install all dependencies with `pip install -r requirements.txt` while the virtual environment is active.

---

## 13. Step 9 — README.md

**File:** `README.md`

The README must contain the following sections in order:

### 13.1 Project Title and Description

A one-paragraph description of what the application does.

### 13.2 Chosen Product URL

State the exact URL used for testing and briefly explain why it was chosen (e.g., high review volume, diverse sentiments, varied review lengths).

### 13.3 Setup Instructions

Step-by-step instructions for a new user to clone the repository, create a virtual environment, install dependencies, copy `.env.example` to `.env`, and fill in their API key.

### 13.4 How to Run

The exact command to run the application, with all CLI flags documented in a table showing flag name, default value, and description.

### 13.5 Output Files

A description of what files are produced in the `output/` directory after a successful run, including the column names present in the CSV.

### 13.6 Design Choices

A brief explanation of the key architectural decisions: modular structure, OpenAI-compatible abstraction, token-aware chunking, exponential backoff, and environment-variable-only secrets management.

### 13.7 Limitations

Honest acknowledgment of known limitations: Amazon bot detection risk, scope limited to review body text only (no Q&A or images), and API credit cost per review.

---

## 14. Step 10 — Testing & Validation

### 14.1 Create a Test Fixture

Navigate to the Amazon reviews page for your chosen product in a browser. Use **Save As → Webpage, HTML only** to save the HTML file locally. Place it at `tests/fixtures/sample_reviews.html`. This enables offline testing without making live HTTP requests.

### 14.2 Write Tests for the Preprocessor

Create `tests/test_preprocessor.py` and write tests that verify:

- `clean()` removes HTML tags from input text
- `clean()` unescapes HTML entities (e.g., `&amp;` becomes `&`)
- `clean()` returns an empty string for blank or whitespace-only input
- `chunk()` returns a single-element list when the text fits within `max_tokens`
- `chunk()` returns multiple elements when the text exceeds `max_tokens`
- `process()` returns an empty list for blank input

### 14.3 Write Tests for the Scraper

Create `tests/test_scraper.py` and write tests that verify:

- `_extract_asin()` correctly extracts the ASIN from a valid Amazon URL
- `_extract_asin()` raises `ValueError` for a URL that has no recognizable ASIN
- `_parse_reviews()` returns a list of `Review` objects when given the saved HTML fixture — mark this test with `pytest.mark.skipif` if the fixture file does not exist, so the test suite still passes without it

### 14.4 Run the Tests

Execute `pytest tests/ -v` from the project root. All tests should pass. Tests marked with `skipif` may be skipped if the fixture is absent — this is expected behavior.

---

## 15. Step 11 — GitHub Repository Setup

### 15.1 Initialize the Local Repository

Run `git init` in the project root, then stage all files and make an initial commit with a descriptive message such as `"Initial commit: review analyzer application"`.

### 15.2 Create a Remote Repository on GitHub

Go to github.com, click **New repository**, name it `review-analyzer`, set visibility to **Public**, and do not initialize it with a README, `.gitignore`, or license (those already exist locally).

### 15.3 Push to GitHub

Add the remote origin using the URL provided by GitHub, rename the default branch to `main`, and push.

### 15.4 Verify .gitignore is Working

Run `git status` after the initial push and confirm that `.env`, the `venv/` directory, and `output/` do not appear as tracked or untracked files.

### 15.5 Final Repository Checklist

Before submitting, verify all of the following files are visible on GitHub:

- `src/__init__.py`
- `src/scraper.py`
- `src/preprocessor.py`
- `src/llm_client.py`
- `src/storage.py`
- `main.py`
- `config.py`
- `requirements.txt`
- `README.md`
- `.env.example`
- `.gitignore`
- `tests/__init__.py`
- `tests/test_scraper.py`
- `tests/test_preprocessor.py`

---

## 16. Step 12 — Demo Video Guide

The video must be **maximum 5 minutes**. Follow this minute-by-minute structure:

### 0:00 – 0:30 | Introduction

State your name and the assignment title. Briefly show the GitHub repository homepage. Read out the chosen product URL and explain why it was selected.

### 0:30 – 1:30 | Code Walkthrough

Open each of the four source files in sequence and explain the key logic in plain language:

- `src/scraper.py` — explain User-Agent rotation and how pagination is handled
- `src/preprocessor.py` — explain the cleaning steps and token-aware chunking
- `src/llm_client.py` — explain the structured prompt design and the retry/backoff logic

### 1:30 – 3:00 | Live Demo

Open a terminal. Show the `.env` file is present and configured (blur or hide the actual API key value). Run the application with `--max-pages 2` and `--log-level DEBUG` so verbose output is visible. Narrate what is happening as each log line appears: page fetching, review parsing, preprocessing, LLM API calls. If a rate limit retry occurs, call attention to it; if it doesn't, explain verbally what the log output would look like.

### 3:00 – 4:00 | Output Demonstration

Open `output/reviews.csv` in Excel or a text editor. Point out the key columns: `body`, `sentiment`, and `summary`. Open `output/reviews.json` and show the same data in structured format. Briefly mention the `output/run.log` file and what it contains.

### 4:00 – 5:00 | Design Choices & Limitations

Summarize the three most important design decisions: modular architecture, LLM provider abstraction, and token chunking. Acknowledge the main limitation (Amazon bot detection) and explain the mitigations used. Close by reading out the submission form link from the assignment.

---

*End of Build Guide — Assignment 2: LLM Interaction & Data Processing*
