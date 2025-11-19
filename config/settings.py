"""
Configuration settings for NVIDIA Multi-Agent Predictor with LangGraph Feedback Loop.

This module loads environment variables and defines workflow, model, and API settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# API Keys
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_JY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_JY가 .env 파일에 설정되지 않았습니다.")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "dcc50abaec994513939365149361eee1")

# ============================================================================
# Workflow Settings
# ============================================================================

# Confidence threshold for feedback loop (0-100)
CONFIDENCE_THRESHOLD = 60

# Maximum number of iterations in feedback loop
MAX_ITERATIONS = 3

# Maximum number of articles to crawl
MAX_CRAWL_ARTICLES = 20

# Number of days to look back for news
NEWS_DAYS_BACK = 30

# ============================================================================
# Model Settings
# ============================================================================

# Gemini model for fast operations (keyword generation, crawling checks)
GEMINI_MODEL_FLASH = "gemini-2.5-flash"

# Gemini model for complex operations (analysis, validation)
GEMINI_MODEL_EXP = "gemini-2.0-flash-exp"
