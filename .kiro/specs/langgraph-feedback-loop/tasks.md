# Implementation Plan

- [x] 1. 프로젝트 구조 설정 및 기본 모듈 생성
  - 디렉토리 구조 생성 (agents/, models/, config/, workflow/, utils/)
  - 각 디렉토리에 `__init__.py` 파일 생성
  - 기존 `nvidia_multi_agent_predictor.py`를 참조용으로 유지
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. 설정 및 상수 모듈 구현
  - [x] 2.1 `config/settings.py` 작성
    - API 키 로드 (GEMINI_API_KEY, NEWS_API_KEY)
    - 워크플로우 설정 (CONFIDENCE_THRESHOLD, MAX_ITERATIONS 등)
    - 모델 설정 (GEMINI_MODEL_FLASH, GEMINI_MODEL_EXP)
    - _Requirements: 7.3_
  
  - [x] 2.2 `config/constants.py` 작성
    - TRUSTED_SOURCES 딕셔너리 정의
    - EVENT_SETTINGS 딕셔너리 정의
    - _Requirements: 7.3_

- [x] 3. Pydantic 모델 분리 및 구현
  - [x] 3.1 `models/search_models.py` 작성
    - SearchKeywords 모델 이동
    - _Requirements: 7.2_
  
  - [x] 3.2 `models/news_models.py` 작성
    - NewsPack, NewsPacks 모델 이동
    - _Requirements: 7.2_
  
  - [x] 3.3 `models/analysis_models.py` 작성
    - Evidence, EventScores, SentimentAnalysis 모델 이동
    - ValidationResult 모델 이동
    - _Requirements: 7.2_

- [x] 4. 에이전트 모듈 분리
  - [x] 4.1 `agents/keyword_agent.py` 작성
    - KeywordAgent 클래스 이동
    - `generate_keywords()` 메서드 유지
    - `generate_keywords_with_context(context: IterationContext)` 메서드 추가
    - _Requirements: 3.3, 6.1, 7.1_
  
  - [x] 4.2 `agents/crawler_agent.py` 작성
    - CrawlerAgent 클래스 이동
    - `fetch_news()`, `crawl_articles()` 메서드 유지
    - _Requirements: 6.1, 7.1_
  
  - [x] 4.3 `agents/merge_agent.py` 작성
    - MergeAgent 클래스 이동
    - `merge_and_refine()` 메서드 유지
    - _Requirements: 6.1, 7.1_
  
  - [x] 4.4 `agents/analysis_agent.py` 작성
    - AnalysisAgent 클래스 이동
    - `analyze()` 메서드에 `previous_analysis` 파라미터 추가
    - 이전 분석 결과를 프롬프트에 통합
    - _Requirements: 3.5, 6.1, 7.1_
  
  - [x] 4.5 `agents/validation_agent.py` 작성
    - ValidationAgent 클래스 이동
    - `validate()` 메서드 유지
    - _Requirements: 6.1, 7.1_

- [x] 5. 워크플로우 상태 관리 구현
  - [x] 5.1 `workflow/state.py` 작성
    - IterationContext 데이터클래스 정의
    - WorkflowState TypedDict 정의
    - State 초기화 함수 작성
    - _Requirements: 1.2, 2.2, 3.2_
  
  - [x] 5.2 State 초기화 및 업데이트 유틸리티 함수 작성
    - `create_initial_state()` 함수
    - `update_state()` 헬퍼 함수
    - `merge_articles()` 함수
    - `create_iteration_context()` 함수
    - _Requirements: 2.3_

- [x] 6. LangGraph 노드 함수 구현
  - [x] 6.1 `workflow/nodes.py` 작성 - 기본 노드들
    - `keyword_node()` 함수 구현
    - `crawler_node()` 함수 구현 (기사 병합 로직 포함)
    - `merge_node()` 함수 구현
    - _Requirements: 2.1, 2.3, 3.4, 6.2_
  
  - [x] 6.2 `workflow/nodes.py` 작성 - 분석 및 검증 노드
    - `analysis_node()` 함수 구현 (이전 분석 참고)
    - `validation_node()` 함수 구현 (결과 저장)
    - _Requirements: 1.5, 2.3, 3.5, 6.2_
  
  - [x] 6.3 `workflow/nodes.py` 작성 - 피드백 및 제어 노드
    - `feedback_node()` 함수 구현 (컨텍스트 생성)
    - `should_continue_or_end()` 조건 함수 구현
    - _Requirements: 1.1, 1.3, 1.4, 3.1, 3.2, 4.1_

