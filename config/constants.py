"""
Constants for NVIDIA Multi-Agent Predictor.

This module defines trusted news sources and event-specific settings
used for sentiment analysis and validation.
"""

# ============================================================================
# Trusted News Sources
# ============================================================================

# Whitelist of trusted news sources with reliability scores (0.0 - 1.0)
# Higher scores indicate more reliable sources
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

# ============================================================================
# Event Settings
# ============================================================================

# Event-specific weights and prediction timeframes
# Each event type has:
#   - weight: Impact multiplier for sentiment analysis (higher = more important)
#   - days: Tuple of (min_days, max_days) for prediction timeframe
EVENT_SETTINGS = {
    'earnings': {
        'weight': 3.0,
        'days': (3, 7)
    },
    'guidance': {
        'weight': 2.5,
        'days': (5, 10)
    },
    'policy': {
        'weight': 2.0,
        'days': (7, 14)
    },
    'product': {
        'weight': 1.5,
        'days': (5, 10)
    },
    'supply': {
        'weight': 1.0,
        'days': (7, 14)
    },
    'partnership': {
        'weight': 1.2,
        'days': (3, 7)
    },
    'general': {
        'weight': 0.5,
        'days': (5, 10)
    }
}
