# Requirements Document

## Introduction

NVIDIA 주가 예측 멀티-에이전트 시스템에 LangGraph 기반 피드백 루프를 추가하여, 신뢰도가 낮은 분석 결과를 자동으로 개선하는 기능을 구현합니다. 시스템은 분석 신뢰도를 평가하고, 임계치 미달 시 부족한 정보를 식별하여 추가 데이터 수집 및 재분석을 수행합니다.

## Glossary

- **System**: NVIDIA 주가 예측 멀티-에이전트 시스템
- **LangGraph**: 상태 기반 그래프 워크플로우 프레임워크
- **Feedback Loop**: 신뢰도 기반 재시도 메커니즘
- **Confidence Score**: 분석 결과의 신뢰도 점수 (0-100)
- **Confidence Threshold**: 신뢰도 임계치 (기본값: 60)
- **Iteration Context**: 이전 시도의 결과 및 부족한 정보를 담은 컨텍스트
- **State**: LangGraph에서 관리하는 워크플로우 상태 객체
- **Node**: LangGraph 그래프의 각 처리 단계 (에이전트)
- **Edge**: 노드 간 전환 조건 및 경로
- **Max Iterations**: 최대 재시도 횟수 (기본값: 3)

## Requirements

### Requirement 1

**User Story:** As a 시스템 사용자, I want 신뢰도가 낮은 분석 결과를 자동으로 개선받고 싶다, so that 더 정확한 주가 예측을 얻을 수 있다

#### Acceptance Criteria

1. WHEN THE System SHALL calculate a Confidence Score below the Confidence Threshold, THE System SHALL initiate a Feedback Loop
2. WHILE THE System SHALL execute the Feedback Loop, THE System SHALL accumulate Iteration Context from previous attempts
3. WHEN THE System SHALL reach Max Iterations, THE System SHALL terminate the Feedback Loop and return the best available result
4. WHEN THE Confidence Score SHALL exceed the Confidence Threshold, THE System SHALL immediately terminate the Feedback Loop and return the result
5. THE System SHALL preserve all intermediate results for debugging and analysis purposes

### Requirement 2

**User Story:** As a 개발자, I want LangGraph를 사용하여 워크플로우를 구현하고 싶다, so that 상태 관리와 조건부 분기를 명확하게 처리할 수 있다

#### Acceptance Criteria

1. THE System SHALL use LangGraph to define the workflow as a directed graph with Nodes and Edges
2. THE System SHALL define a State object that contains all necessary data for the workflow
3. WHEN THE System SHALL transition between Nodes, THE System SHALL update the State with new information
4. THE System SHALL implement conditional Edges based on Confidence Score evaluation
5. THE System SHALL support visualization of the workflow graph for debugging

### Requirement 3

**User Story:** As a 시스템 사용자, I want 재시도 시 이전 시도의 부족한 점이 보완되기를 원한다, so that 반복할 때마다 분석 품질이 향상된다

#### Acceptance Criteria

1. WHEN THE System SHALL identify insufficient confidence, THE System SHALL extract specific deficiency reasons from validation results
2. THE System SHALL append deficiency information to the Iteration Context
3. WHEN THE System SHALL generate new keywords, THE System SHALL incorporate the Iteration Context to address previous deficiencies
4. WHEN THE System SHALL collect news, THE System SHALL merge new articles with previous articles to expand coverage
5. WHEN THE System SHALL perform sentiment analysis, THE System SHALL consider both current and previous analysis results

### Requirement 4

**User Story:** As a 시스템 관리자, I want 무한 루프를 방지하고 싶다, so that 시스템 리소스가 과도하게 소비되지 않는다

#### Acceptance Criteria

1. THE System SHALL enforce a Max Iterations limit of 3 attempts
2. WHEN THE System SHALL reach Max Iterations, THE System SHALL return the result with the highest Confidence Score among all attempts
3. THE System SHALL log each iteration attempt with timestamp and confidence metrics
4. THE System SHALL calculate and display total execution time across all iterations
5. WHERE THE System SHALL detect repeated failures, THE System SHALL provide actionable error messages to the user

### Requirement 5

**User Story:** As a 데이터 분석가, I want 각 반복의 결과를 비교하고 싶다, so that 피드백 루프의 효과를 평가할 수 있다

#### Acceptance Criteria

1. THE System SHALL store results from each iteration in the State object
2. THE System SHALL include iteration number, confidence score, and key findings for each attempt
3. WHEN THE System SHALL complete all iterations, THE System SHALL generate a comparison report showing improvement metrics
4. THE System SHALL save the complete iteration history to a JSON file
5. THE System SHALL display a summary table comparing confidence scores across iterations

### Requirement 6

**User Story:** As a 개발자, I want 기존 에이전트 코드를 최소한으로 수정하고 싶다, so that 시스템 안정성을 유지할 수 있다

#### Acceptance Criteria

1. THE System SHALL wrap existing agent classes without modifying their core logic
2. THE System SHALL create LangGraph Node functions that call existing agent methods
3. THE System SHALL maintain backward compatibility with the current Orchestrator interface
4. THE System SHALL add new functionality through composition rather than inheritance
5. THE System SHALL preserve all existing error handling and fallback mechanisms

### Requirement 7

**User Story:** As a 개발자, I want 코드를 모듈화된 구조로 재구성하고 싶다, so that 각 컴포넌트를 독립적으로 수정하고 테스트할 수 있다

#### Acceptance Criteria

1. THE System SHALL separate each agent class into individual module files under an agents directory
2. THE System SHALL extract Pydantic model definitions into separate model files under a models directory
3. THE System SHALL move configuration constants and settings into dedicated config files
4. THE System SHALL organize LangGraph workflow components into a workflow directory with separate files for graph definition, state management, and node functions
5. THE System SHALL create utility modules for output formatting and file handling operations
