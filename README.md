# NVIDIA Stock Predictor with LangGraph Feedback Loop

An intelligent multi-agent system for NVIDIA stock prediction that uses LangGraph to implement an iterative feedback loop. The system automatically improves analysis quality by re-collecting data and refining predictions when confidence scores are below threshold.

## Overview

This system combines multiple AI agents to:
1. Generate targeted search keywords for NVIDIA-related news
2. Collect and crawl news articles from various sources
3. Merge and refine articles into coherent news packs
4. Perform sentiment analysis with evidence extraction
5. Validate results and calculate confidence scores
6. **Automatically retry with improved context when confidence is low**

The LangGraph-based feedback loop ensures that low-confidence predictions are iteratively improved by identifying deficiencies and collecting additional data.

## Key Features

- **Iterative Feedback Loop**: Automatically retries analysis when confidence < 60%
- **Context Accumulation**: Each iteration learns from previous attempts
- **Smart Keyword Generation**: Adapts search strategy based on feedback
- **Article Deduplication**: Merges new articles with existing ones
- **Confidence Tracking**: Monitors improvement across iterations
- **Best Result Selection**: Returns the highest confidence result
- **Comprehensive Logging**: Tracks all iterations with detailed metrics

## Architecture

### Module Structure

```
nvidia_predictor/
├── agents/                    # AI agent implementations
│   ├── keyword_agent.py      # Generates search keywords
│   ├── crawler_agent.py      # Collects and crawls news
│   ├── merge_agent.py        # Merges articles into news packs
│   ├── analysis_agent.py     # Performs sentiment analysis
│   └── validation_agent.py   # Validates and scores results
│
├── models/                    # Pydantic data models
│   ├── search_models.py      # SearchKeywords
│   ├── news_models.py        # NewsPack, NewsPacks
│   └── analysis_models.py    # SentimentAnalysis, ValidationResult
│
├── config/                    # Configuration files
│   ├── settings.py           # API keys, thresholds, model settings
│   └── constants.py          # Trusted sources, event weights
│
├── workflow/                  # LangGraph workflow components
│   ├── state.py              # WorkflowState and IterationContext
│   ├── graph.py              # LangGraph graph definition
│   └── nodes.py              # Node functions for each agent
│
├── utils/                     # Utility functions
│   ├── output_formatter.py   # Result formatting and display
│   └── file_handler.py       # JSON file operations
│
└── main.py                    # Main execution entry point
```

### LangGraph Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│                                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Keyword  │───▶│ Crawler  │───▶│  Merge   │              │
│  │  Agent   │    │  Agent   │    │  Agent   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                                │                     │
│       │                                ▼                     │
│       │                         ┌──────────┐                │
│       │                         │ Analysis │                │
│       │                         │  Agent   │                │
│       │                         └──────────┘                │
│       │                                │                     │
│       │                                ▼                     │
│       │                         ┌──────────┐                │
│       │                         │Validation│                │
│       │                         │  Agent   │                │
│       │                         └──────────┘                │
│       │                                │                     │
│       │                                ▼                     │
│       │                         ┌──────────┐                │
│       │                    ┌───│Confidence│                 │
│       │                    │   │  Check   │                 │
│       │                    │   └──────────┘                 │
│       │                    │         │                      │
│       │              Pass  │         │ Fail                 │
│       │              (≥60) │         │ (<60)                │
│       │                    │         │                      │
│       │                    ▼         ▼                      │
│       │              ┌──────────┐  ┌──────────┐            │
│       │              │  Return  │  │ Feedback │            │
│       │              │  Result  │  │  Node    │            │
│       │              └──────────┘  └──────────┘            │
│       │                                │                     │
│       └────────────────────────────────┘                     │
│                  (Max 3 iterations)                          │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

### System Requirements

- Python 3.10 or higher
- Internet connection for API calls and news crawling

### Dependencies

```toml
dependencies = [
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "google-generativeai>=0.8.0",
    "newsapi-python>=0.2.7",
    "playwright>=1.40.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0"
]
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nvidia_predictor
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install -e .
```

### 3. Install Playwright Browser

