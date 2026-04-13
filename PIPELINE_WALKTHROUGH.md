# Quick Pipeline Overview

## The Flow (30 seconds to understand)

```
Input URL 
  ↓ [Validate URL]
Config (.env) 
  ↓ [Validate API keys]
Web Scraper (ScraperAPI + BeautifulSoup)
  ↓ [Extract: author, rating, date, title, body, verified]
Text Preprocessor (Clean + Chunk with tokens)
  ↓ [Remove HTML, normalize, count tokens, split if needed]
LLM Client (Groq/OpenAI)
  ↓ [Send chunks, get sentiment + summary]
Storage (CSV + JSON)
  ↓ [Save with retry logic]
Output Files
```

---

## Key Components (What Each Does)

| Component | What | Why |
|-----------|------|-----|
| **main.py** | Orchestrates pipeline | Coordinates all steps |
| **config.py** | Loads .env, validates | Fails fast if missing keys |
| **scraper.py** | Fetches + parses reviews | 3x retry with backoff |
| **preprocessor.py** | Cleans text, chunks | Handles long reviews |
| **llm_client.py** | Sends to LLM, parses | Exponential backoff retry |
| **storage.py** | Saves CSV + JSON | Retry logic for file locks |

---

## How to Run (Copy-Paste)

```bash
python main.py --url "https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ" --max-reviews 20 --log-level INFO
```

**Expected output** (~2 minutes):
```
✓ Successfully scraped 20 reviews          [30-60s]
✓ LLM client ready
Processing review 1/20, 2/20, ... 20/20    [20-40s]
✓ Results saved successfully
  - CSV: output\flipkart_reviews.csv
  - JSON: output\flipkart_reviews.json
```

---

## Error Handling (Why It's Robust)

| Layer | Handles |
|-------|---------|
| Input | Invalid URL, wrong log-level |
| Config | Missing API keys, invalid numbers |
| Network | Timeouts, connection errors (3x retry) |
| API | Rate limits 429, server errors 5xx (exponential backoff) |
| File I/O | Permission denied (3x retry with waits) |
| Graceful | No LLM key? Skip analysis, still saves scraped data |

---

## Video Script (5 minutes)

**[0:00-0:30]** Run command, show validation
```
$ python main.py --url "..." --max-reviews 20
✓ Configuration loaded
✓ Argument validation passed
```

**[0:30-2:00]** Watch scraping (30-60s)
```
INFO: Starting scraping process...
DEBUG: Found 24 review containers
✓ Successfully scraped 20 reviews
```

**[2:00-4:00]** Watch LLM analysis (20-40s)
```
INFO: Processing review 1/20
INFO: Processing review 2/20
... (each: ~1-2s)
✓ All reviews processed
```

**[4:00-4:30]** Show files saved
```
✓ Results saved successfully
  - output\flipkart_reviews.csv (20 rows)
  - output\flipkart_reviews.json (20 objects)
```

**[4:30-5:00]** Open and show CSV/JSON
```
# Show columns: author, date, rating, sentiment, summary
# Show JSON structure with pretty formatting
```

---

## What You'll See in Output

**CSV**: 20 rows × 9 columns
- author, date, rating, verified, title, body, sentiment, summary, url

**JSON**: Array of 20 objects
```json
{
  "author": "John",
  "rating": 4.5,
  "date": "2026-04-13",
  "sentiment": "Positive",
  "summary": "User satisfied with product."
}
```

**Log**: Timestamps + detailed progress
- When things started/ended
- Retry attempts (if any)
- Parsing details (DEBUG level)

---

## Key Points for Video Narration

1. **Setup**: Define problem - need to extract reviews + analyze sentiment
2. **Architecture**: 5 modules working together (pipeline)
3. **Web Scraping**: Uses proxy API to avoid blocking, retries 3x
4. **Preprocessing**: Cleans HTML, chunks long text (token-aware)
5. **LLM**: Sends to Groq/OpenAI, handles rate limits with backoff
6. **Storage**: Saves both formats, retries if locked
7. **Result**: Structured data with sentiment analysis

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "SCRAPER_API_KEY is missing" | Add to .env file |
| Ratings showing NULL | Normal - CSS selectors don't match all HTML structures |
| LLM analysis skipped | OPENAI_API_KEY not set (OK, shows graceful degradation) |
| "File locked" | Close CSV if open in Excel, retry automatic |
| Script freezes | Check .env file, ensure internet connection |

