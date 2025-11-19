import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from newsapi import NewsApiClient
from playwright.sync_api import sync_playwright
from google import genai
from pydantic import BaseModel, Field

# .env 파일 로드
load_dotenv()

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_JY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_JY가 .env 파일에 설정되지 않았습니다.")

# Gemini 클라이언트 초기화
client = genai.Client(api_key=GEMINI_API_KEY)

# NewsAPI 클라이언트
NEWS_API_KEY = 'dcc50abaec994513939365149361eee1'
news_api = NewsApiClient(api_key=NEWS_API_KEY)

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

# 신뢰도 임계치
CONFIDENCE_THRESHOLD = 60


# ============================================================================
# Pydantic 모델 정의 (구조화된 출력용)
# ============================================================================

class SearchKeywords(BaseModel):
    """키워드 에이전트 출력"""
    keywords: List[str] = Field(description="검색 키워드 리스트 (10개)")
    reasoning: str = Field(description="키워드 선택 이유")


class NewsPack(BaseModel):
    """뉴스팩 구조"""
    pack_id: str = Field(description="뉴스팩 ID (예: pack_001)")
    event_type: str = Field(description="이벤트 유형: earnings/policy/product/supply/partnership/general")
    summary: str = Field(description="핵심 내용 요약 (3-5문장)")
    relevance_score: float = Field(description="NVIDIA 관련성 점수 (0.0-1.0)")
    article_indices: List[int] = Field(description="포함된 기사 인덱스")


class NewsPacks(BaseModel):
    """병합 에이전트 출력"""
    packs: List[NewsPack] = Field(description="뉴스팩 리스트 (5-10개)")


class Evidence(BaseModel):
    """근거 정보"""
    event_type: str = Field(description="이벤트 유형")
    sentence: str = Field(description="근거 문장")


