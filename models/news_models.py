"""
뉴스 관련 Pydantic 모델

MergeAgent의 출력 데이터 구조를 정의합니다.
뉴스팩은 관련된 여러 기사를 하나의 이벤트로 그룹화한 단위입니다.
"""

from typing import List
from pydantic import BaseModel, Field


class NewsPack(BaseModel):
    """
    뉴스팩 구조
    
    관련된 여러 기사를 하나의 이벤트로 그룹화한 단위입니다.
    중복/재탕 기사를 통합하고 핵심 내용을 요약합니다.
    
    Attributes:
        pack_id: 뉴스팩 고유 ID (예: pack_001)
        event_type: 이벤트 유형 (earnings/policy/product/supply/partnership/general)
        summary: 핵심 내용 요약 (3-5문장)
        relevance_score: NVIDIA 관련성 점수 (0.0-1.0)
        article_indices: 포함된 기사의 인덱스 리스트
    
    Example:
        >>> pack = NewsPack(
        ...     pack_id="pack_001",
        ...     event_type="earnings",
        ...     summary="NVIDIA Q4 실적 발표...",
        ...     relevance_score=0.95,
        ...     article_indices=[0, 1, 2]
        ... )
    """
    pack_id: str = Field(description="뉴스팩 ID (예: pack_001)")
    event_type: str = Field(description="이벤트 유형: earnings/policy/product/supply/partnership/general")
    summary: str = Field(description="핵심 내용 요약 (3-5문장)")
    relevance_score: float = Field(description="NVIDIA 관련성 점수 (0.0-1.0)")
    article_indices: List[int] = Field(description="포함된 기사 인덱스")


class NewsPacks(BaseModel):
    """
    병합 에이전트 출력 모델
    
    MergeAgent가 생성한 뉴스팩 리스트를 담는 모델입니다.
    Gemini의 구조화된 출력 기능을 위한 스키마로 사용됩니다.
    
    Attributes:
        packs: 생성된 뉴스팩 리스트 (5-10개)
    
    Example:
        >>> result = NewsPacks(packs=[pack1, pack2, pack3])
    """
    packs: List[NewsPack] = Field(description="뉴스팩 리스트 (5-10개)")