---

## Timing for Video

| Phase | Duration |
|-------|----------|
| Validation | Instant |
| Scraping 20 reviews | 30-60s |
| LLM analysis | 20-40s |
| Storage | 1-2s |
| **Total** | **~1-2 min** |

**Pause between phases** in video for clarity.

---

## Recording Checklist

- [ ] Terminal font large (150% zoom)
- [ ] High contrast theme (easy to read)
- [ ] Run once to test, then record
- [ ] Pause 2 seconds between phases
- [ ] Show validation → scraping → LLM → output
- [ ] Narrate clearly, not too fast
- [ ] Under 5 minutes total
- [ ] Show both .csv and .json files at end


---

## System Overview

**Purpose**: Scrape product reviews from Flipkart, preprocess them, analyze sentiment using an LLM, and store results.

**Key Technologies**:
- **Web Scraper**: BeautifulSoup + ScraperAPI
- **LLM Integration**: OpenAI SDK (compatible with Groq)
- **Data Processing**: Pandas, tiktoken
- **Storage**: CSV + JSON
- **Error Handling**: Exponential backoff, retry logic, input validation

**Data Pipeline**:
```
[User Input] → [Config Loading] → [Web Scraping] → [Preprocessing] → [LLM Analysis] → [Storage] → [Output Files]
```

---

## Architecture

### 1. **main.py** - Orchestrator
**Role**: Controls the entire workflow

**Responsibilities**:
- Parse and validate CLI arguments
- Load configuration
- Coordinate all modules
- Handle errors gracefully
- Provide user feedback

**Key Functions**:
- `validate_args()` - Validates URL, log-level, max-reviews
- `setup_logging()` - Configures logging to console and file
- `main()` - Orchestrates the full pipeline

**Inputs**: CLI arguments (--url, --max-reviews, --output-dir, --log-level)  
**Outputs**: Exit codes (0=success, 1=error), logged messages

---

### 2. **config.py** - Configuration Manager
**Role**: Loads and validates environment configuration

**Responsibilities**:
- Reads .env file
- Validates required API keys
- Parses numeric configurations
- Provides sensible defaults

**Key Functions**:
- `load_config()` - Loads all env variables and validates them
- `ConfigError` - Custom exception for config issues

**Environment Variables**:
```
SCRAPER_API_KEY       (Required) - ScraperAPI key for web scraping
OPENAI_API_KEY        (Optional) - API key for LLM (Groq/OpenAI)
OPENAI_BASE_URL       (Default: https://api.openai.com/v1)
OPENAI_MODEL          (Default: gpt-4o-mini)
MAX_TOKENS_PER_CHUNK  (Default: 1000)
REQUEST_DELAY_SECONDS (Default: 2.0)
MAX_RETRIES           (Default: 3)
```

**Validation Logic**:
- Fails fast if SCRAPER_API_KEY missing
- Warns if OPENAI_API_KEY missing (graceful degradation)
- Validates numeric ranges (no negative numbers)
- Parses types correctly (int/float)

---

### 3. **src/scraper.py** - Web Scraper
**Role**: Fetches reviews from Flipkart

**Key Classes**:
- `Review` - Data class representing a single review
- `FlipkartScraper` - Scrapes and parses reviews

**Data Model (Review)**:
```python
@dataclass
class Review:
    author: str              # Reviewer's name
    rating: Optional[float]  # Star rating (0-5)
    date: str               # Review date (YYYY-MM-DD)
    title: str              # Review headline
    body: str               # Review text
    verified: bool          # Verified purchase flag
    url: str                # Product page URL
    summary: str = ""       # LLM-generated summary (added later)
    sentiment: str = ""     # LLM-generated sentiment (added later)
```

**Key Methods**:

#### _fetch_page(url, render=False)
**Purpose**: Fetch page HTML using ScraperAPI

**Process**:
1. Check if API key exists
2. Build ScraperAPI request with params
3. Retry logic (3 attempts with exponential backoff)
4. Handle specific error types:
   - **Timeout** (90s) → Retry with 5s wait
   - **Connection Error** → Retry with 5s wait
   - **Rate Limited (429)** → Wait 10s before retry
   - **Server Error (5xx)** → Retry with 5s wait
   - **HTTP 4xx** → Fail immediately (client error)

