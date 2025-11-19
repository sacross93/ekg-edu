# Quick Start Guide

Get up and running with the NVIDIA Stock Predictor in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Internet connection
- Google Gemini API key

## Installation (5 steps)

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd nvidia_predictor
```

### 2. Install Dependencies

**Option A: Using uv (recommended)**
```bash
uv sync
```

**Option B: Using pip**
```bash
pip install -e .
```

### 3. Install Playwright Browser

```bash
playwright install chromium
```

### 4. Configure API Keys

Create `.env` file:
```bash
cat > .env << EOF
GEMINI_API_KEY_JY=your_gemini_api_key_here
NEWS_API_KEY=your_news_api_key_here
EOF
```

**Get API Keys:**
- Gemini: https://makersuite.google.com/app/apikey
- News API: https://newsapi.org/register (optional, default provided)

### 5. Run

```bash
python main.py
```

## First Run

Expected output:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NVIDIA Stock Prediction Workflow                          ║
║                         LangGraph Feedback Loop                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Starting workflow with max 3 iterations...
Confidence threshold: 60%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              🔄 ITERATION 1 / 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Keyword Generation
   Generated 10 keywords...

🔍 News Collection
   Fetched articles...

[... continues ...]
```

Execution time: 2-7 minutes depending on iterations needed.

## Understanding Results

### High Confidence (≥ 60%)

```
✅ Validation
   Confidence Score: 78% ✅

Direction:     ⬆️  UP
Confidence:    78%
Timeframe:     3-7 days
```

**Meaning:** Strong prediction, reliable for stated timeframe.

### Low Confidence (< 60%)

```
✅ Validation
   Confidence Score: 42% ❌ (Below threshold)

🔄 Feedback Analysis
   Deficiencies identified:
   • Source reliability too low
   • Insufficient evidence
```

**Meaning:** System will retry with improved keywords (up to 3 times).

## Output Files

After execution, you'll find:

1. **Console output**: Real-time progress and final prediction
2. **JSON file**: `nvidia_multi_agent_YYYYMMDD_HHMMSS.json`
3. **Log file**: `logs/nvidia_predictor_YYYYMMDD_HHMMSS.log`

## Common Issues

### "GEMINI_API_KEY_JY not found"

**Fix:** Create `.env` file with your API key
```bash
echo "GEMINI_API_KEY_JY=your_key_here" > .env
```

### "playwright: command not found"

**Fix:** Install Playwright browsers
```bash
python -m playwright install chromium
```

### "ModuleNotFoundError: No module named 'langgraph'"

**Fix:** Install dependencies
```bash
pip install -e .
```

## Configuration

Edit `config/settings.py` to customize:

```python
# Adjust confidence threshold
CONFIDENCE_THRESHOLD = 60  # Lower = more lenient

# Change max iterations
MAX_ITERATIONS = 3  # Increase for more retries

# Modify news search period
NEWS_DAYS_BACK = 30  # Days to search back

# Limit articles crawled
MAX_CRAWL_ARTICLES = 20  # Per iteration
```

## Next Steps

- Read [EXAMPLES.md](EXAMPLES.md) for detailed usage examples
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues
- Review [README.md](../README.md) for complete documentation
- Examine sample results in `docs/sample_results/`

## Quick Tips

1. **First run may be slow** as Playwright downloads browser
2. **Free API tiers have limits** - monitor usage
3. **Confidence < 60% triggers retry** - this is normal
4. **Results saved automatically** - check JSON files
5. **Logs help debugging** - check `logs/` directory

## Example Commands

```bash
# Basic run
python main.py

# Run with verbose logging
python main.py 2>&1 | tee output.log

# Check test suite
python test_workflow.py
python test_components.py

# View saved results
cat nvidia_multi_agent_*.json | jq .

# Check logs
tail -f logs/nvidia_predictor_*.log
```

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Examples**: Review [EXAMPLES.md](EXAMPLES.md)
- **Tests**: Run test files to verify setup

## Success Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip list | grep langgraph`)
- [ ] Playwright browser installed (`playwright --version`)
- [ ] `.env` file created with API keys
- [ ] First run completed successfully
- [ ] JSON output file generated
- [ ] Confidence score displayed

If all checked, you're ready to use the system! 🎉
