"""
워크플로우 상태 관리 모듈

LangGraph 워크플로우의 상태 정의 및 초기화 함수를 제공합니다.
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IterationContext:
    """
    각 반복의 컨텍스트 정보
    
    이전 시도의 결과와 부족한 점을 담아 다음 반복에서 개선할 수 있도록 합니다.
    """
    iteration: int
    deficiencies: List[str] = field(default_factory=list)
    contra_arguments: List[str] = field(default_factory=list)
    previous_keywords: List[str] = field(default_factory=list)
    previous_confidence: int = 0


class WorkflowState(TypedDict, total=False):
    """
    LangGraph 워크플로우 상태
    
    워크플로우 전체에서 공유되는 상태 정보를 정의합니다.
    각 노드는 이 상태를 읽고 업데이트합니다.
    """
    # 현재 반복 정보
    iteration: int
    max_iterations: int
    
    # 누적 컨텍스트
    iteration_contexts: List[IterationContext]
    
    # 현재 데이터
    keywords: List[str]
    articles: List[Dict[str, Any]]
    news_packs: List[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]]
    validation: Optional[Dict[str, Any]]
    
    # 결과 추적
    all_results: List[Dict[str, Any]]
    best_result: Optional[Dict[str, Any]]
    
    # 제어 플래그
    should_continue: bool
    final_result: Optional[Dict[str, Any]]
    
    # 에러 추적
    errors: List[Dict[str, Any]]
    has_critical_error: bool
    
    # 타임스탬프 추적
    start_time: Optional[str]
    iteration_timestamps: List[Dict[str, Any]]


def create_initial_state(max_iterations: int = 3) -> WorkflowState:
    """
    초기 워크플로우 상태 생성
    
    Args:
        max_iterations: 최대 반복 횟수 (기본값: 3)
    
    Returns:
        초기화된 WorkflowState 객체
    """
    return WorkflowState(
        # 현재 반복 정보
        iteration=1,
        max_iterations=max_iterations,
        
        # 누적 컨텍스트
        iteration_contexts=[],
        
        # 현재 데이터
        keywords=[],
        articles=[],
        news_packs=[],
        analysis=None,
        validation=None,
        
        # 결과 추적
        all_results=[],
        best_result=None,
        
        # 제어 플래그
        should_continue=True,
        final_result=None,
        
        # 에러 추적
        errors=[],
        has_critical_error=False,
        
        # 타임스탬프 추적
        start_time=datetime.now().isoformat(),
        iteration_timestamps=[]
    )



def update_state(state: WorkflowState, **updates) -> WorkflowState:
    """
    상태 업데이트 헬퍼 함수
    
    기존 상태를 복사하고 지정된 필드를 업데이트합니다.
    불변성을 유지하면서 상태를 안전하게 업데이트할 수 있습니다.
    
    Args:
        state: 현재 워크플로우 상태
        **updates: 업데이트할 필드와 값
    
    Returns:
        업데이트된 WorkflowState 객체
    
    Example:
        >>> new_state = update_state(state, iteration=2, keywords=["AI", "GPU"])
    """
    # 상태 복사
    new_state = state.copy()
    
    # 업데이트 적용
    for key, value in updates.items():
        if key in WorkflowState.__annotations__:
            new_state[key] = value
        else:
            raise KeyError(f"Invalid state key: {key}")
    
    return new_state


def merge_articles(existing_articles: List[Dict[str, Any]], 
                   new_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    기존 기사와 새 기사를 병합 (중복 제거)
    
    URL을 기준으로 중복을 제거하고 기사를 병합합니다.
    피드백 루프에서 이전 반복의 기사를 유지하면서 새 기사를 추가할 때 사용합니다.
    
    Args:
        existing_articles: 기존 기사 리스트
        new_articles: 새로 수집한 기사 리스트
    
    Returns:
        List[Dict[str, Any]]: 병합된 기사 리스트 (중복 제거됨)
    
    Note:
        URL이 없는 기사는 무시됩니다.
    """
    # 기존 기사의 URL 집합 생성 (중복 체크용)
    existing_urls = {article.get("url") for article in existing_articles if article.get("url")}
    
    # 기존 기사 복사 (불변성 유지)
    merged = existing_articles.copy()
    
    # 새 기사 추가 (중복 제거)
    for article in new_articles:
        url = article.get("url")
        # URL이 있고 중복이 아닌 경우에만 추가
        if url and url not in existing_urls:
            merged.append(article)
            existing_urls.add(url)  # 집합에 추가하여 다음 체크에서 중복 방지
    
    return merged


def create_iteration_context(
    iteration: int,
    validation: Dict[str, Any],
    keywords: List[str],
    article_count: int,
    analysis: Optional[Dict[str, Any]] = None
) -> IterationContext:
    """
    검증 결과로부터 다음 반복을 위한 컨텍스트 생성
    
    Args:
        iteration: 현재 반복 번호
        validation: 검증 결과
        keywords: 사용된 키워드 리스트
        article_count: 수집된 기사 수
        analysis: 분석 결과 (선택적)
    
    Returns:
        IterationContext 객체
    """
    confidence = validation.get("confidence", 0)
    deficiencies = []
    
    # 검증 노트에서 부족한 점 추출
    if validation.get("validation_notes"):
        deficiencies.extend(validation["validation_notes"])
    
    # 신뢰도에 따른 구체적인 개선 방향 추가
    # 낮은 신뢰도의 원인을 분석하여 다음 반복에서 개선
    if confidence < 40:
        # 신뢰도가 매우 낮으면 출처 품질 개선 필요
        deficiencies.append("출처 신뢰도가 매우 낮음 - 더 신뢰할 수 있는 소스 필요")
    
    if article_count < 10:
        # 기사 수가 부족하면 더 다양한 키워드로 검색 필요
        deficiencies.append("뉴스 기사 수 부족 - 더 다양한 키워드 필요")
    
    if analysis and not analysis.get("evidences"):
        # 근거가 부족하면 더 구체적인 이벤트 정보 필요
        deficiencies.append("근거 부족 - 더 구체적인 이벤트 정보 필요")
    
    # 반대 근거 추출
    contra_arguments = validation.get("contra_arguments", [])
    
    return IterationContext(
        iteration=iteration,
        deficiencies=deficiencies,
        contra_arguments=contra_arguments,
        previous_keywords=keywords,
        previous_confidence=confidence
    )