```bash
playwright install chromium
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY_JY=your_gemini_api_key_here

# Optional: News API Key (default provided)
NEWS_API_KEY=your_news_api_key_here
```

**Getting API Keys:**
- **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **News API**: Get from [NewsAPI.org](https://newsapi.org/register)

## Configuration

### Workflow Settings (`config/settings.py`)

```python
# Confidence threshold for accepting results
CONFIDENCE_THRESHOLD = 60  # Results below this trigger retry

# Maximum number of iterations
MAX_ITERATIONS = 3  # Prevents infinite loops

# News collection settings
MAX_CRAWL_ARTICLES = 20  # Max articles to crawl per iteration
NEWS_DAYS_BACK = 30  # How far back to search for news

# Model selection
GEMINI_MODEL_FLASH = "gemini-2.5-flash"  # Fast model
GEMINI_MODEL_EXP = "gemini-2.0-flash-exp"  # Experimental model
```

### Trusted Sources (`config/constants.py`)

The system weights news sources by reliability:

```python
TRUSTED_SOURCES = {
    'reuters': 1.0,
    'bloomberg': 1.0,
    'wall street journal': 1.0,
    'financial times': 0.9,
    'associated press': 0.9,
    'cnbc': 0.8,
    'marketwatch': 0.8,
    'yahoo finance': 0.7,
    'investing.com': 0.6
}
```

### Event Weights

Different event types have different impacts on predictions:

```python
EVENT_SETTINGS = {
    'earnings': {'weight': 3.0, 'days': (3, 7)},
    'guidance': {'weight': 2.5, 'days': (5, 10)},
    'policy': {'weight': 2.0, 'days': (7, 14)},
    'product': {'weight': 1.5, 'days': (5, 10)},
    'supply': {'weight': 1.0, 'days': (7, 14)},
    'partnership': {'weight': 1.2, 'days': (3, 7)},
    'general': {'weight': 0.5, 'days': (5, 10)}
}
```

## Usage

### Basic Execution

```bash
python main.py
```

### What Happens During Execution

1. **Iteration 1**: Initial analysis with default keywords
   - If confidence ≥ 60%: Returns result immediately
   - If confidence < 60%: Proceeds to iteration 2

2. **Iteration 2**: Improved analysis with feedback
   - Generates new keywords based on deficiencies
   - Collects additional articles
   - Merges with previous articles
   - Re-analyzes with accumulated context

3. **Iteration 3**: Final attempt (if needed)
   - Last chance to improve confidence
   - Returns best result from all iterations

### Output

The system provides:

1. **Console Output**:
   - Real-time progress for each iteration
   - Confidence scores and improvements
   - Final prediction with evidence

2. **JSON Files**:
   - `nvidia_multi_agent_YYYYMMDD_HHMMSS.json`: Final result
   - Includes all iterations and metadata

3. **Logs**:
   - `logs/nvidia_predictor_YYYYMMDD_HHMMSS.log`: Detailed execution log

### Example Output

```
=== Iteration 1 ===
Keywords: ['NVIDIA earnings Q4', 'Jensen Huang AI', ...]
Articles collected: 15
Confidence: 45% ❌ (Below threshold)

Deficiencies identified:
- Source reliability too low - need more trusted sources
- Insufficient evidence for earnings impact

=== Iteration 2 ===
Keywords: ['NVIDIA quarterly report', 'NVDA financial results', ...]
Articles collected: 28 (13 new)
Confidence: 72% ✅ (Above threshold)

Final Prediction:
Direction: UP
Confidence: 72%
Timeframe: 3-7 days
Key Evidence:
- Strong Q4 earnings beat expectations (Reuters)
- Data center revenue up 217% YoY (Bloomberg)
```

## How the Feedback Loop Works

### 1. Confidence Evaluation

After each analysis, the validation agent calculates:
- Source reliability score
- Evidence quality score
- Argument balance score
- Overall confidence (0-100)

### 2. Deficiency Identification

When confidence < 60%, the system identifies:
- Missing information types
- Weak evidence areas
- Source reliability issues
- Contradictory arguments

### 3. Context Accumulation

Each iteration builds on previous attempts:
```python
IterationContext:
  - iteration: 2
  - deficiencies: ["Need more trusted sources", "Weak earnings data"]
  - contra_arguments: ["Supply chain concerns mentioned"]
  - previous_keywords: ["NVIDIA AI", "Jensen Huang"]
  - previous_confidence: 45
```

### 4. Adaptive Keyword Generation

The keyword agent uses context to generate better keywords:
- Avoids repeating ineffective keywords
- Targets specific deficiencies
- Seeks more reliable sources
- Explores different angles

### 5. Article Merging

New articles are merged with existing ones:
- Deduplication by URL
- Preserves all unique articles
- Expands information coverage

### 6. Improved Analysis

The analysis agent considers:
- Current articles
- Previous analysis results
- Accumulated evidence
- Historical context

## Customization

### Adjusting Confidence Threshold

Edit `config/settings.py`:
```python
CONFIDENCE_THRESHOLD = 70  # More strict (fewer retries)
# or
CONFIDENCE_THRESHOLD = 50  # More lenient (more retries)
```

### Changing Max Iterations

```python
MAX_ITERATIONS = 5  # Allow more improvement attempts
```

### Modifying Trusted Sources

Add or modify sources in `config/constants.py`:
```python
TRUSTED_SOURCES = {
    'your_source': 0.9,  # Add new source
    'reuters': 1.0,
    # ...
}
```

### Using Different Models

```python
GEMINI_MODEL_FLASH = "gemini-1.5-pro"  # Use different model
```

## Troubleshooting

### Issue: Low Confidence Even After 3 Iterations

**Possible Causes:**
- Limited news availability for the period
- Contradictory information in sources
- Insufficient trusted sources

**Solutions:**
- Increase `NEWS_DAYS_BACK` to search further back
- Increase `MAX_CRAWL_ARTICLES` for more data
- Lower `CONFIDENCE_THRESHOLD` if appropriate

### Issue: API Rate Limits

**Solutions:**
- Add delays between API calls
- Use different API keys
- Reduce `MAX_CRAWL_ARTICLES`

### Issue: Playwright Browser Errors

**Solution:**
```bash
playwright install chromium --force
```

### Issue: Missing Environment Variables

**Error:** `GEMINI_API_KEY_JY not found`

**Solution:**
- Ensure `.env` file exists in project root
- Check variable name matches exactly
- Restart terminal after creating `.env`

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python test_workflow.py
python test_components.py
python test_performance.py
```

### Viewing Workflow Graph

The system can generate a Mermaid diagram of the workflow:
```python
from workflow.graph import create_workflow

workflow = create_workflow()
print(workflow.get_graph().draw_mermaid())
```

## Performance Considerations

- **Execution Time**: 2-5 minutes per iteration
- **API Calls**: ~10-20 per iteration (Gemini + News API)
- **Memory Usage**: ~200-500 MB
- **Network**: Requires stable internet connection

## Limitations

1. **News Availability**: Predictions depend on available news
2. **API Costs**: Multiple iterations increase API usage
3. **Real-time Data**: News may be delayed by hours
4. **Market Complexity**: Cannot predict unexpected events

## Future Enhancements

- Dynamic threshold adjustment based on market volatility
- Parallel keyword processing
- News caching to avoid duplicate crawling
- Real-time monitoring dashboard
- Support for multiple stocks
- Historical backtesting

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Documentation

### Quick Links

- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 5 minutes
- **[Usage Examples](docs/EXAMPLES.md)** - Real-world scenarios and output examples
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Solutions to common issues
- **[Sample Results](docs/sample_results/)** - Example output files

### Additional Resources

- **[Requirements Document](.kiro/specs/langgraph-feedback-loop/requirements.md)** - System requirements and specifications
- **[Design Document](.kiro/specs/langgraph-feedback-loop/design.md)** - Architecture and design details
- **[Implementation Tasks](.kiro/specs/langgraph-feedback-loop/tasks.md)** - Development task list

## Support

For issues and questions:
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md) first
- Review [Usage Examples](docs/EXAMPLES.md) for common scenarios
- Examine logs in `logs/` directory
- Open an issue on GitHub with log files attached