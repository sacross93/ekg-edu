"""
LangGraph 그래프 정의 모듈

NVIDIA 주가 예측 멀티-에이전트 시스템의 피드백 루프 워크플로우를 정의합니다.
LangGraph를 사용하여 상태 기반 그래프로 워크플로우를 구성하고,
신뢰도 기반 조건부 분기를 통해 자동 재시도 메커니즘을 구현합니다.
"""

from langgraph.graph import StateGraph, END
from workflow.state import WorkflowState
from workflow import nodes


def create_workflow() -> StateGraph:
    """
    LangGraph 워크플로우 생성 및 컴파일
    
    워크플로우는 다음 단계로 구성됩니다:
    1. keyword_generation: 검색 키워드 생성
    2. news_collection: 뉴스 수집 및 크롤링
    3. news_merge: 뉴스 병합 및 정제
    4. sentiment_analysis: 감성 분석
    5. validation: 결과 검증 및 신뢰도 계산
    6. feedback: 피드백 생성 (조건부)
    
    신뢰도가 임계치 미만이고 최대 반복 횟수에 도달하지 않았다면
    피드백 노드를 거쳐 다시 키워드 생성으로 돌아갑니다.
    
    Returns:
        컴파일된 StateGraph 객체
    """
    # StateGraph 생성
    workflow = StateGraph(WorkflowState)
    
    # 노드 추가
    workflow.add_node("keyword_generation", nodes.keyword_node)
    workflow.add_node("news_collection", nodes.crawler_node)
    workflow.add_node("news_merge", nodes.merge_node)
    workflow.add_node("sentiment_analysis", nodes.analysis_node)
    workflow.add_node("validation", nodes.validation_node)
    workflow.add_node("feedback", nodes.feedback_node)
    
    # 진입점 설정
    workflow.set_entry_point("keyword_generation")
    
    # 순차 엣지 정의
    workflow.add_edge("keyword_generation", "news_collection")
    workflow.add_edge("news_collection", "news_merge")
    workflow.add_edge("news_merge", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "validation")
    
    # 조건부 엣지: validation → feedback or END
    # 신뢰도가 임계치 미만이면 feedback으로, 그렇지 않으면 종료
    workflow.add_conditional_edges(
        "validation",
        nodes.should_continue_or_end,
        {
            "continue": "feedback",
            "end": END
        }
    )
    
    # 피드백 후 다시 키워드 생성으로 (피드백 루프)
    workflow.add_edge("feedback", "keyword_generation")
    
    # 그래프 컴파일
    return workflow.compile()


def get_workflow_graph():
    """
    컴파일된 워크플로우 그래프 반환
    
    메인 실행 파일에서 사용할 수 있도록 컴파일된 그래프를 반환합니다.
    
    Returns:
        컴파일된 워크플로우 그래프
    """
    return create_workflow()


def generate_mermaid_diagram() -> str:
    """
    워크플로우의 Mermaid 다이어그램 생성
    
    워크플로우의 구조를 시각화하기 위한 Mermaid 다이어그램 문자열을 생성합니다.
    이 다이어그램은 각 노드와 엣지, 조건부 분기를 포함합니다.
    
    Returns:
        Mermaid 다이어그램 문자열
    
    Example:
        >>> diagram = generate_mermaid_diagram()
        >>> print(diagram)
    """
    diagram = """```mermaid
graph TD
    Start([시작]) --> KeywordGen[키워드 생성<br/>keyword_generation]
    KeywordGen --> NewsColl[뉴스 수집<br/>news_collection]
    NewsColl --> NewsMerge[뉴스 병합<br/>news_merge]
    NewsMerge --> Analysis[감성 분석<br/>sentiment_analysis]
    Analysis --> Validation[검증<br/>validation]
    
    Validation --> Decision{신뢰도 체크}
    
    Decision -->|신뢰도 >= 60%<br/>또는<br/>최대 반복 도달| End([종료])
    Decision -->|신뢰도 < 60%<br/>그리고<br/>반복 가능| Feedback[피드백 생성<br/>feedback]
    
    Feedback --> KeywordGen
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Decision fill:#FFD700
    style Feedback fill:#87CEEB
    style KeywordGen fill:#E6E6FA
    style NewsColl fill:#E6E6FA
    style NewsMerge fill:#E6E6FA
    style Analysis fill:#E6E6FA
    style Validation fill:#E6E6FA
```"""
    return diagram


def print_workflow_diagram():
    """
    워크플로우 다이어그램을 콘솔에 출력
    
    Mermaid 다이어그램을 생성하여 콘솔에 출력합니다.
    이 다이어그램은 Markdown 뷰어나 Mermaid 지원 도구에서 렌더링할 수 있습니다.
    """
    print("\n" + "="*80)
    print("워크플로우 구조 다이어그램")
    print("="*80)
    print(generate_mermaid_diagram())
    print("="*80 + "\n")