class EventScores(BaseModel):
    """이벤트별 점수 - Dict 대신 명시적 필드 사용"""
    earnings: float = Field(default=0.0, description="실적 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    policy: float = Field(default=0.0, description="정책/규제 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    product: float = Field(default=0.0, description="제품 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    supply: float = Field(default=0.0, description="공급망 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    partnership: float = Field(default=0.0, description="파트너십 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    

class SentimentAnalysis(BaseModel):
    """분석 에이전트 출력"""
    overall_sentiment: float = Field(description="전체 감성 점수 (-3.0 ~ +3.0)", ge=-3.0, le=3.0)
    event_scores: EventScores = Field(description="이벤트별 점수")
    evidences: List[Evidence] = Field(description="근거 리스트 (최소 3개)")
    optimal_timeframe: int = Field(description="최적 예측 기간 (1-14일)", ge=1, le=14)
    direction: str = Field(description="예측 방향: Up/Down/Hold 중 하나")


class ValidationResult(BaseModel):
    """검증 에이전트 출력"""
    confidence: int = Field(description="최종 신뢰도 (0-100)", ge=0, le=100)
    is_valid: bool = Field(description="임계치 통과 여부")
    validation_notes: List[str] = Field(description="검증 사항")
    contra_arguments: List[str] = Field(description="반대 근거")


# ============================================================================
# 에이전트 1: 키워드 에이전트
# ============================================================================

class KeywordAgent:
    """검색 키워드 생성 에이전트 - Gemini 구조화된 출력 사용"""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.model = "gemini-2.5-flash"
        
        # 폴백 기본 키워드
        self.default_keywords = [
            "NVIDIA earnings report",
            "NVDA stock forecast",
            "NVIDIA AI chip demand",
            "NVIDIA data center revenue",
            "NVIDIA China export ban",
            "Jensen Huang NVIDIA",
            "NVIDIA Blackwell GPU",
            "NVIDIA quarterly guidance",
            "NVIDIA partnership news",
            "NVIDIA supply chain"
        ]
    
    def generate_keywords(self) -> List[str]:
        """카테고리별 검색 키워드 생성"""
        print("\n" + "="*80)
        print("[에이전트 1] 키워드 생성")
        print("="*80)
        
        try:
            prompt = f"""당신은 금융 뉴스 검색 전문가입니다. NVIDIA(NVDA) 주가 예측을 위한 검색 키워드 10개를 생성하세요.

현재 날짜: {datetime.now().strftime("%Y-%m-%d")}

카테고리별로 생성:
- 제품/기술 (2개): AI chip, GPU, Hopper, Blackwell
- 정책/규제 (2개): China, export control, regulation
- 재무 (2개): earnings, revenue, guidance
- 파트너십 (2개): partnership, deal, customer
- 공급망 (2개): TSMC, supply chain, manufacturing

각 키워드는 "NVIDIA" 또는 "NVDA"를 포함하고 영어로 작성하세요.
검색에 효과적인 구체적인 구문을 사용하세요."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': SearchKeywords,
                }
            )
            
            # 구조화된 출력 파싱
            result: SearchKeywords = response.parsed
            
            if result and result.keywords and len(result.keywords) >= 5:
                keywords = result.keywords[:10]  # 최대 10개
                
                print(f"\n생성된 검색어 ({len(keywords)}개):")
                for i, kw in enumerate(keywords, 1):
                    print(f"  {i}. {kw}")
                print(f"\n생성 이유: {result.reasoning[:200]}...")
                
                return keywords
            else:
                raise Exception("키워드 수 부족")
            
        except Exception as e:
            print(f"\n⚠️ 키워드 생성 실패: {e}")
            print("기본 키워드를 사용합니다.")
            
            for i, kw in enumerate(self.default_keywords, 1):
                print(f"  {i}. {kw}")
            
            return self.default_keywords


# ============================================================================
# 에이전트 2: 뉴스 수집 에이전트
# ============================================================================

class CrawlerAgent:
    """뉴스 수집 및 크롤링 에이전트 - 다중 소스, 중복 제거, 엔티티 링크"""
    
    def __init__(self, news_api, genai_client: genai.Client):
        self.news_api = news_api
        self.client = genai_client
        self.model = "gemini-2.5-flash"
    
    def fetch_news(self, keywords: List[str], days_back: int = 30) -> List[Dict[str, Any]]:
        """NewsAPI로 뉴스 수집"""
        print("\n" + "="*80)
        print("[에이전트 2] 뉴스 수집")
        print("="*80)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        all_articles = []
        seen_urls = set()
        
        for keyword in keywords:
            try:
                print(f"\n검색 중: '{keyword}'")
                response = self.news_api.get_everything(
                    q=keyword,
                    from_param=start_date,
                    to=end_date,
                    language='en',
                    sort_by='relevancy',
                    page_size=15  # 키워드당 15개
                )
                
                for article in response.get('articles', []):
                    url = article.get('url')
                    title = article.get('title', '')
                    description = article.get('description', '')
                    
                    # 중복 제거
                    if url and url not in seen_urls:
                        # NVIDIA 관련성 LLM으로 확인
                        if self._is_nvidia_related(title, description):
                            seen_urls.add(url)
                            all_articles.append({
                                'title': title,
                                'description': description,
                                'url': url,
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', ''),
                                'content': article.get('content', '')
                            })
                            print(f"  ✓ {title[:60]}...")
                
            except Exception as e:
                print(f"  ✗ 검색 실패: {e}")
                continue
        
        # 날짜순 정렬 (최신순)
        all_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        print(f"\n총 {len(all_articles)}개의 NVIDIA 관련 뉴스 수집 완료")
        return all_articles
    
    def _is_nvidia_related(self, title: str, description: str) -> bool:
        """LLM을 사용한 NVIDIA 관련성 확인"""
        # 빈 텍스트는 바로 거부
        if not title and not description:
            return False
        
        # 간단한 키워드 사전 필터 (API 호출 최소화)
        text = f"{title} {description}".lower()
        if 'nvidia' in text or 'nvda' in text:
            return True
        
        # 애매한 경우만 LLM에 질의 (API 호출 절약)
        try:
            prompt = f"""다음 뉴스가 NVIDIA Corporation (NVDA) 주가와 관련이 있는지 판단하세요.

제목: {title}
설명: {description[:200]}

NVIDIA 관련이면 "YES", 아니면 "NO"만 답하세요."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            answer = response.text.strip().upper()
            return 'YES' in answer
            
        except:
            # LLM 실패 시 보수적으로 포함
            return True
    
    def crawl_articles(self, articles: List[Dict[str, Any]], max_crawl: int = 20) -> List[Dict[str, Any]]:
        """Playwright로 기사 본문 크롤링"""
        print("\n기사 본문 크롤링 중...")
        
        crawled = []
        for idx, article in enumerate(articles[:max_crawl]):
            print(f"  [{idx+1}/{min(max_crawl, len(articles))}] {article['title'][:50]}...")
            
            content = self._crawl_single_article(article['url'])
            crawled.append({
                **article,
                'full_content': content if content else article.get('description', '')
            })
        
        print(f"✓ {len(crawled)}개 기사 크롤링 완료")
        return crawled
    
    def _crawl_single_article(self, url: str) -> Optional[str]:
        """단일 기사 크롤링"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=10000)
                page.wait_for_timeout(1500)
                
                # 본문 추출
                content = ""
                selectors = ['article', '[role="article"]', '.article-content', 'main', 'body']
                
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            content = element.inner_text()
                            if len(content) > 200:  # 충분한 내용이 있으면
                                break
                    except:
                        continue
                
                browser.close()
                return content[:3000]  # 토큰 제한
                
        except Exception as e:
            return None


# ============================================================================
# 에이전트 3: 병합·정제 에이전트
# ============================================================================

class MergeAgent:
    """뉴스 병합 및 정제 에이전트 - Gemini 구조화된 출력 사용"""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.model = "gemini-2.0-flash-exp"
    
    def merge_and_refine(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스를 뉴스팩으로 병합·정제"""
        print("\n" + "="*80)
        print("[에이전트 3] 뉴스 병합 및 정제")
        print("="*80)
        
        if not articles:
            return []
        
        # 기사가 너무 많으면 상위만 선택
        articles = articles[:20]
        
        # 기사 목록 텍스트 생성
        news_list = ""
        for idx, article in enumerate(articles):
            news_list += f"[{idx}] {article['title']}\n"
            news_list += f"출처: {article['source']} | {article['publishedAt'][:10]}\n"
            content = article.get('full_content', article.get('description', ''))[:300]
            news_list += f"{content}...\n\n"
        
        try:
            prompt = f"""NVIDIA 관련 뉴스들을 분석하고 이벤트별로 그룹화하세요.

뉴스 목록:
{news_list[:10000]}

임무:
1. 중복/재탕 기사를 같은 이벤트로 묶기
2. 이벤트 유형별 분류
3. 각 뉴스팩마다 핵심 내용 3-5문장으로 요약
4. NVIDIA 관련성 점수 (0.0~1.0) 부여

이벤트 유형:
- earnings: 실적, 매출, EPS
- policy: 규제, 정책, 수출통제
- product: 신제품, GPU, 칩
- supply: 공급망, 제조
- partnership: 파트너십, 협업
- general: 기타

5~8개의 뉴스팩을 생성하세요."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': NewsPacks,
                }
            )
            
            # 구조화된 출력 파싱
            result: NewsPacks = response.parsed
            
            if result and result.packs:
                news_packs = [pack.model_dump() for pack in result.packs]
                
                print(f"\n✓ {len(news_packs)}개의 뉴스팩 생성:")
                for pack in news_packs:
                    print(f"  - {pack['event_type'].upper()}: {pack['summary'][:60]}... "
                          f"(관련성: {pack['relevance_score']:.2f})")
                return news_packs
            else:
                raise Exception("뉴스팩 생성 실패")
            
        except Exception as e:
            print(f"⚠️ 병합 실패: {e}")
            print("각 기사를 개별 뉴스팩으로 처리합니다.")
            
            # 폴백: 각 기사를 개별 뉴스팩으로
            fallback_packs = []
            for idx, article in enumerate(articles[:10]):
                fallback_packs.append({
                    'pack_id': f'pack_{idx:03d}',
                    'event_type': 'general',
                    'summary': article['title'] + ". " + article.get('description', '')[:200],
                    'relevance_score': 0.7,
                    'article_indices': [idx]
                })
            
            return fallback_packs


# ============================================================================
# 에이전트 4: 분석 에이전트
# ============================================================================

class AnalysisAgent:
    """감성 및 이벤트 분석 에이전트 - Gemini 구조화된 출력 사용"""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.model = "gemini-2.0-flash-exp"
        
        # 이벤트별 가중치 및 예측 기간
        self.event_settings = {
            'earnings': {'weight': 3.0, 'days': (3, 7)},
            'guidance': {'weight': 2.5, 'days': (5, 10)},
            'policy': {'weight': 2.0, 'days': (7, 14)},
            'product': {'weight': 1.5, 'days': (5, 10)},
            'supply': {'weight': 1.0, 'days': (7, 14)},
            'partnership': {'weight': 1.2, 'days': (3, 7)},
            'general': {'weight': 0.5, 'days': (5, 10)}
        }
    
    def analyze(self, news_packs: List[Dict[str, Any]], articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """감성 분석 및 이벤트 추출"""
        print("\n" + "="*80)
        print("[에이전트 4] 감성 및 이벤트 분석")
        print("="*80)
        
        # 뉴스팩 컨텍스트 생성
        context = ""
        for pack in news_packs[:10]:
            context += f"\n[{pack['event_type'].upper()}] 관련성: {pack.get('relevance_score', 0.5):.2f}\n"
            context += f"{pack['summary'][:400]}\n"
            context += "-" * 60 + "\n"
        
        try:
            prompt = f"""당신은 NVIDIA 주가 분석 전문가입니다. 뉴스를 분석하고 주가 예측을 제공하세요.

현재 날짜: {datetime.now().strftime("%Y-%m-%d")}

분석 대상 뉴스:
{context[:8000]}

다음을 분석하세요:

1. overall_sentiment: 전체 감성 점수 (-3.0 ~ +3.0 사이의 실수)
   - 실적 호조, 신제품 성공 = 긍정 (+2 ~ +3)
   - 실적 미달, 규제 강화 = 부정 (-2 ~ -3)
   - 중립 = 0

2. event_scores: 각 이벤트별 점수를 개별 필드로
   - earnings: 실적 관련 점수 (-3.0 ~ +3.0)
   - policy: 정책/규제 점수 (-3.0 ~ +3.0)
   - product: 제품 관련 점수 (-3.0 ~ +3.0)
   - supply: 공급망 점수 (-3.0 ~ +3.0)
   - partnership: 파트너십 점수 (-3.0 ~ +3.0)

3. evidences: 근거 리스트 (최소 3개)
   - 각 근거는 event_type과 sentence 포함
   - event_type: earnings/policy/product/supply/partnership/general

4. optimal_timeframe: 예측 기간 (1~14 사이의 정수)
   - earnings: 3-7일
   - policy: 7-14일
   - 기타: 5-10일

5. direction: "Up", "Down", "Hold" 중 하나 (정확히 이 문자열)

주의: 모든 필드를 반드시 채워야 합니다. 관련 없는 이벤트는 0.0으로 설정하세요."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': SentimentAnalysis,
                }
            )
            
            # 구조화된 출력 파싱
            result: SentimentAnalysis = response.parsed
            
            if result:
                # event_scores를 딕셔너리로 변환
                event_scores_dict = result.event_scores.model_dump()
                
                result_dict = {
                    'overall_sentiment': result.overall_sentiment,
                    'event_scores': event_scores_dict,
                    'evidences': [e.model_dump() for e in result.evidences],
                    'optimal_timeframe': result.optimal_timeframe,
                    'direction': result.direction
                }
                
                print(f"\n✓ 분석 성공")
                print(f"전체 감성: {result.overall_sentiment:+.1f}")
                print(f"이벤트별 점수:")
                for event, score in event_scores_dict.items():
                    if score != 0:
                        print(f"  - {event}: {score:+.1f}")
                print(f"최적 예측 기간: {result.optimal_timeframe}일")
                print(f"예측 방향: {result.direction}")
                
                return result_dict
            else:
                raise Exception("response.parsed가 None")
            
        except Exception as e:
            print(f"⚠️ 분석 실패: {e}")
            print(f"에러 타입: {type(e).__name__}")
            import traceback
            print(f"상세 에러:\n{traceback.format_exc()}")
            print("기본 분석을 사용합니다.")
            
            # 폴백: 단순 추정
            sentiment = self._simple_sentiment(news_packs)
            
            return {
                'overall_sentiment': sentiment,
                'event_scores': {'general': sentiment},
                'evidences': [{'event_type': 'general', 'sentence': '자동 분석 실패, 단순 추정'}],
                'optimal_timeframe': 7,
                'direction': 'Up' if sentiment > 0 else ('Down' if sentiment < 0 else 'Hold')
            }
    
    def _simple_sentiment(self, news_packs: List[Dict[str, Any]]) -> float:
        """간단한 감성 추정 (폴백용)"""
        if not news_packs:
            return 0.0
        
        avg_relevance = sum(pack.get('relevance_score', 0.5) for pack in news_packs) / len(news_packs)
        return (avg_relevance - 0.5) * 2  # -1 ~ 1 범위


# ============================================================================
# 에이전트 5: 검증 에이전트
# ============================================================================

class ValidationAgent:
    """검증 에이전트 - 사실 검증, 일관성 체크, Devil's Advocate"""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.model = "gemini-2.0-flash-exp"
    
    def validate(self, 
                 analysis: Dict[str, Any],
                 news_packs: List[Dict[str, Any]],
                 articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """분석 결과 검증 및 신뢰도 계산"""
        print("\n" + "="*80)
        print("[에이전트 5] 결과 검증")
        print("="*80)
        
        # 1. 출처 신뢰도 계산
        source_score = self._calculate_source_quality(articles)
        
        # 2. 일관성 점수 계산
        consistency_score = self._calculate_consistency(news_packs)
        
        # 3. 최신성 점수
        recency_score = self._calculate_recency(articles)
        
        # 4. Devil's Advocate - 반대 근거 찾기
        contra_args = self._find_counter_arguments(analysis, news_packs)
        
        # 5. 최종 신뢰도 계산
        confidence = int(
            source_score * 40 +
            consistency_score * 30 +
            recency_score * 20 +
            min(abs(analysis.get('overall_sentiment', 0)) * 3.33, 10)  # 감성 강도 10%
        )
        
        is_valid = confidence >= CONFIDENCE_THRESHOLD
        
        print(f"\n신뢰도 분석:")
        print(f"  - 출처 품질: {source_score:.1%} (가중치 40%)")
        print(f"  - 일관성: {consistency_score:.1%} (가중치 30%)")
        print(f"  - 최신성: {recency_score:.1%} (가중치 20%)")
        print(f"  - 감성 강도: {abs(analysis.get('overall_sentiment', 0)):.1f}")
        print(f"\n최종 신뢰도: {confidence}%")
        print(f"임계치 통과: {'✓ YES' if is_valid else '✗ NO (예측 보류)'}")
        
        if contra_args:
            print(f"\n반대 근거:")
            for arg in contra_args:
                print(f"  ⚠️  {arg}")
        
        validation_notes = [
            f"출처 신뢰도: {source_score:.0%}",
            f"일관성 점수: {consistency_score:.0%}",
            f"최신성: {recency_score:.0%}"
        ]
        
        return {
            'confidence': confidence,
            'is_valid': is_valid,
            'validation_notes': validation_notes,
            'contra_arguments': contra_args
        }
    
    def _calculate_source_quality(self, articles: List[Dict[str, Any]]) -> float:
        """출처 신뢰도 점수"""
        if not articles:
            return 0.0
        
        scores = []
        for article in articles:
            source = article.get('source', '').lower()
            score = 0.5  # 기본값
            for trusted, weight in TRUSTED_SOURCES.items():
                if trusted in source:
                    score = weight
                    break
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _calculate_consistency(self, news_packs: List[Dict[str, Any]]) -> float:
        """일관성 점수 - 여러 뉴스팩이 같은 방향을 가리키는지"""
        if len(news_packs) < 2:
            return 0.6  # 뉴스 적으면 중간 점수
        
        # 이벤트 타입 다양성 (좋음)
        event_types = set(pack.get('event_type', '') for pack in news_packs)
        diversity = len(event_types) / len(news_packs)
        
        # 관련성 점수 평균
        relevance = sum(pack.get('relevance_score', 0) for pack in news_packs) / len(news_packs)
        
        return (diversity * 0.3 + relevance * 0.7)
    
    def _calculate_recency(self, articles: List[Dict[str, Any]]) -> float:
        """최신성 점수"""
        if not articles:
            return 0.0
        
        now = datetime.now()
        recent_count = 0
        
        for article in articles:
            pub_date = article.get('publishedAt', '')
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                days_ago = (now - pub_dt).days
                if days_ago <= 7:  # 1주일 이내
                    recent_count += 1
            except:
                continue
        
        return recent_count / len(articles)
    
    def _find_counter_arguments(self, analysis: Dict[str, Any], news_packs: List[Dict[str, Any]]) -> List[str]:
        """Devil's Advocate - 반대 근거 찾기"""
        
        summary = "\n".join(pack.get('summary', '')[:200] for pack in news_packs[:3])
        
        prompt = f"""당신은 비판적 심사관입니다. 다음 분석 결과에 대한 반대 근거를 찾으세요.

**분석 결과**:
- 예측 방향: {analysis.get('direction', 'Unknown')}
- 감성 점수: {analysis.get('overall_sentiment', 0)}

**뉴스 요약**:
{summary}

**질문**:
1. 간과된 부정적 요인이 있는가?
2. 과대평가된 긍정적 요인이 있는가?
3. 시장 맥락에서 놓친 리스크는?

간단히 3개 이하로 반대 근거를 나열하세요. 없으면 "없음"이라고만 하세요.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            text = response.text
            
            if "없음" in text or "None" in text:
                return []
            
            # 줄바꿈으로 분리
            args = [line.strip('- ').strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 10]
            return args[:3]
            
        except:
            return []


# ============================================================================
# 오케스트레이터
# ============================================================================

class Orchestrator:
    """멀티-에이전트 오케스트레이터 - 전체 워크플로우 관리"""
    
    def __init__(self):
        self.keyword_agent = KeywordAgent(client)
        self.crawler_agent = CrawlerAgent(news_api, client)  # client 전달
        self.merge_agent = MergeAgent(client)
        self.analysis_agent = AnalysisAgent(client)
        self.validation_agent = ValidationAgent(client)
    
    def run(self, user_query: str = "엔비디아 주가가 오를까 내릴까?") -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        
        print("\n" + "="*80)
        print("🤖 NVIDIA 주가 예측 멀티-에이전트 시스템")
        print("="*80)
        print(f"\n사용자 질의: \"{user_query}\"")
        print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1단계: 키워드 생성
            keywords = self.keyword_agent.generate_keywords()
            
            # 2단계: 뉴스 수집
            articles = self.crawler_agent.fetch_news(keywords, days_back=30)
            
            if not articles:
                return self._create_failure_result("수집된 뉴스가 없습니다.")
            
            # 본문 크롤링
            crawled_articles = self.crawler_agent.crawl_articles(articles, max_crawl=20)
            
            # 3단계: 뉴스 병합 및 정제
            news_packs = self.merge_agent.merge_and_refine(crawled_articles)
            
            # 4단계: 감성 및 이벤트 분석
            analysis = self.analysis_agent.analyze(news_packs, crawled_articles)
            
            # 5단계: 검증
            validation = self.validation_agent.validate(analysis, news_packs, crawled_articles)
            
            # 최종 결과 생성
            final_result = self._create_final_result(
                analysis, validation, news_packs, crawled_articles, keywords
            )
            
            return final_result
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return self._create_failure_result(f"시스템 오류: {str(e)}")
    
    def _create_final_result(self, analysis, validation, news_packs, articles, keywords) -> Dict[str, Any]:
        """최종 예측 결과 생성"""
        
        # 긍정/부정 요인 추출
        positive_factors = []
        negative_factors = []
        
        for evidence in analysis.get('evidences', []):
            event = evidence.get('event_type', evidence.get('event', ''))  # 두 형식 모두 지원
            sentence = evidence.get('sentence', '')
            score = analysis.get('event_scores', {}).get(event, 0)
            
            if score > 0:
                positive_factors.append(f"[{event}] {sentence}")
            elif score < 0:
                negative_factors.append(f"[{event}] {sentence}")
        
        # 요약 생성
        summary_parts = []
        for pack in news_packs[:3]:
            summary_parts.append(f"- {pack['event_type'].upper()}: {pack['summary'][:100]}...")
        
        summary = "\n".join(summary_parts)
        
        is_valid = validation['is_valid']
        reason_if_invalid = "" if is_valid else f"신뢰도 {validation['confidence']}%로 임계치 {CONFIDENCE_THRESHOLD}% 미달"
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user_query': "엔비디아 주가 예측",
            'keywords_used': keywords,
            'total_articles': len(articles),
            'news_packs': len(news_packs),
            'prediction': {
                'direction': analysis.get('direction', 'Hold'),
                'confidence': validation['confidence'],
                'timeframe': analysis.get('optimal_timeframe', 7),
                'positive_factors': positive_factors[:5],
                'negative_factors': negative_factors[:5],
                'summary': summary,
                'is_valid': is_valid,
                'reason_if_invalid': reason_if_invalid
            },
            'analysis_details': {
                'overall_sentiment': analysis.get('overall_sentiment', 0),
                'event_scores': analysis.get('event_scores', {}),
                'validation_notes': validation.get('validation_notes', []),
                'contra_arguments': validation.get('contra_arguments', [])
            },
            'news_packs': news_packs,
            'raw_articles': articles[:10]  # 상위 10개만 저장
        }
    
    def _create_failure_result(self, reason: str) -> Dict[str, Any]:
        """실패 결과 생성"""
        return {
            'timestamp': datetime.now().isoformat(),
            'prediction': {
                'direction': 'Hold',
                'confidence': 0,
                'timeframe': 0,
                'positive_factors': [],
                'negative_factors': [],
                'summary': reason,
                'is_valid': False,
                'reason_if_invalid': reason
            }
        }


# ============================================================================
# 결과 출력 함수
# ============================================================================

def print_final_result(result: Dict[str, Any]):
    """최종 결과를 보기 좋게 출력"""
    
    print("\n\n")
    print("="*80)
    print("📊 최종 예측 결과")
    print("="*80)
    
    pred = result['prediction']
    
    if not pred['is_valid']:
        print("\n⚠️  예측 보류")
        print(f"사유: {pred['reason_if_invalid']}")
        print("\n더 많은 데이터가 필요하거나 시장 불확실성이 높습니다.")
        return
    
    # 방향 이모지
    direction_emoji = {
        'Up': '📈 상승',
        'Down': '📉 하락',
        'Hold': '➡️  보합'
    }
    
    print(f"\n방향: {direction_emoji.get(pred['direction'], pred['direction'])}")
    print(f"신뢰도: {pred['confidence']}%")
    print(f"권장 예측 기간: {pred['timeframe']}일")
    
    if pred['positive_factors']:
        print(f"\n✅ 긍정적 요인 ({len(pred['positive_factors'])}개):")
        for factor in pred['positive_factors']:
            print(f"   {factor}")
    
    if pred['negative_factors']:
        print(f"\n❌ 부정적 요인 ({len(pred['negative_factors'])}개):")
        for factor in pred['negative_factors']:
            print(f"   {factor}")
    
    print(f"\n📝 분석 요약:")
    print(pred['summary'])
    
    # 검증 정보
    details = result.get('analysis_details', {})
    if details.get('validation_notes'):
        print(f"\n🔍 검증 정보:")
        for note in details['validation_notes']:
            print(f"   • {note}")
    
    if details.get('contra_arguments'):
        print(f"\n⚠️  반대 의견 (Devil's Advocate):")
        for arg in details['contra_arguments']:
            print(f"   • {arg}")
    
    print("\n" + "="*80)


# ============================================================================
# 메인 함수
# ============================================================================

def main():
    """메인 실행 함수"""
    
    # 오케스트레이터 초기화 및 실행
    orchestrator = Orchestrator()
    result = orchestrator.run()
    
    # 결과 출력
    print_final_result(result)
    
    # JSON 파일로 저장
    output_file = f"nvidia_multi_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 전체 결과가 {output_file}에 저장되었습니다.")


if __name__ == "__main__":
    main()