**Outputs**: BeautifulSoup object with parsed HTML

**Error Handling**:
- Specific exception types caught separately
- Debug logging for each attempt
- Max 3 retries per page

#### _parse_date(date_str)
**Purpose**: Convert Flipkart relative dates to YYYY-MM-DD format

**Supports**:
- Relative: "5 days ago", "2 months ago", "1 year ago"
- Numeric: "110" (treated as days ago)
- Absolute: "Oct, 2023", "15 Oct 2023", "October 2023"

**Logic**:
1. Check for "ago" pattern → calculate date offset
2. Check for bare number → treat as days offset
3. Try multiple date formats
4. Return original if unparseable

#### _parse_reviews(soup, page_url)
**Purpose**: Extract review data from HTML

**Multi-Strategy Rating Extraction**:
1. **Strategy 1**: Look for star symbols (★⭐) with numbers
2. **Strategy 2**: Search for "rating:" labels
3. **Strategy 3**: Look for "X out of 5" format
4. **Strategy 4**: Search child elements for isolated digits (1-5 range)
5. Falls back to NULL if none work

**Other Extractions**:
- **Author**: From author name element, splits on comma
- **Date**: From date element, handles "·" separators
- **Title/Body**: From review text containers
- **Verified**: Checks for "Verified" or "Verified Purchase" text

**Logging**:
```
DEBUG: Found 24 review containers
DEBUG: Review 0: Found rating 4.5 via star symbol
DEBUG: Review 1: No rating found (will be NULL)
DEBUG: Parsed 24 reviews from 24 containers
```

#### scrape(url, max_pages=5, max_reviews=20)
**Purpose**: Main scraping method

**Logic**:
1. Normalize URL (convert product → product-reviews)
2. Loop through pages (up to max_pages)
3. Fetch each page
4. Parse reviews
5. Stop when max_reviews reached
6. Return List[Review]

**Robustness**:
- Retries page fetch on failure
- Continues to next page if parse fails
- Skips individual reviews with errors
- Logs detailed progress

---

### 4. **src/preprocessor.py** - Text Preprocessing
**Role**: Cleans and chunks reviews for LLM processing

**Key Methods**:

#### clean(text)
**Purpose**: Clean noisy review text

**Operations**:
1. HTML unescape - Convert `&nbsp;` → space
2. Strip HTML tags - Remove `<br>`, `<span>` etc.
3. Normalize Unicode (NFC) - Fix encoding issues
4. Remove control characters - Keep only printable
5. Collapse whitespace - Multiple spaces → single space

**Example**:
```
Input:  "Great&nbsp;product! &lt;p&gt;Works well&lt;/p&gt;"
Output: "Great product! Works well"
```

#### count_tokens(text)
**Purpose**: Count tokens for context window management

**Uses tiktoken**:
- cl100k_base encoding (GPT-4 compatible)
- Falls back to word count if tiktoken unavailable

#### chunk(text) → List[str]
**Purpose**: Split long reviews into overlapping chunks

**Parameters**:
- max_tokens: 1000 (configurable)
- overlap_tokens: 50

**Example**:
```
Original: 2400 tokens
↓
Chunk 1: tokens 0-1000
Chunk 2: tokens 950-1950 (50 token overlap)
Chunk 3: tokens 1900-2400

Overlap preserves context between chunks
```

#### process(text) → List[str]
**Purpose**: Clean and chunk in one call

**Pipeline**:
1. Clean text
2. Count tokens
3. If ≤ max_tokens: return [text]
4. Else: chunk into overlapping segments

---

### 5. **src/llm_client.py** - LLM Integration
**Role**: Send reviews to LLM for sentiment analysis

**Key Methods**:

#### __init__(api_key, base_url, model)
**Purpose**: Initialize OpenAI/Groq client

**System Prompt**:
```
"You are a professional product review analyst. Analyze the 
following review and respond ONLY with a valid JSON object. 
The JSON must have exactly two keys: 'sentiment' and 'summary'. 
'sentiment' should be one of: 'Positive', 'Negative', or 'Neutral'. 
'summary' should be a concise 1-2 sentence summary of the 
review content."
```