- [x] 7. LangGraph 그래프 정의 및 컴파일
  - [x] 7.1 `workflow/graph.py` 작성
    - StateGraph 생성
    - 모든 노드 추가
    - 순차 엣지 정의
    - 조건부 엣지 정의 (validation → feedback or END)
    - 그래프 컴파일
    - _Requirements: 2.1, 2.4, 7.4_
  
  - [x] 7.2 그래프 시각화 함수 추가
    - Mermaid 다이어그램 생성 함수
    - `print_workflow_diagram()` 함수
    - _Requirements: 2.5_

- [x] 8. 유틸리티 모듈 구현
  - [x] 8.1 `utils/output_formatter.py` 작성
    - `print_final_result()` 함수 구현
    - `print_iteration_comparison()` 함수 구현
    - `print_iteration_summary()` 함수 구현
    - _Requirements: 5.5, 7.5_
  
  - [x] 8.2 `utils/file_handler.py` 작성
    - `save_result_to_json()` 함수 구현
    - `save_iteration_history()` 함수 구현
    - `save_workflow_state()` 함수 구현
    - `load_result_from_json()` 함수 구현
    - _Requirements: 5.4, 7.5_

- [x] 9. 메인 실행 파일 작성
  - [x] 9.1 `main.py` 작성
    - 워크플로우 초기화
    - State 초기화
    - 그래프 실행
    - 결과 출력 및 저장
    - _Requirements: 1.1, 1.3, 1.4, 4.4, 5.1, 5.2, 5.3_
  
  - [x] 9.2 로깅 설정 추가
    - 각 반복의 로그 기록
    - 실행 시간 측정
    - 타임스탬프가 포함된 로그 파일 생성
    - _Requirements: 4.3, 4.4_

- [x] 10. 결과 비교 및 개선 메트릭 구현
  - [x] 10.1 반복 간 비교 로직 구현
    - 신뢰도 변화 추적 (print_iteration_comparison)
    - 기사 수 증가 추적
    - 개선 메트릭 계산 및 출력
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 10.2 최종 보고서 생성
    - 모든 반복의 요약 테이블 (print_iteration_comparison)
    - 개선 효과 표시
    - 반복 히스토리 JSON 저장 (save_iteration_history)
    - _Requirements: 5.3, 5.5_

- [x] 11. 에러 처리 및 폴백 메커니즘 강화
  - [x] 11.1 각 노드에 에러 처리 강화
    - 노드 실패 시 State에 에러 정보 기록
    - 부분 결과로 계속 진행할 수 있도록 개선
    - 각 에이전트의 폴백 메커니즘 검증
    - _Requirements: 6.5_
  
  - [x] 11.2 무한 루프 방지 로직 검증 및 테스트
    - max_iterations 강제 적용 확인
    - 타임아웃 메커니즘 추가 (선택적)
    - 엣지 케이스 테스트
    - _Requirements: 4.1, 4.2_

- [x] 12. 통합 및 최종 테스트
  - [x] 12.1 전체 워크플로우 실행 테스트
    - 정상 시나리오 테스트 (첫 시도에서 높은 신뢰도)
    - 재시도 시나리오 테스트 (낮은 신뢰도로 피드백 루프 발동)
    - 최대 반복 시나리오 테스트 (3회 반복 후 종료)
    - _Requirements: 1.1, 1.3, 1.4_
  
  - [x] 12.2 결과 검증 및 품질 확인
    - 신뢰도 개선 효과 확인
    - 컨텍스트 누적 및 활용 확인
    - 최고 결과 선택 로직 검증
    - 저장된 결과 파일 검증
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2_
  
  - [x] 12.3 성능 및 안정성 테스트
    - 실행 시간 측정 및 최적화
    - 메모리 사용량 모니터링
    - API 호출 횟수 확인
    - _Requirements: 6.3_

- [ ] 13. 문서화 및 정리
  - [x] 13.1 README 업데이트
    - 새로운 모듈 구조 설명
    - LangGraph 피드백 루프 설명
    - 실행 방법 및 요구사항 업데이트
    - 설정 가이드 추가 (환경 변수, 임계치 등)
  
  - [x] 13.2 코드 주석 및 docstring 검토
    - 각 함수의 docstring 완성도 확인
    - 복잡한 로직에 인라인 주석 추가
    - 타입 힌트 일관성 확인
  
  - [x] 13.3 예제 및 사용 가이드 작성
    - 샘플 실행 결과 저장
    - 반복 비교 예제 추가
    - 트러블슈팅 가이드 작성
