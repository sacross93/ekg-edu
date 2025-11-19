# Documentation

Complete documentation for the NVIDIA Stock Predictor with LangGraph Feedback Loop.

## Getting Started

### New Users

1. **[Quick Start Guide](QUICK_START.md)** ⚡
   - 5-minute setup
   - First run instructions
   - Basic configuration

### Learning the System

2. **[Usage Examples](EXAMPLES.md)** 📚
   - Example 1: High confidence on first iteration
   - Example 2: Feedback loop improvement
   - Example 3: Maximum iterations reached
   - Understanding output and interpreting results

3. **[Sample Results](sample_results/)** 📊
   - `feedback_loop_example.json` - Complete iteration history
   - Real-world output examples
   - Iteration comparison data

### Troubleshooting

4. **[Troubleshooting Guide](TROUBLESHOOTING.md)** 🔧
   - Installation issues
   - API and authentication problems
   - Execution errors
   - Low confidence issues
   - Performance optimization
   - Data quality problems
   - Advanced debugging

## Architecture Documentation

### Design and Specifications

Located in `.kiro/specs/langgraph-feedback-loop/`:

- **[Requirements](../.kiro/specs/langgraph-feedback-loop/requirements.md)**
  - System requirements
  - User stories and acceptance criteria
  - EARS-compliant specifications

- **[Design](../.kiro/specs/langgraph-feedback-loop/design.md)**
  - Architecture overview
  - Module structure
  - Component interfaces
  - Data models
  - Error handling strategy
  - Testing approach

- **[Tasks](../.kiro/specs/langgraph-feedback-loop/tasks.md)**
  - Implementation plan
  - Task breakdown
  - Progress tracking

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── QUICK_START.md              # 5-minute setup guide
├── EXAMPLES.md                 # Detailed usage examples
├── TROUBLESHOOTING.md          # Problem-solving guide
└── sample_results/             # Example output files
    └── feedback_loop_example.json
```

## Key Concepts

### LangGraph Workflow

The system uses LangGraph to implement a state-based workflow with conditional branching:

```
Keyword → Crawler → Merge → Analysis → Validation
                                           ↓
                                    Confidence Check
                                     ↙         ↘
                              Pass (≥60%)   Fail (<60%)
                                 ↓              ↓
                                END         Feedback
                                               ↓
                                          (retry up to 3x)
```

### Feedback Loop

When confidence is below threshold:
1. System identifies deficiencies
2. Generates improved keywords
3. Collects additional articles
4. Re-analyzes with accumulated context
5. Repeats until confidence ≥ 60% or max iterations reached

### Confidence Scoring

Overall confidence (0-100) calculated from:
- **Source Reliability (40%)**: Based on trusted source whitelist
- **Evidence Quality (30%)**: Number and specificity of evidence
- **Argument Balance (20%)**: Positive vs negative factors
- **Recency (10%)**: How recent the news articles are

## Common Workflows

### Standard Prediction

```bash
# Run with defaults
python main.py

# Output: JSON file + console summary
# Time: 2-7 minutes
```

### Custom Configuration

```python
# Edit config/settings.py
CONFIDENCE_THRESHOLD = 70  # More strict
MAX_ITERATIONS = 5         # More retries
NEWS_DAYS_BACK = 60       # Longer search period
```

### Testing

```bash
# Test workflow
python test_workflow.py

# Test components
python test_components.py

# Performance test
python test_performance.py
```

## File Locations

### Configuration Files

- `.env` - API keys (create this)
- `config/settings.py` - Workflow settings
- `config/constants.py` - Trusted sources, event weights

### Output Files

- `nvidia_multi_agent_YYYYMMDD_HHMMSS.json` - Results
- `logs/nvidia_predictor_YYYYMMDD_HHMMSS.log` - Execution logs

### Source Code

- `agents/` - AI agent implementations
- `models/` - Pydantic data models
- `workflow/` - LangGraph workflow components
- `utils/` - Utility functions
- `main.py` - Entry point

## Quick Reference

### Environment Variables

```bash
GEMINI_API_KEY_JY=<your_key>    # Required
NEWS_API_KEY=<your_key>         # Optional (default provided)
```

### Key Settings

```python
CONFIDENCE_THRESHOLD = 60       # Minimum acceptable confidence
MAX_ITERATIONS = 3              # Maximum retry attempts
MAX_CRAWL_ARTICLES = 20        # Articles per iteration
NEWS_DAYS_BACK = 30            # Days to search back
```

### Trusted Sources (Reliability Scores)

```python
Reuters, Bloomberg, WSJ = 1.0   # Highest reliability
Financial Times, AP = 0.9
CNBC, MarketWatch = 0.8
Yahoo Finance = 0.7
Investing.com = 0.6
```

### Event Weights

```python
Earnings = 3.0 (highest impact)
Guidance = 2.5
Policy = 2.0
Product = 1.5
Partnership = 1.2
Supply = 1.0
General = 0.5 (lowest impact)
```

## Interpreting Results

### Confidence Levels

| Range | Meaning | Action |
|-------|---------|--------|
| 70-100% | High confidence | Reliable prediction |
| 60-69% | Medium confidence | Use with other inputs |
| 0-59% | Low confidence | Treat with caution |

### Direction Indicators

- **⬆️ UP**: Positive sentiment > +1.0
- **⬇️ DOWN**: Negative sentiment < -1.0
- **➡️ NEUTRAL**: Sentiment between -1.0 and +1.0

### Timeframe

Typical prediction windows:
- **3-7 days**: Earnings, partnerships
- **5-10 days**: Product launches, general news
- **7-14 days**: Policy changes, supply chain

## Best Practices

1. **Run during market hours** for most recent news
2. **Check confidence score** before acting on predictions
3. **Review iteration history** to understand improvements
4. **Monitor API usage** to avoid rate limits
5. **Keep dependencies updated** for best performance
6. **Review logs** when troubleshooting
7. **Backup configurations** before making changes

## Troubleshooting Quick Links

Common issues and solutions:

- [Installation Problems](TROUBLESHOOTING.md#installation-issues)
- [API Errors](TROUBLESHOOTING.md#api-and-authentication)
- [Low Confidence](TROUBLESHOOTING.md#low-confidence-issues)
- [Performance Issues](TROUBLESHOOTING.md#performance-problems)
- [Data Quality](TROUBLESHOOTING.md#data-quality-issues)

## Additional Help

### Diagnostic Commands

```bash
# Check installation
python --version
pip list | grep -E "langgraph|langchain"

# Verify environment
cat .env

# Check logs
tail -f logs/nvidia_predictor_*.log

# Test APIs
python -c "from config.settings import *; print('Config loaded')"
```

### Getting Support

1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review [Usage Examples](EXAMPLES.md)
3. Examine log files in `logs/`
4. Check saved results in JSON files
5. Run test suite to verify setup
6. Open GitHub issue with details

## Contributing

When contributing documentation:

1. Keep examples realistic and tested
2. Include both success and failure scenarios
3. Provide clear error messages and solutions
4. Update this index when adding new docs
5. Use consistent formatting and style
6. Include code examples where helpful

## Version History

- **v1.0** - Initial documentation with feedback loop
  - Quick start guide
  - Usage examples
  - Troubleshooting guide
  - Sample results

## License

[Your License Here]

---

**Need help?** Start with the [Quick Start Guide](QUICK_START.md) or [Troubleshooting Guide](TROUBLESHOOTING.md).
