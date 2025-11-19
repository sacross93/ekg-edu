"""
Configuration module for NVIDIA stock prediction system.

This module contains all configuration settings, constants,
and environment variable management.
"""

from .settings import (
    GEMINI_API_KEY,
    NEWS_API_KEY,
    CONFIDENCE_THRESHOLD,
    MAX_ITERATIONS,
    MAX_CRAWL_ARTICLES,
    NEWS_DAYS_BACK,
    GEMINI_MODEL_FLASH,
    GEMINI_MODEL_EXP,
)
from .constants import TRUSTED_SOURCES, EVENT_SETTINGS

__all__ = [
    'GEMINI_API_KEY',
    'NEWS_API_KEY',
    'CONFIDENCE_THRESHOLD',
    'MAX_ITERATIONS',
    'MAX_CRAWL_ARTICLES',
    'NEWS_DAYS_BACK',
    'GEMINI_MODEL_FLASH',
    'GEMINI_MODEL_EXP',
    'TRUSTED_SOURCES',
    'EVENT_SETTINGS',
]
