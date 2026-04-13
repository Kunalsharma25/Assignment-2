# Quick Reference - Video Recording Guide

## Command to Run
```bash
python main.py --url "https://www.flipkart.com/hp-320-5-mp-hd-webcam-usb-connectivity/p/itm00644a314bab0?pid=ACCH28H2F69RKYQZ" --max-reviews 20 --log-level INFO
```

## Key Sections to Show (In Order)

### 1. START (0:30-1:00)
**Show**: Terminal opening, command execution  
**Say**: "Starting the pipeline with 20 reviews..."
```
$ python main.py --url "..." --max-reviews 20
```

### 2. VALIDATION (1:00-1:15)
**Show**: Initial logs  
**Expect**: 
```
INFO: Argument validation passed
INFO: Configuration loaded successfully
```

### 3. SCRAPING (1:15-2:30)
**Show**: Live scraping progress  
**Expect**:
```
INFO: Starting scraping process...
DEBUG: Found 24 review containers
INFO: ✓ Successfully scraped 20 reviews
```
**Duration**: ~30-60s (depends on ScraperAPI response time)

### 4. LLM ANALYSIS (2:30-4:00)
**Show**: Processing each review  
**Expect**:
```
INFO: Processing review 1/20
INFO: Processing review 2/20
... (each takes ~1-2s)
INFO: ✓ All reviews processed
```

### 5. STORAGE & OUTPUT (4:00-4:30)
**Show**: File saved message  
**Expect**:
```
✓ Results saved successfully
  - CSV: output\flipkart_reviews.csv
  - JSON: output\flipkart_reviews.json
  - Verdict: output\final_verdict.json
```

### 5b. FINAL VERDICT (4:30-4:45)
**Show**: The overall product analysis console output
**Expect**:
```
📊 FINAL VERDICT:
   Overall Sentiment: Positive
   Strengths: Camera quality, Value...
   Verdict: Highly recommended for...
   ✓ RECOMMENDED: YES
```

### 6. RESULTS (4:30-5:00)
**Show**: Open and display files
```
# Open CSV
notepad output\flipkart_reviews.csv

# Or open JSON
type output\flipkart_reviews.json
```

## Things to Highlight During Recording

### Architecture Discussion (2 min)
- Input validation → Config → Scraping → Preprocessing → LLM → Storage
- Each component has specific responsibility
- Modular design = easier testing

### Web Scraping (1 min)
- Uses ScraperAPI (proxy service)
- BeautifulSoup parses HTML
- Retry logic: 3 attempts with exponential backoff
- Handles timeouts, connection errors, rate limits

### Text Preprocessing (30s)
- Clean: Remove HTML, normalize Unicode
- Count tokens using tiktoken
- Chunk: If >1000 tokens, split with overlap
- Example: 2400 tokens → 3 chunks (1000, 1050, 200)

### LLM Integration (1 min)
- Uses Groq or OpenAI
- System prompt defines output format (JSON)
- Exponential backoff: 2s, 4s, 8s retries
- Parses JSON response for sentiment + summary

### Data Storage (30s)
- Pandas DataFrame conversion
- CSV: UTF-8-SIG encoding, retry logic
- JSON: Pretty-printed, 2-space indent, retry logic
- Both formats for flexibility

## Expected Error Scenarios

### Scenario 1: Missing API Key
**Show**: Validation error at startup
```
❌ Configuration Error: SCRAPER_API_KEY is missing!
```

### Scenario 2: Network Timeout
**Show**: Retry logs
```
WARNING: Timeout on attempt 1/3: [Errno 110] Connection timed out
DEBUG: Fetching page (attempt 2/3)...
```

### Scenario 3: Rate Limited
**Show**: Rate limit handling
```
WARNING: Rate limited (429). Waiting before retry...
DEBUG: Fetching page (attempt 2/3)...
```

### Scenario 4: File Permission Error
**Show**: Retry logic
```
WARNING: File locked, retrying in 1 second (attempt 1/3)
INFO: ✓ Results saved successfully
```

## File Output Examples

### CSV Columns
```
author | date | rating | verified | title | body | sentiment | summary | url
```

### JSON Structure
```json
[
  {
    "author": "Name",
    "rating": 4.5,
    "date": "2026-04-13",
    "title": "Great",
    "body": "Works well",
    "verified": true,
    "sentiment": "Positive",
    "summary": "User satisfied"
  }
]
```

## Log Level Comparison

### INFO (Default - Use for video)
```
INFO: Starting scraping process...
INFO: Processing review 1/20
INFO: ✓ Successfully scraped 20 reviews
```

### DEBUG (Too verbose for video)
```
DEBUG: Fetching page (attempt 1/3)...
DEBUG: Found 24 review containers
DEBUG: Review 0: Found rating 4.5 via star symbol
```

## Timing Guide

| Phase | Duration | Variability |
|-------|----------|-------------|
| Validation | 0.1s | Instant |
| Config Load | 0.1s | Instant |
| Scraping | 30-60s | API response time |
| Preprocessing | 1-2s | Text length |
| LLM Analysis | 20-40s | API response time |
| Storage | 1-2s | File size/disk speed |
| **Total** | **~1-2 min** | Depends on API |

## Script Template

```
[INTRO - 30s]
"This application combines web scraping, text preprocessing, and 
LLM analysis to extract insights from product reviews."

[EXECUTION - 60s]
"Watch as it scrapes reviews, cleans the text, analyzes sentiment, 
and saves results to CSV and JSON - all in about a minute."

[ARCHITECTURE - 60s]
"The system has 5 main components: 
1. Config manager validates environment
2. Web scraper fetches and parses reviews
3. Text preprocessor cleans and chunks
4. LLM client sends to API and handles retries
5. Storage manager saves both formats"

[RESULTS - 90s]
"The output includes all review metadata plus LLM-generated 
sentiment analysis and summaries for each review."

[CLOSING - 30s]
"This demonstrates production-quality Python with robust error 
handling, proper logging, and clean architecture."
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| API Key error | Check .env file has correct key |
| No reviews scraped | Check URL is correct Flipkart product page |
| Rating showing NULL | Normal - CSS selector doesn't match current HTML structure |
| LLM analysis skipped | OPENAI_API_KEY not set - that's OK, shows graceful degradation |
| Slow scraping | ScraperAPI delays - mention rate limiting is intentional |
| File permission error | If .csv still open in Excel - close it first |

## Pro Tips for Recording

1. **Run once first** to warm up and verify works
2. **Increase font size** - `Ctrl+Scroll` in terminal
3. **Use PowerShell** for better formatting
4. **Show timestamps** in log output - helps viewers follow along
5. **Pause at transitions** between phases
6. **Explain decisions** - why this tech, why this approach
7. **Show error handling** - run with invalid input to demonstrate validation
8. **Compare outputs** - show CSV and JSON side-by-side
9. **Mention complexity** - token chunking is non-trivial
10. **Emphasize robustness** - all the retry logic and error handling

## Post-Recording Checklist

- [ ] Audio is clear (no background noise)
- [ ] Text is readable (good contrast, large font)
- [ ] All 5 phases visible: validation → scraping → preprocessing → LLM → storage
- [ ] Shows both success case and demonstrates error handling
- [ ] Output files visible (CSV + JSON)
- [ ] Under 5 minutes total
- [ ] Pace is not too fast (viewers can follow)
- [ ] Explains key technical decisions
- [ ] Demonstrates all three components: scraper, LLM, storage