#### _call_api(text)
**Purpose**: Make API call with exponential backoff

**Retry Logic**:
- Max retries: 3 (configurable)
- Initial backoff: 2s
- Backoff multiplier: 2x each retry
- Total time: 2 + 4 + 8 = 14s max

**Catches**:
- **RateLimitError (429)** → Retry with backoff
- **APIConnectionError** → Retry with backoff
- **APIStatusError 5xx** → Retry with backoff
- **APIStatusError 4xx** → Fail immediately

#### _parse_llm_response(content)
**Purpose**: Extract JSON from LLM response

**Handles**:
- JSON with markdown formatting: ` ```json {...}``` `
- Raw JSON: `{...}`
- Fallback: Returns "Unknown" sentiment + first 200 chars

#### analyze(chunks)
**Purpose**: Analyze one or multiple chunks

**For single chunk**:
1. Call API
2. Parse response
3. Return sentiment + summary

**For multiple chunks**:
1. Analyze each chunk
2. Collect all summaries
3. Make final API call with combined summaries
4. Return combined sentiment + summary

---

### 6. **src/storage.py** - Data Storage
**Role**: Save results to CSV and JSON

**Key Methods**:

#### convert_to_df(reviews)
**Purpose**: Convert Review objects to Pandas DataFrame

**Column Order**:
```
author, date, rating, verified, title, body, sentiment, summary, url
```

**Handling**:
- Converts Review dataclass to dict
- Reorders columns (only includes existing ones)
- Handles missing columns gracefully

#### save_csv(reviews, filename)
**Purpose**: Save to CSV with retry logic

**Format**: UTF-8-SIG (with BOM for Excel)

**Retry Logic**:
- Max retries: 3
- Wait: 1s between attempts
- Catches: PermissionError (file locked)

#### save_json(reviews, filename)
**Purpose**: Save to JSON with pretty printing

**Format**:
- UTF-8 encoding
- 2-space indentation
- ensure_ascii=False (preserves non-ASCII)

**Retry Logic**: Same as CSV

#### save_all(reviews, base_name)
**Purpose**: Save both formats

**Outputs**:
```
Dict containing:
- "csv": path/to/flipkart_reviews.csv
- "json": path/to/flipkart_reviews.json
```

---

## Step-by-Step Execution Flow

### 1. Program Start
```
$ python main.py --url "https://www.flipkart.com/..." --max-reviews 20 --log-level INFO
```

### 2. Argument Validation
**Location**: main.py

**Checks**:
- ✅ URL is valid HTTPS Flipkart URL
- ✅ max-reviews is positive (max 1000)
- ✅ log-level is DEBUG/INFO/WARNING/ERROR/CRITICAL
- ❌ Any check fails → Print error + exit(1)

**Output**:
```
INFO: Argument validation passed
```

### 3. Configuration Loading
**Location**: config.py

**Process**:
1. Load .env file
2. Check SCRAPER_API_KEY exists
3. Parse: base_url, model, max_tokens, delays
4. Return config dict

**Output**:
```
INFO: Configuration loaded successfully
```

### 4. Logging Setup
**Location**: main.py

**Creates**:
- Console logger (INFO level by default)
- File logger (output/run.log) 
- Suppresses noisy loggers (requests, urllib3)

### 5. Initialization
**Location**: main.py

**Creates instances**:
- FlipkartScraper (with API key)
- Preprocessor (with token settings)
- LLMClient (if API key valid)
- StorageManager (with output dir)

**Output**:
```
INFO: Starting scraping process...
```

### 6. SCRAPING PHASE
**Duration**: ~30-60s for 20 reviews (with 2s delay)

**Per Page**:
```
1. Fetch HTML via ScraperAPI
   └─ Retry with backoff if fails
   
2. Parse reviews
   ├─ Find review containers (CSS selectors)
   ├─ Extract: author, rating, date, title, body, verified
   ├─ Parse date (relative → YYYY-MM-DD)
   └─ Log extraction details (DEBUG level)
   
3. Return List[Review]
```

