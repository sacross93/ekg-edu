# Design Document

## Overview

LangGraph 기반 피드백 루프 시스템은 기존 NVIDIA 주가 예측 멀티-에이전트 시스템을 확장하여, 신뢰도가 낮은 분석 결과를 자동으로 개선하는 기능을 제공합니다. 시스템은 상태 기반 그래프 워크플로우를 사용하여 조건부 재시도 로직을 구현하며, 각 반복마다 이전 시도의 컨텍스트를 누적하여 분석 품질을 점진적으로 향상시킵니다.

## Architecture

### High-Level Architecture

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

### Module Structure

```
nvidia_predictor/
├── agents/
│   ├── __init__.py
│   ├── keyword_agent.py      # 키워드 생성 에이전트
│   ├── crawler_agent.py      # 뉴스 수집 에이전트
│   ├── merge_agent.py        # 뉴스 병합 에이전트
│   ├── analysis_agent.py     # 감성 분석 에이전트
│   └── validation_agent.py   # 검증 에이전트
│
├── models/
│   ├── __init__.py
│   ├── search_models.py      # SearchKeywords
│   ├── news_models.py        # NewsPack, NewsPacks
│   └── analysis_models.py    # SentimentAnalysis, ValidationResult, etc.
│
├── config/
│   ├── __init__.py
│   ├── settings.py           # API 키, 임계치 등
│   └── constants.py          # 신뢰 소스, 이벤트 가중치 등
│
├── workflow/
│   ├── __init__.py
│   ├── state.py              # WorkflowState 정의
│   ├── graph.py              # LangGraph 그래프 정의
│   └── nodes.py              # Node 함수들
│
├── utils/
│   ├── __init__.py
│   ├── output_formatter.py   # 결과 출력 포맷팅
│   └── file_handler.py       # JSON 파일 저장/로드
│
└── main.py                   # 메인 실행 파일
```

## Components and Interfaces

### 1. State Management (workflow/state.py)

```python
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class IterationContext:
    """각 반복의 컨텍스트"""
    iteration: int
    deficiencies: List[str]  # 부족한 점
    contra_arguments: List[str]  # 반대 근거
    previous_keywords: List[str]  # 이전 키워드
    previous_confidence: int  # 이전 신뢰도

class WorkflowState(TypedDict):
    """LangGraph 워크플로우 상태"""
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
    all_results: List[Dict[str, Any]]  # 각 반복의 결과
    best_result: Optional[Dict[str, Any]]  # 최고 신뢰도 결과
    
    # 제어 플래그
    should_continue: bool
    final_result: Optional[Dict[str, Any]]
```

### 2. LangGraph Workflow (workflow/graph.py)

```python
from langgraph.graph import StateGraph, END
from workflow.state import WorkflowState
from workflow import nodes

def create_workflow() -> StateGraph:
    """LangGraph 워크플로우 생성"""
    
    workflow = StateGraph(WorkflowState)
    
    # 노드 추가
    workflow.add_node("keyword_generation", nodes.keyword_node)
    workflow.add_node("news_collection", nodes.crawler_node)
    workflow.add_node("news_merge", nodes.merge_node)
    workflow.add_node("sentiment_analysis", nodes.analysis_node)
    workflow.add_node("validation", nodes.validation_node)
    workflow.add_node("feedback", nodes.feedback_node)
    
    # 엣지 정의
    workflow.set_entry_point("keyword_generation")
    workflow.add_edge("keyword_generation", "news_collection")
    workflow.add_edge("news_collection", "news_merge")
    workflow.add_edge("news_merge", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "validation")
    
    # 조건부 엣지: 신뢰도 체크
    workflow.add_conditional_edges(
        "validation",
        nodes.should_continue_or_end,
        {
            "continue": "feedback",
            "end": END
        }
    )
    
    # 피드백 후 다시 키워드 생성으로
    workflow.add_edge("feedback", "keyword_generation")
    
    return workflow.compile()
```

### 3. Node Functions (workflow/nodes.py)

각 노드는 기존 에이전트를 래핑하여 State를 업데이트합니다.

