# NVIDIA 주가 예측 시스템

LangChain과 Gemini 2.5 Flash를 사용한 뉴스 기반 NVIDIA 주가 예측 시스템입니다.

## 설치 방법

### 1. 의존성 설치 (uv 사용)

```bash
uv sync
```

### 2. Playwright 브라우저 설치

```bash
uv run playwright install chromium
```

### 3. 환경 변수 설정

`.env` 파일에 다음을 추가:
```
GEMINI_API_KEY_JY=your_gemini_api_key_here
```

## 실행 방법

```bash
uv run python nvidia_stock_predictor.py
```

## 시스템 구조

### 1단계: 검색어 생성
- LLM이 NVIDIA 주가 예측에 유용한 검색어 5-10개 생성
- JsonOutputParser로 구조화된 출력

### 2단계: 뉴스 수집
- NewsAPI를 통해 최근 30일 뉴스 수집
- URL 기반 중복 제거

### 3단계: 뉴스 필터링
- LLM이 주가 예측에 유용한 뉴스만 선별 (최대 15개)
- 광고성, 무관한 뉴스 제외

### 4단계: 상세 내용 크롤링
- Playwright로 선택된 뉴스의 전체 내용 수집
- 접근 불가 사이트는 제목/설명으로 대체

### 5단계: 주가 예측
- 수집된 뉴스를 바탕으로 장기 주가 전망 분석
- 긍정/부정 요인, 신뢰도, 요약 제공

## 출력

- 콘솔에 예측 결과 출력
- JSON 파일로 전체 분석 결과 저장 (`nvidia_prediction_YYYYMMDD_HHMMSS.json`)

## 주요 특징

- ✅ JsonOutputParser를 사용한 구조화된 LLM 응답
- ✅ 5단계 파이프라인 자동 실행
- ✅ 에러 처리 및 로깅
- ✅ 중복 제거 및 토큰 최적화
- ✅ Gemini 2.5 Flash 사용으로 빠른 응답