**Logging**:
```
INFO: Starting scraping process...
DEBUG: Fetching page (attempt 1/3): https://www.flipkart.com/...
DEBUG: Successfully fetched page. Response size: 84532 bytes
DEBUG: Found 24 review containers
DEBUG: Review 0: Found rating 4.5 via star symbol
DEBUG: Review 1: No rating found (will be NULL)
...
DEBUG: Parsed 24 reviews from 24 containers
INFO: ✓ Successfully scraped 20 reviews
```

**Output**: List of 20 Review objects with author, rating, date, title, body, verified

---

### 7. PREPROCESSING PHASE
**Duration**: ~1-2s for 20 reviews

**Per Review**:
```
1. Clean text
   ├─ HTML unescape
   ├─ Remove tags
   ├─ Normalize Unicode
   └─ Collapse whitespace
   
2. Count tokens using tiktoken

3. If tokens > 1000:
   ├─ Split into overlapping chunks
   └─ Each chunk ≤ 1000 tokens, with 50-token overlap
   Else:
   └─ Keep as single chunk
```

**Logging**:
```
DEBUG: Cleaned body: "Great product, works perfectly"
DEBUG: Token count: 45
DEBUG: Segmented text into 1 chunks.
```

**Output**: List of chunks (usually 1 per review)

---

### 8. LLM ANALYSIS PHASE
**Duration**: ~2-3s per review (with throttling)

**Per Review (if OPENAI_API_KEY set)**:
```
1. FOR EACH chunk:
   ├─ Build message with system prompt + review text
   ├─ Call LLM API
   │  └─ Retry with exponential backoff (2, 4, 8s)
   ├─ Parse JSON response
   │  └─ Extract sentiment + summary
   └─ Log result
   
2. IF multiple chunks:
   ├─ Combine all summaries
   ├─ Make final API call
   └─ Return combined sentiment + summary
   Else:
   └─ Return single result
```

**Example API Call**:
```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [{
    "role": "system",
    "content": "You are a professional..."
  }, {
    "role": "user", 
    "content": "Review content: \"Great product!\""
  }],
  "temperature": 0.2,
  "max_tokens": 300
}
```

**Example Response**:
```json
{
  "sentiment": "Positive",
  "summary": "User found the product to be great with no complaints."
}
```

**Logging**:
```
INFO: Processing review 1/20
DEBUG: Sending to LLM...
INFO: httpx: HTTP Request: POST https://api.groq.com/... "HTTP/1.1 200 OK"
DEBUG: LLM Response: {"sentiment": "Positive", "summary": "..."}
```

**Output**: sentiment + summary added to Review object

---

### 9. STORAGE PHASE
**Duration**: ~1-2s

**Process**:
```
1. Convert Review objects → Pandas DataFrame
   └─ Reorder columns: author, date, rating, verified, title, body, sentiment, summary, url
   
2. Save CSV
   ├─ Retry 3x if permission denied
   └─ UTF-8-SIG encoding
   
3. Save JSON
   ├─ Retry 3x if permission denied
   └─ Pretty-printed with 2-space indent
   
4. Return paths dict
```

**Logging**:
```
INFO: Saving results...
INFO: ✓ Results saved successfully
INFO:   - CSV: output\flipkart_reviews.csv
INFO:   - JSON: output\flipkart_reviews.json
```

**Output Files**:
```
output/
├─ flipkart_reviews.csv  (20 rows × 9 columns)
├─ flipkart_reviews.json (20 objects)
└─ run.log              (detailed execution log)
```

### 10. Completion
**Logging**:
```
============================================================
Pipeline Complete! Processed 20 reviews.
Output: output\flipkart_reviews.csv and output\flipkart_reviews.json
============================================================

✅ Success! Processed 20 reviews.
📁 Output files:
  - output\flipkart_reviews.csv
  - output\flipkart_reviews.json
```

---

## Component Dependencies

```
main.py
  ├─ config.py              (Configuration → Dict)
  ├─ src/scraper.py         (Raw HTML → Review objects)
  ├─ src/preprocessor.py    (Text → Chunks)
  ├─ src/llm_client.py      (Chunks → Sentiment + Summary)
  └─ src/storage.py         (Review objects → CSV + JSON)

Scraper → Config
  ├─ API Key: SCRAPER_API_KEY
  └─ Delay: REQUEST_DELAY_SECONDS

LLMClient → Config
  ├─ API Key: OPENAI_API_KEY
  ├─ Base URL: OPENAI_BASE_URL
  └─ Model: OPENAI_MODEL

External APIs:
  ├─ ScraperAPI (Web scraping)
  └─ Groq/OpenAI (LLM inference)

Libraries:
  ├─ requests (HTTP)
  ├─ BeautifulSoup (HTML parsing)
  ├─ Pandas (Data manipulation)
  ├─ tiktoken (Token counting)
  └─ openai (LLM client)
```