```python
from workflow.state import WorkflowState, IterationContext
from agents import KeywordAgent, CrawlerAgent, MergeAgent, AnalysisAgent, ValidationAgent

def keyword_node(state: WorkflowState) -> WorkflowState:
    """키워드 생성 노드"""
    agent = KeywordAgent(client)
    
    # 이전 컨텍스트 활용
    context = state["iteration_contexts"][-1] if state["iteration_contexts"] else None
    
    if context:
        # 피드백을 반영한 키워드 생성
        keywords = agent.generate_keywords_with_context(context)
    else:
        # 첫 시도
        keywords = agent.generate_keywords()
    
    state["keywords"] = keywords
    return state

def crawler_node(state: WorkflowState) -> WorkflowState:
    """뉴스 수집 노드"""
    agent = CrawlerAgent(news_api, client)
    
    # 새 뉴스 수집
    new_articles = agent.fetch_news(state["keywords"])
    crawled = agent.crawl_articles(new_articles)
    
    # 이전 기사와 병합 (중복 제거)
    existing_urls = {a["url"] for a in state.get("articles", [])}
    merged_articles = state.get("articles", []).copy()
    
    for article in crawled:
        if article["url"] not in existing_urls:
            merged_articles.append(article)
    
    state["articles"] = merged_articles
    return state

def merge_node(state: WorkflowState) -> WorkflowState:
    """뉴스 병합 노드"""
    agent = MergeAgent(client)
    news_packs = agent.merge_and_refine(state["articles"])
    state["news_packs"] = news_packs
    return state

def analysis_node(state: WorkflowState) -> WorkflowState:
    """감성 분석 노드"""
    agent = AnalysisAgent(client)
    
    # 이전 분석 결과 참고
    previous_analysis = None
    if state["all_results"]:
        previous_analysis = state["all_results"][-1].get("analysis")
    
    analysis = agent.analyze(
        state["news_packs"], 
        state["articles"],
        previous_analysis=previous_analysis
    )
    
    state["analysis"] = analysis
    return state

def validation_node(state: WorkflowState) -> WorkflowState:
    """검증 노드"""
    agent = ValidationAgent(client)
    
    validation = agent.validate(
        state["analysis"],
        state["news_packs"],
        state["articles"]
    )
    
    state["validation"] = validation
    
    # 결과 저장
    result = {
        "iteration": state["iteration"],
        "confidence": validation["confidence"],
        "analysis": state["analysis"],
        "validation": validation,
        "keywords": state["keywords"],
        "article_count": len(state["articles"])
    }
    
    state["all_results"].append(result)
    
    # 최고 결과 업데이트
    if not state["best_result"] or validation["confidence"] > state["best_result"]["confidence"]:
        state["best_result"] = result
    
    return state

def feedback_node(state: WorkflowState) -> WorkflowState:
    """피드백 노드 - 다음 반복을 위한 컨텍스트 생성"""
    
    validation = state["validation"]
    
    # 부족한 점 추출
    deficiencies = []
    if validation["confidence"] < 60:
        if validation.get("validation_notes"):
            deficiencies.extend(validation["validation_notes"])
        
        # 구체적인 개선 방향 추가
        if validation["confidence"] < 40:
            deficiencies.append("출처 신뢰도가 매우 낮음 - 더 신뢰할 수 있는 소스 필요")
        if len(state["articles"]) < 10:
            deficiencies.append("뉴스 기사 수 부족 - 더 다양한 키워드 필요")
        if not state["analysis"].get("evidences"):
            deficiencies.append("근거 부족 - 더 구체적인 이벤트 정보 필요")
    
    # 컨텍스트 생성
    context = IterationContext(
        iteration=state["iteration"],
        deficiencies=deficiencies,
        contra_arguments=validation.get("contra_arguments", []),
        previous_keywords=state["keywords"],
        previous_confidence=validation["confidence"]
    )
    
    state["iteration_contexts"].append(context)
    state["iteration"] += 1
    
    return state

def should_continue_or_end(state: WorkflowState) -> str:
    """계속 진행할지 종료할지 결정"""
    
    validation = state["validation"]
    confidence = validation["confidence"]
    
    # 신뢰도 충족 시 종료
    if confidence >= 60:
        return "end"
    
    # 최대 반복 도달 시 종료
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    
    # 계속 진행
    return "continue"
```

### 4. Agent Modifications

기존 에이전트에 컨텍스트 기반 생성 메서드 추가:

```python
# agents/keyword_agent.py

class KeywordAgent:
    def generate_keywords_with_context(self, context: IterationContext) -> List[str]:
        """이전 컨텍스트를 반영한 키워드 생성"""
        
        prompt = f"""당신은 금융 뉴스 검색 전문가입니다. NVIDIA(NVDA) 주가 예측을 위한 검색 키워드 10개를 생성하세요.

**이전 시도 정보**:
- 반복 횟수: {context.iteration}
- 이전 신뢰도: {context.previous_confidence}%
- 이전 키워드: {', '.join(context.previous_keywords)}

**부족했던 점**:
{chr(10).join(f'- {d}' for d in context.deficiencies)}

**반대 근거**:
{chr(10).join(f'- {a}' for a in context.contra_arguments)}

위 정보를 바탕으로, 부족한 부분을 보완할 수 있는 새로운 키워드를 생성하세요.
이전 키워드와 중복되지 않도록 하고, 더 구체적이고 다양한 관점의 키워드를 포함하세요."""

        # ... (기존 로직과 유사하게 구현)
```

