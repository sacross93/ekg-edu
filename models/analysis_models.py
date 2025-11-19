"""
분석 및 검증 관련 Pydantic 모델

AnalysisAgent와 ValidationAgent의 출력 데이터 구조를 정의합니다.
감성 분석 결과와 검증 결과를 구조화된 형태로 표현합니다.
"""

from typing import List
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """
    근거 정보 모델
    
    감성 분석의 근거가 되는 문장과 이벤트 유형을 담습니다.
    
    Attributes:
        event_type: 이벤트 유형 (earnings/policy/product/supply/partnership/general)
        sentence: 근거가 되는 문장
    
    Example:
        >>> evidence = Evidence(
        ...     event_type="earnings",
        ...     sentence="NVIDIA Q4 실적이 예상을 상회했다"
        ... )
    """
    event_type: str = Field(description="이벤트 유형")
    sentence: str = Field(description="근거 문장")


class EventScores(BaseModel):
    """
    이벤트별 점수 모델
    
    각 이벤트 유형별로 감성 점수를 명시적 필드로 관리합니다.
    Dict 대신 명시적 필드를 사용하여 타입 안정성과 검증을 보장합니다.
    
    Attributes:
        earnings: 실적 관련 점수 (-3.0 ~ +3.0)
        policy: 정책/규제 점수 (-3.0 ~ +3.0)
        product: 제품 관련 점수 (-3.0 ~ +3.0)
        supply: 공급망 점수 (-3.0 ~ +3.0)
        partnership: 파트너십 점수 (-3.0 ~ +3.0)
    
    Note:
        모든 점수는 -3.0(매우 부정)에서 +3.0(매우 긍정) 범위입니다.
        관련 없는 이벤트는 0.0으로 설정됩니다.
    """
    earnings: float = Field(default=0.0, description="실적 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    policy: float = Field(default=0.0, description="정책/규제 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    product: float = Field(default=0.0, description="제품 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    supply: float = Field(default=0.0, description="공급망 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    partnership: float = Field(default=0.0, description="파트너십 점수 (-3 ~ +3)", ge=-3.0, le=3.0)


class SentimentAnalysis(BaseModel):
    """
    분석 에이전트 출력 모델
    
    AnalysisAgent가 생성한 감성 분석 결과를 담는 모델입니다.
    전체 감성 점수, 이벤트별 점수, 근거, 예측 기간, 방향을 포함합니다.
    
    Attributes:
        overall_sentiment: 전체 감성 점수 (-3.0 ~ +3.0)
        event_scores: 이벤트별 점수 객체
        evidences: 근거 리스트 (최소 3개)
        optimal_timeframe: 최적 예측 기간 (1-14일)
        direction: 예측 방향 (Up/Down/Hold)
    
    Example:
        >>> analysis = SentimentAnalysis(
        ...     overall_sentiment=2.5,
        ...     event_scores=EventScores(earnings=3.0, policy=-1.0),
        ...     evidences=[evidence1, evidence2, evidence3],
        ...     optimal_timeframe=7,
        ...     direction="Up"
        ... )
    """
    overall_sentiment: float = Field(description="전체 감성 점수 (-3.0 ~ +3.0)", ge=-3.0, le=3.0)
    event_scores: EventScores = Field(description="이벤트별 점수")
    evidences: List[Evidence] = Field(description="근거 리스트 (최소 3개)")
    optimal_timeframe: int = Field(description="최적 예측 기간 (1-14일)", ge=1, le=14)
    direction: str = Field(description="예측 방향: Up/Down/Hold 중 하나")


class ValidationResult(BaseModel):
    """
    검증 에이전트 출력 모델
    
    ValidationAgent가 생성한 검증 결과를 담는 모델입니다.
    신뢰도 점수, 유효성, 검증 사항, 반대 근거를 포함합니다.
    
    Attributes:
        confidence: 최종 신뢰도 점수 (0-100)
        is_valid: 임계치 통과 여부
        validation_notes: 검증 사항 리스트
        contra_arguments: 반대 근거 리스트 (Devil's Advocate)
    
    Example:
        >>> validation = ValidationResult(
        ...     confidence=75,
        ...     is_valid=True,
        ...     validation_notes=["출처 신뢰도: 85%", "일관성: 70%"],
        ...     contra_arguments=["규제 리스크 존재"]
        ... )
    """
    confidence: int = Field(description="최종 신뢰도 (0-100)", ge=0, le=100)
    is_valid: bool = Field(description="임계치 통과 여부")
    validation_notes: List[str] = Field(description="검증 사항")
    contra_arguments: List[str] = Field(description="반대 근거")