---

## Data Transformations

### Review Data Journey

```
Step 1: WEB SCRAPING
Input:  HTML <div class="review">...</div>
Output: Review(
          author="John",
          rating=4.5,
          date="2026-04-13",
          title="Great product!",
          body="Works perfectly...",
          verified=True,
          url="https://www.flipkart.com/...",
          summary="",
          sentiment=""
        )

Step 2: PREPROCESSING
Input:  Review.body = "Great&nbsp;product!  <b>Highly</b> recommended!! 😊😊😊"
Output: "Great product! Highly recommended!!!" → [chunk1, chunk2, ...]

Step 3: LLM ANALYSIS
Input:  chunks = ["Great product! Highly recommended!!!"]
Output: Review.sentiment = "Positive"
        Review.summary = "User is very satisfied with the product."

Step 4: STORAGE
Input:  List[Review] (20 objects)
Output: DataFrame (20 rows × 9 columns)
        ↓
        flipkart_reviews.csv
        flipkart_reviews.json
```

---

## Error Handling & Robustness

### Level 1: Input Validation
```
main.py → validate_args()
├─ URL format ✓
├─ URL domain (Flipkart only) ✓
├─ max-reviews (> 0, ≤ 1000) ✓
├─ log-level (valid Python logging level) ✓
└─ Exits with error message if any fail
```

### Level 2: Configuration Validation
```
config.py → load_config()
├─ SCRAPER_API_KEY required → Fails fast
├─ OPENAI_API_KEY optional → Warns, continues
├─ Numeric values validated (positive, in range) ✓
└─ Raises ConfigError with helpful message
```

### Level 3: Web Scraping Resilience
```
scraper.py → _fetch_page()
├─ Timeout (90s)            → Retry 3x with 5s wait
├─ Connection errors        → Retry 3x with 5s wait
├─ Rate limit (429)         → Retry 3x with 10s wait
├─ Server errors (5xx)      → Retry 3x with 5s wait
├─ Client errors (4xx)      → Fail immediately
└─ Max 3 retries, then raise with context
```

### Level 4: Parsing Robustness
```
scraper.py → _parse_reviews()
├─ Rating extraction        → Multiple fallback strategies
├─ Date parsing             → Multiple format support
├─ Missing elements         → Set to default values
├─ Malformed reviews        → Skip with error log
└─ Each review wrapped in try-catch
```

### Level 5: LLM API Resilience
```
llm_client.py → _call_api()
├─ Rate limit (429)         → Retry with exponential backoff
├─ Connection errors        → Retry with exponential backoff
├─ Server errors (5xx)      → Retry with exponential backoff
├─ Client errors (4xx)      → Fail immediately with message
└─ Max 3 retries (2s, 4s, 8s)
```

### Level 6: File I/O Resilience
```
storage.py → save_csv() / save_json()
├─ Permission denied        → Retry 3x with 1s wait
├─ File locked             → Retry 3x with 1s wait
└─ Max 3 retries, then raise
```

### Level 7: Graceful Degradation
```
main.py
├─ No reviews scraped       → Print warning, exit(0)
├─ LLM unavailable          → Skip analysis, save scraped data
├─ Partial file save        → Log partial success
└─ Trap KeyboardInterrupt   → Clean exit with message
```

---

## How to Run

### Setup
```bash
# 1. Clone/open repository
cd d:\Assigment_2

# 2. Create .env file
copy .env.example .env

# 3. Fill in API keys
notepad .env
# Add:
# SCRAPER_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here (optional)

# 4. Install dependencies
pip install -r requirements.txt
```

### Basic Run
```bash
python main.py \
  --url "https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ" \
  --max-reviews 20
```