```python
# agents/analysis_agent.py

class AnalysisAgent:
    def analyze(self, news_packs, articles, previous_analysis=None):
        """감성 분석 - 이전 분석 결과 참고"""
        
        context = ""
        if previous_analysis:
            context = f"""
**이전 분석 결과**:
- 전체 감성: {previous_analysis.get('overall_sentiment', 0)}
- 예측 방향: {previous_analysis.get('direction', 'Unknown')}
- 주요 근거: {', '.join(e.get('sentence', '')[:50] for e in previous_analysis.get('evidences', [])[:3])}

이전 분석을 참고하되, 새로운 정보를 통합하여 더 정확한 분석을 제공하세요.
"""
        
        # ... (기존 프롬프트에 context 추가)
```

## Data Models

### Iteration Context

```python
@dataclass
class IterationContext:
    iteration: int
    deficiencies: List[str]
    contra_arguments: List[str]
    previous_keywords: List[str]
    previous_confidence: int
```

### Workflow State

모든 워크플로우 데이터를 포함하는 중앙 상태 객체 (위 참조)

## Error Handling

### 1. Agent Failure Handling

각 노드에서 에이전트 실패 시:
- 기존 폴백 메커니즘 유지
- State에 에러 정보 기록
- 다음 노드로 진행 (부분 결과 사용)

### 2. Infinite Loop Prevention

- `max_iterations` 강제 적용 (기본값: 3)
- 각 반복마다 타임스탬프 기록
- 전체 실행 시간 제한 (선택적)

### 3. State Corruption

- State 업데이트 시 불변성 유지
- 각 노드는 State 복사본 수정
- 검증 실패 시 이전 State 복원

## Testing Strategy

### Unit Tests

1. **State Management Tests**
   - State 초기화 테스트
   - State 업데이트 테스트
   - IterationContext 생성 테스트

2. **Node Function Tests**
   - 각 노드의 입출력 테스트
   - 컨텍스트 전달 테스트
   - 에러 처리 테스트

3. **Conditional Logic Tests**
   - `should_continue_or_end` 분기 테스트
   - 신뢰도 임계치 테스트
   - 최대 반복 제한 테스트

### Integration Tests

1. **Single Iteration Test**
   - 전체 워크플로우 1회 실행
   - 결과 검증

2. **Multi-Iteration Test**
   - 신뢰도 낮은 시나리오로 2-3회 반복
   - 컨텍스트 누적 확인
   - 개선 효과 측정

3. **Edge Cases**
   - 첫 시도에서 높은 신뢰도
   - 모든 반복에서 낮은 신뢰도
   - 에이전트 실패 시나리오

### Performance Tests

- 전체 실행 시간 측정
- 각 노드별 실행 시간 프로파일링
- 메모리 사용량 모니터링

## Configuration

### settings.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_JY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "dcc50abaec994513939365149361eee1")

# Workflow Settings
CONFIDENCE_THRESHOLD = 60
MAX_ITERATIONS = 3
MAX_CRAWL_ARTICLES = 20
NEWS_DAYS_BACK = 30

# Model Settings
GEMINI_MODEL_FLASH = "gemini-2.5-flash"
GEMINI_MODEL_EXP = "gemini-2.0-flash-exp"
```

### constants.py

```python
# 신뢰 소스 화이트리스트
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

# 이벤트별 가중치 및 예측 기간
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

## Deployment Considerations

### Dependencies

```toml
[project]
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

### Environment Setup

1. `.env` 파일 설정
2. Playwright 브라우저 설치: `playwright install chromium`
3. 의존성 설치: `uv sync` 또는 `pip install -e .`

### Execution

```bash
python -m nvidia_predictor.main
```

## Monitoring and Logging

### Logging Strategy

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nvidia_predictor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Metrics to Track

- 각 반복의 신뢰도 점수
- 각 노드의 실행 시간
- 수집된 기사 수
- 생성된 뉴스팩 수
- 최종 예측 방향 및 신뢰도

## Future Enhancements

1. **동적 임계치 조정**: 시장 변동성에 따라 신뢰도 임계치 자동 조정
2. **병렬 처리**: 여러 키워드 세트를 병렬로 처리
3. **캐싱**: 이미 수집한 뉴스 캐싱하여 중복 크롤링 방지
4. **A/B 테스트**: 다른 LLM 모델 비교
5. **실시간 모니터링**: 대시보드를 통한 실시간 워크플로우 모니터링
