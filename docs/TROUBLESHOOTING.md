# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the NVIDIA Stock Predictor system.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API and Authentication](#api-and-authentication)
- [Execution Problems](#execution-problems)
- [Low Confidence Issues](#low-confidence-issues)
- [Performance Problems](#performance-problems)
- [Data Quality Issues](#data-quality-issues)
- [Advanced Debugging](#advanced-debugging)

---

## Installation Issues

### Problem: `playwright` command not found

**Symptoms:**
```
Error: Playwright browser not installed
playwright: command not found
```

**Solution:**
```bash
# Install Playwright browsers
playwright install chromium

# If playwright command not found, try:
python -m playwright install chromium

# Or with full path:
~/.local/bin/playwright install chromium
```

**Verification:**
```bash
playwright --version
# Should output: Version 1.40.0 or higher
```

---

### Problem: `uv` installation fails

**Symptoms:**
```
uv: command not found
```

**Solution:**

**Option 1: Install with pip**
```bash
pip install uv
```

**Option 2: Use pip directly**
```bash
pip install -e .
```

**Option 3: Install from requirements**
```bash
pip install langgraph langchain-core google-generativeai newsapi-python playwright pydantic python-dotenv
```

---

### Problem: Python version incompatibility

**Symptoms:**
```
ERROR: This package requires Python >=3.10
```

**Solution:**
```bash
# Check your Python version
python --version

# If < 3.10, install Python 3.10+
# On Ubuntu/Debian:
sudo apt update
sudo apt install python3.10

# On macOS with Homebrew:
brew install python@3.10

# Create virtual environment with correct version:
python3.10 -m venv .venv
source .venv/bin/activate
```

---

## API and Authentication

### Problem: Missing Gemini API Key

**Symptoms:**
```
Error: GEMINI_API_KEY_JY not found in environment
KeyError: 'GEMINI_API_KEY_JY'
```

**Solution:**

1. **Create `.env` file** in project root:
```bash
touch .env
```

2. **Add your API key**:
```env
GEMINI_API_KEY_JY=your_actual_api_key_here
```

3. **Get API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Verify `.env` is loaded**:
```python
# Test in Python:
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("GEMINI_API_KEY_JY"))  # Should print your key
```

**Common mistakes:**
- ❌ Spaces around `=`: `GEMINI_API_KEY_JY = abc123`
- ✅ No spaces: `GEMINI_API_KEY_JY=abc123`
- ❌ Quotes in value: `GEMINI_API_KEY_JY="abc123"`
- ✅ No quotes needed: `GEMINI_API_KEY_JY=abc123`

---

### Problem: Gemini API Rate Limits

**Symptoms:**
```
Error: 429 Resource Exhausted
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Solution:**

**Option 1: Wait and retry**
```bash
# Rate limits reset after a period
# Free tier: 60 requests per minute
# Wait 1 minute and try again
```

**Option 2: Reduce API calls**

Edit `config/settings.py`:
```python
MAX_CRAWL_ARTICLES = 10  # Reduce from 20
MAX_ITERATIONS = 2  # Reduce from 3
```

**Option 3: Upgrade API tier**
- Visit [Google AI Studio](https://makersuite.google.com/)
- Upgrade to paid tier for higher limits

**Option 4: Add delays**

Edit `agents/keyword_agent.py` (and other agents):
```python
import time

def generate_keywords(self):
    time.sleep(1)  # Add 1 second delay
    # ... rest of code
```

---

### Problem: News API Key Issues

**Symptoms:**
```
Error: 401 Unauthorized
newsapi.newsapi_exception.NewsAPIException: 401 - Unauthorized
```

**Solution:**

1. **Get free API key** from [NewsAPI.org](https://newsapi.org/register)

2. **Add to `.env`**:
```env
NEWS_API_KEY=your_news_api_key_here
```

3. **Check API limits**:
   - Free tier: 100 requests/day
   - Developer tier: 1000 requests/day

4. **Reduce requests** if hitting limits:
```python
# config/settings.py
NEWS_DAYS_BACK = 7  # Reduce from 30
```

---

## Execution Problems

### Problem: Workflow hangs or freezes

**Symptoms:**
- Script runs but produces no output
- Process appears stuck
- No error messages

**Diagnosis:**
```bash
# Run with verbose logging
python main.py 2>&1 | tee debug.log

# Check if process is running
ps aux | grep python

# Check network connectivity
ping newsapi.org
ping generativelanguage.googleapis.com
```

**Solutions:**

**1. Check internet connection**
```bash
# Test API connectivity
curl -I https://newsapi.org/v2/top-headlines?apiKey=test
curl -I https://generativelanguage.googleapis.com
```

**2. Increase timeouts**

Edit `agents/crawler_agent.py`:
```python
# In crawl_articles method
page.goto(url, timeout=60000)  # Increase from 30000
```

**3. Check Playwright browser**
```bash
# Reinstall browser
playwright install chromium --force
```

**4. Add debug logging**

Edit `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

### Problem: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'langgraph'
ImportError: cannot import name 'StateGraph'
```

**Solution:**

**1. Verify installation**
```bash
pip list | grep langgraph
pip list | grep langchain
```

**2. Reinstall dependencies**
```bash
pip uninstall langgraph langchain-core
pip install langgraph langchain-core
```

**3. Check Python path**
```python
import sys
print(sys.path)
# Should include your project directory
```

**4. Activate virtual environment**
```bash
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

---

### Problem: Playwright browser crashes

**Symptoms:**
```
Error: Browser closed unexpectedly
playwright._impl._api_types.Error: Browser closed
```

**Solutions:**

**1. Install system dependencies** (Linux):
```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

**2. Run in headless mode** (already default):
```python
# In crawler_agent.py, verify:
browser = playwright.chromium.launch(headless=True)
```

**3. Increase memory**:
```bash
# Check available memory
free -h

# Close other applications if low on memory
```

**4. Use alternative browser**:
```python
# In crawler_agent.py, try Firefox:
browser = playwright.firefox.launch(headless=True)
```

---

## Low Confidence Issues

### Problem: Confidence always below threshold

**Symptoms:**
- All 3 iterations complete
- Confidence remains < 60%
- Warning: "Below threshold"

**Diagnosis:**

Check the validation notes in output:
```
Validation Notes:
- Source reliability: 35%  ← Too low
- Evidence quality: 40%    ← Weak evidence
- Recency: 20%            ← Old news
```

**Solutions:**

**1. Adjust confidence threshold**

Edit `config/settings.py`:
```python
CONFIDENCE_THRESHOLD = 50  # Lower from 60
# or
CONFIDENCE_THRESHOLD = 40  # Even more lenient
```

**2. Expand news search period**
```python
NEWS_DAYS_BACK = 60  # Increase from 30
```

**3. Increase article collection**
```python
MAX_CRAWL_ARTICLES = 30  # Increase from 20
```

**4. Add more trusted sources**

Edit `config/constants.py`:
```python
TRUSTED_SOURCES = {
    'reuters': 1.0,
    'bloomberg': 1.0,
    # Add more sources:
    'seeking alpha': 0.7,
    'benzinga': 0.6,
    'thestreet': 0.6,
}
```

**5. Allow more iterations**
```python
MAX_ITERATIONS = 5  # Increase from 3
```

---

### Problem: Source reliability too low

**Symptoms:**
```
Source Reliability: 35%
Deficiency: Need more trusted sources
```

**Root causes:**
- News from low-reliability sources
- Trusted sources not covering the topic
- Keywords not targeting quality sources

**Solutions:**

**1. Improve keyword targeting**

The system should automatically improve keywords, but you can manually test:
```python
# Test keywords that target specific sources:
keywords = [
    "NVIDIA Reuters",
    "NVDA Bloomberg",
    "NVIDIA Wall Street Journal",
    "NVIDIA Financial Times earnings"
]
```

**2. Expand trusted source list**

Edit `config/constants.py`:
```python
TRUSTED_SOURCES = {
    # Existing sources...
    'barrons': 0.8,
    'forbes': 0.7,
    'business insider': 0.6,
}
```

**3. Check News API plan**

Free tier may not include premium sources:
- Upgrade to Developer plan for better source access
- Consider alternative news APIs

---

### Problem: Insufficient evidence

**Symptoms:**
```
Evidence Quality: 30%
Deficiency: Weak evidence for earnings impact
```

**Solutions:**

**1. Target specific event types**

Keywords should be more specific:
```python
# Instead of generic:
"NVIDIA news"

# Use specific:
"NVIDIA quarterly earnings Q4 2025"
"NVIDIA data center revenue growth"
"Blackwell GPU production schedule"
```

**2. Increase crawl depth**

Edit `agents/crawler_agent.py`:
```python
# Crawl more articles
articles_to_crawl = articles[:30]  # Increase from 20
```

**3. Adjust event weights**

Edit `config/constants.py`:
```python
EVENT_SETTINGS = {
    'earnings': {'weight': 4.0, 'days': (3, 7)},  # Increase weight
    'product': {'weight': 2.0, 'days': (5, 10)},
    # ...
}
```

---

## Performance Problems

### Problem: Execution takes too long

**Symptoms:**
- Single iteration > 5 minutes
- Total execution > 15 minutes
- Timeout errors

**Diagnosis:**
```bash
# Check which step is slow
# Look for timing in logs:
grep "took" logs/nvidia_predictor_*.log
```

**Solutions:**

**1. Reduce article crawling**
```python
MAX_CRAWL_ARTICLES = 10  # Reduce from 20
```

**2. Limit news search period**
```python
NEWS_DAYS_BACK = 14  # Reduce from 30
```

**3. Use faster model**
```python
GEMINI_MODEL_FLASH = "gemini-1.5-flash"  # Faster than 2.5
```

**4. Reduce max iterations**
```python
MAX_ITERATIONS = 2  # Reduce from 3
```

**5. Optimize Playwright**

Edit `agents/crawler_agent.py`:
```python
# Add timeout and skip images
page.goto(url, timeout=15000, wait_until='domcontentloaded')
context = browser.new_context(
    bypass_csp=True,
    ignore_https_errors=True,
    java_script_enabled=True,
    # Disable images to speed up:
    # (requires additional config)
)
```

---

### Problem: High memory usage

**Symptoms:**
```
MemoryError
Process killed (OOM)
System becomes slow
```

**Solutions:**

**1. Reduce article storage**
```python
# In crawler_agent.py, limit content length:
full_content = content[:5000]  # Truncate long articles
```

**2. Clear state between iterations**

Edit `workflow/nodes.py`:
```python
# In feedback_node, optionally clear old data:
if state["iteration"] > 1:
    # Keep only recent articles
    state["articles"] = state["articles"][-20:]
```

**3. Use generator patterns**

For large datasets, process in chunks rather than loading all at once.

**4. Monitor memory**
```bash
# Check memory usage during execution
watch -n 1 'ps aux | grep python | grep main.py'
```

---

## Data Quality Issues

### Problem: Duplicate articles

**Symptoms:**
- Same article appears multiple times
- Article count doesn't increase much between iterations

**Diagnosis:**
```python
# Check for duplicates in saved JSON:
import json
with open('nvidia_multi_agent_*.json') as f:
    data = json.load(f)
    urls = [a['url'] for a in data['raw_articles']]
    print(f"Total: {len(urls)}, Unique: {len(set(urls))}")
```

**Solution:**

The system should automatically deduplicate. If not working:

Edit `workflow/nodes.py` in `crawler_node`:
```python
# Ensure deduplication logic is correct:
existing_urls = {a["url"] for a in state.get("articles", [])}
merged_articles = state.get("articles", []).copy()

for article in crawled:
    if article["url"] not in existing_urls:
        merged_articles.append(article)
        existing_urls.add(article["url"])  # Add to set
```

---

### Problem: Irrelevant news articles

**Symptoms:**
- Articles not about NVIDIA
- Generic tech news
- Low relevance scores

**Solutions:**

**1. Improve keyword specificity**

Keywords should include "NVIDIA" or "NVDA":
```python
# Good keywords:
"NVIDIA quarterly earnings"
"NVDA stock analysis"
"Jensen Huang announcement"

# Avoid generic:
"AI chip market"  # Too broad
"semiconductor industry"  # Too general
```

**2. Add filtering in crawler**

Edit `agents/crawler_agent.py`:
```python
def fetch_news(self, keywords):
    # Add NVIDIA filter
    filtered_keywords = [f"NVIDIA {kw}" for kw in keywords]
    # ... rest of code
```

**3. Increase relevance threshold**

Edit `agents/merge_agent.py`:
```python
# Filter out low-relevance packs
news_packs = [p for p in news_packs if p.relevance_score > 0.5]
```

---

### Problem: Old news articles

**Symptoms:**
```
Recency: 15%
Most articles > 14 days old
```

**Solutions:**

**1. Reduce search period**
```python
NEWS_DAYS_BACK = 7  # Only recent news
```

**2. Sort by recency**

Edit `agents/crawler_agent.py`:
```python
# In fetch_news, add sort parameter:
all_articles = newsapi.get_everything(
    q=query,
    language='en',
    sort_by='publishedAt',  # Most recent first
    # ...
)
```

**3. Filter old articles**
```python
from datetime import datetime, timedelta

# In crawler_agent.py:
cutoff_date = datetime.now() - timedelta(days=7)
recent_articles = [
    a for a in articles 
    if datetime.fromisoformat(a['publishedAt'].replace('Z', '+00:00')) > cutoff_date
]
```

---

## Advanced Debugging

### Enable detailed logging

Edit `main.py`:
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Enable LangGraph debugging
import os
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
```

---

### Inspect workflow state

Add state inspection in `workflow/nodes.py`:
```python
def validation_node(state: WorkflowState) -> WorkflowState:
    # Add debugging
    print(f"\n=== STATE DEBUG ===")
    print(f"Iteration: {state['iteration']}")
    print(f"Articles: {len(state.get('articles', []))}")
    print(f"Keywords: {state.get('keywords', [])}")
    print(f"==================\n")
    
    # ... rest of code
```

---

### Test individual agents

Create `test_agent.py`:
```python
from agents.keyword_agent import KeywordAgent
from config.settings import GEMINI_API_KEY
import google.generativeai as genai

# Test keyword generation
genai.configure(api_key=GEMINI_API_KEY)
client = genai.GenerativeModel('gemini-2.5-flash')

agent = KeywordAgent(client)
keywords = agent.generate_keywords()
print("Keywords:", keywords)
```

Run individual tests:
```bash
python test_agent.py
```

---

### Visualize workflow graph

```python
from workflow.graph import create_workflow

workflow = create_workflow()
print(workflow.get_graph().draw_mermaid())
```

Save to file:
```bash
python -c "from workflow.graph import create_workflow; print(create_workflow().get_graph().draw_mermaid())" > workflow.mmd
```

---

### Check API connectivity

```python
# test_apis.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Test News API
news_key = os.getenv('NEWS_API_KEY')
response = requests.get(
    f'https://newsapi.org/v2/top-headlines?apiKey={news_key}&q=NVIDIA'
)
print(f"News API: {response.status_code}")

# Test Gemini API
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY_JY'))
model = genai.GenerativeModel('gemini-2.5-flash')
result = model.generate_content("Test")
print(f"Gemini API: Success - {result.text[:50]}")
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs**: Review `logs/nvidia_predictor_*.log`
2. **Check saved results**: Examine JSON output files
3. **Run tests**: Execute `test_workflow.py`, `test_components.py`
4. **Review configuration**: Verify `config/settings.py` and `.env`
5. **Check system resources**: Ensure adequate memory and disk space

### Useful diagnostic commands

```bash
# System info
python --version
pip list | grep -E "langgraph|langchain|google-generativeai"

# Check environment
cat .env | grep -v "^#"

# Check logs
tail -f logs/nvidia_predictor_*.log

# Check disk space
df -h

# Check memory
free -h

# Check network
ping -c 3 newsapi.org
```

### Common error patterns

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `KeyError: 'GEMINI_API_KEY_JY'` | Missing .env file | Create .env with API key |
| `429 Resource Exhausted` | API rate limit | Wait or reduce requests |
| `Browser closed` | Playwright issue | Reinstall: `playwright install chromium` |
| `ModuleNotFoundError` | Missing dependency | `pip install -e .` |
| `Confidence: 0%` | No valid articles | Check NEWS_API_KEY and internet |
| `Timeout` | Network/slow response | Increase timeouts, check connection |

---

## Prevention Tips

1. **Always use virtual environment**
2. **Keep dependencies updated**: `pip install --upgrade langgraph langchain-core`
3. **Monitor API usage**: Track daily limits
4. **Regular testing**: Run test suite periodically
5. **Backup configurations**: Save working `.env` and `config/` files
6. **Review logs**: Check for warnings before they become errors
7. **Start simple**: Test with default settings before customizing

---

For additional support, refer to:
- [README.md](../README.md) - General usage
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [Design Document](.kiro/specs/langgraph-feedback-loop/design.md) - Architecture details