### With Options
```bash
# Skip LLM analysis (just scrape)
# Don't set OPENAI_API_KEY in .env

# More verbose logging
python main.py --url "..." --max-reviews 10 --log-level DEBUG

# Different output directory
python main.py --url "..." --max-reviews 10 --output-dir results/

# Maximum verbosity
python main.py --url "..." --max-reviews 5 --log-level DEBUG --output-dir debug_output/
```

### Monitor Progress
```bash
# Watch logs live (PowerShell)
Get-Content -Path output/run.log -Wait -Tail 20

# Or after completion
type output/run.log

# Check CSV
notepad output/flipkart_reviews.csv

# Check JSON
notepad output/flipkart_reviews.json
```

---

## Example Outputs

### Console Output (Normal Run)
```
============================================================
Flipkart Review Analyzer Pipeline Started
Target URL: https://www.flipkart.com/hp-320-5-mp-...
Max Reviews: 20
============================================================
✓ Successfully scraped 20 reviews
✓ LLM client ready
Processing review 1/20
Processing review 2/20
...
Processing review 20/20
✓ All reviews processed
✓ Results saved successfully
  - CSV: output\flipkart_reviews.csv
  - JSON: output\flipkart_reviews.json
============================================================
Pipeline Complete! Processed 20 reviews.
Output: output\flipkart_reviews.csv and output\flipkart_reviews.json
============================================================

✅ Success! Processed 20 reviews.
📁 Output files:
  - output\flipkart_reviews.csv
  - output\flipkart_reviews.json
```

### CSV Structure
```
author,date,rating,verified,title,body,sentiment,summary,url
"John Doe","2026-04-13",4.5,True,"Great product!","Works perfectly...","Positive","User is very satisfied with performance.",https://www.flipkart.com/...
"Jane Smith","2026-04-12",null,True,"Good value","Nice features but...","Neutral","Mixed experience with some limitations.",https://www.flipkart.com/...
...
```

### JSON Structure
```json
[
  {
    "author": "John Doe",
    "rating": 4.5,
    "date": "2026-04-13",
    "title": "Great product!",
    "body": "Works perfectly with all systems...",
    "verified": true,
    "url": "https://www.flipkart.com/...",
    "summary": "User is very satisfied with performance.",
    "sentiment": "Positive"
  },
  ...
]
```

### DEBUG Log Excerpt
```
2026-04-13 18:58:15,000 [INFO] main: ============================================================
2026-04-13 18:58:15,001 [INFO] main: Flipkart Review Analyzer Pipeline Started
2026-04-13 18:58:15,002 [INFO] main: Target URL: https://www.flipkart.com/hp-320-...
2026-04-13 18:58:15,003 [INFO] main: Max Reviews: 20
2026-04-13 18:58:15,004 [INFO] main: ============================================================
2026-04-13 18:58:15,100 [DEBUG] src.scraper: Fetching page (attempt 1/3): https://www.flipkart.com/...
2026-04-13 18:58:18,200 [DEBUG] src.scraper: Successfully fetched page. Response size: 84532 bytes
2026-04-13 18:58:18,300 [DEBUG] src.scraper: Found 24 review containers
2026-04-13 18:58:18,350 [DEBUG] src.scraper: Review 0: Found rating 4.5 via star symbol
2026-04-13 18:58:18,360 [DEBUG] src.scraper: Review 1: No rating found (will be NULL)
2026-04-13 18:58:18,400 [DEBUG] src.scraper: Parsed 24 reviews from 24 containers
2026-04-13 18:58:18,500 [INFO] main: ✓ Successfully scraped 20 reviews
2026-04-13 18:58:18,600 [INFO] main: Initializing LLM client...
2026-04-13 18:58:18,700 [INFO] main: ✓ LLM client ready
2026-04-13 18:58:18,800 [INFO] main: Processing review 1/20
2026-04-13 18:58:19,300 [DEBUG] src.preprocessor: Token count: 128
2026-04-13 18:58:19,400 [INFO] httpx: HTTP Request: POST https://api.groq.com/... "HTTP/1.1 200 OK"
2026-04-13 18:58:19,500 [DEBUG] src.llm_client: LLM Response: {"sentiment": "Positive", "summary": "User satisfied with performance."}
```

---

## Video Demonstration Guide

### Script Outline (5 minutes max)

