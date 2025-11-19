"""
검색 키워드 관련 Pydantic 모델

KeywordAgent의 출력 데이터 구조를 정의합니다.
"""

from typing import List
from pydantic import BaseModel, Field


class SearchKeywords(BaseModel):
    """
    키워드 에이전트 출력 모델
    
    KeywordAgent가 생성한 검색 키워드와 선택 이유를 담는 모델입니다.
    Gemini의 구조화된 출력 기능을 위한 스키마로 사용됩니다.
    
    Attributes:
        keywords: 생성된 검색 키워드 리스트 (최대 10개)
        reasoning: 키워드 선택 이유 및 전략 설명
    
    Example:
        >>> result = SearchKeywords(
        ...     keywords=["NVIDIA earnings", "NVDA stock forecast"],
        ...     reasoning="실적과 전망 관련 키워드 선택"
        ... )
    """
    keywords: List[str] = Field(description="검색 키워드 리스트 (10개)")
    reasoning: str = Field(description="키워드 선택 이유")