**[0:00-0:30] Introduction (30s)**
```
"This is the Flipkart Review Analyzer - a Python application that 
scrapes product reviews, preprocesses text, analyzes sentiment with 
an LLM, and stores results in CSV and JSON format.

I'll walk through the entire pipeline from start to finish."
```

**[0:30-1:00] Architecture Overview (30s)**
```
Show diagram:
URL input 
  → Config loader (validates API keys)
  → Web scraper (ScraperAPI + BeautifulSoup)
  → Text preprocessor (cleaning + chunking)
  → LLM client (Groq/OpenAI)
  → Storage (CSV + JSON output)
```

**[1:00-2:00] Running the Application (60s)**
```
1. [0:00-0:10] Show the command
   $ python main.py --url "https://..." --max-reviews 20 --log-level DEBUG
   
2. [0:10-0:30] Show initial validation and config loading
   ✓ Argument validation passed
   ✓ Configuration loaded successfully
   ✓ LLM client ready
   
3. [0:30-0:50] Show live scraping progress
   INFO: Starting scraping process...
   Processing review 1/20
   Processing review 2/20
   ...
   Processing review 20/20
   
4. [0:50-1:00] Show completion
   ✅ Success! Processed 20 reviews.
   📁 Output files:
     - output\flipkart_reviews.csv
     - output\flipkart_reviews.json
```

**[2:00-3:30] Code Walkthrough (90s)**
```
1. [0:00-0:20] Main.py - Orchestration
   - Open main.py
   - Show validate_args() function
   - Show CLI argument parsing
   
2. [0:20-0:40] Config.py - Environment loading
   - Show .env file
   - Show load_config() with validation
   - Highlight ConfigError exception
   
3. [0:40-1:00] Scraper.py - Web scraping
   - Show _fetch_page() with retry logic
   - Show _parse_reviews() with multiple strategies
   - Show date parsing logic
   
4. [1:00-1:30] Preprocessor + LLM Client
   - Show clean() function
   - Show chunk() with token counting
   - Show LLM API call with exponential backoff
```

**[3:30-4:30] Output & Results (60s)**
```
1. [0:00-0:20] CSV Output
   - Open flipkart_reviews.csv in Excel
   - Show all columns: author, date, rating, verified, 
     title, body, sentiment, summary, url
   - Highlight some positive/negative/neutral reviews
   
2. [0:20-0:40] JSON Output  
   - Show flipkart_reviews.json in text editor
   - Highlight structure: array of objects
   - Show pretty printing with indentation
   
3. [0:40-0:60] Log File
   - Show output/run.log
   - Highlight key milestones:
     • "Successfully scraped X reviews"
     • "LLM Response: {...}"
     • "Results saved successfully"
```

**[4:30-5:00] Summary & Error Handling (30s)**
```
"The system includes robust error handling:
- Input validation (URL, log-level, counts)
- Config validation (API keys, numeric ranges)
- Web scraping resilience (3x retry with backoff)
- LLM API retry logic (exponential backoff)
- File I/O resilience (retries with waits)
- Graceful degradation (skips LLM if unavailable)

This ensures reliable operation even with transient failures."
```

### Recording Checklist
- [ ] Terminal clearly visible (good font size)
- [ ] Show timestamps in logs
- [ ] Highlight each phase: scraping → preprocessing → LLM → storage
- [ ] Show both success and error handling
- [ ] Display final CSV/JSON output
- [ ] Explain key decisions (retry logic, chunking, etc.)
- [ ] Keep under 5 minutes
- [ ] Audio clear and pace not too fast

### Tips for Recording
1. **Use high contrast theme** (easier to read on video)
2. **Zoom terminal to 150%** (more readable)
3. **Use clear, slow speech**
4. **Pause between sections** (1-2 seconds)
5. **Use text overlays** for technical details
6. **Show both DEBUG and INFO logs** for clarity
7. **Run once for practice, then for real**

---

## Summary

This pipeline demonstrates:
✅ **Web scraping** at scale with resilience  
✅ **Text preprocessing** for ML input  
✅ **LLM integration** with proper error handling  
✅ **Structured data export** (CSV + JSON)  
✅ **Production-quality code** with validation and logging  
✅ **Graceful degradation** when APIs unavailable  

**Total time**: ~5-10 minutes for 20 reviews (depends on API response times)
