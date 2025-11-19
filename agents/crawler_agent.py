"""
뉴스 수집 및 크롤링 에이전트 모듈

NewsAPI를 통해 NVIDIA 관련 뉴스를 수집하고, Playwright를 사용하여
기사 본문을 크롤링합니다. LLM을 활용한 관련성 필터링과 중복 제거 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from playwright.sync_api import sync_playwright
from google import genai


class CrawlerAgent:
    """
    뉴스 수집 및 크롤링 에이전트
    
    NewsAPI를 통해 키워드 기반으로 뉴스를 수집하고, Playwright를 사용하여
    기사 본문을 크롤링합니다. LLM을 활용하여 NVIDIA 관련성을 검증하고
    중복 기사를 제거합니다.
    
    Attributes:
        news_api: NewsAPI 클라이언트
        client: Gemini API 클라이언트 (관련성 검증용)
        model: 사용할 Gemini 모델명
    """
    
    def __init__(self, news_api: NewsApiClient, genai_client: genai.Client) -> None:
        """
        CrawlerAgent 초기화
        
        Args:
            news_api: NewsAPI 클라이언트 인스턴스
            genai_client: Gemini API 클라이언트 인스턴스
        """
        self.news_api = news_api
        self.client = genai_client
        self.model = "gemini-2.5-flash-preview-09-2025"
    
    def fetch_news(self, keywords: List[str], days_back: int = 30) -> List[Dict[str, Any]]:
        """
        NewsAPI를 사용하여 뉴스 수집
        
        주어진 키워드 리스트를 사용하여 NewsAPI에서 뉴스를 검색합니다.
        각 키워드당 최대 15개의 기사를 수집하며, LLM을 사용하여 NVIDIA 관련성을 검증합니다.
        중복 URL은 자동으로 제거됩니다.
        
        Args:
            keywords: 검색 키워드 리스트
            days_back: 검색할 과거 일수 (기본값: 30일)
        
        Returns:
            List[Dict[str, Any]]: 수집된 뉴스 기사 리스트
                각 기사는 title, description, url, publishedAt, source, content 필드 포함
        """
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
        """
        LLM을 사용한 NVIDIA 관련성 확인
        
        기사의 제목과 설명을 분석하여 NVIDIA 주가와 관련이 있는지 판단합니다.
        먼저 간단한 키워드 필터를 적용하여 API 호출을 최소화하고,
        애매한 경우에만 LLM에 질의합니다.
        
        Args:
            title: 기사 제목
            description: 기사 설명
        
        Returns:
            bool: NVIDIA 관련 여부 (True: 관련 있음, False: 관련 없음)
        """
        # 빈 텍스트는 바로 거부
        if not title and not description:
            return False
        
        # 간단한 키워드 사전 필터 (API 호출 최소화)
        # NVIDIA 또는 NVDA가 명시적으로 언급되면 즉시 승인
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
        """
        Playwright를 사용하여 기사 본문 크롤링
        
        수집된 기사의 URL을 방문하여 전체 본문을 크롤링합니다.
        크롤링에 실패한 경우 기사 설명(description)을 대체 텍스트로 사용합니다.
        
        Args:
            articles: 크롤링할 기사 리스트
            max_crawl: 최대 크롤링 기사 수 (기본값: 20)
        
        Returns:
            List[Dict[str, Any]]: 본문이 추가된 기사 리스트
                각 기사에 'full_content' 필드가 추가됨
        """
        print("\n기사 본문 크롤링 중...")
        
        crawled = []
        for idx, article in enumerate(articles[:max_crawl]):
            print(f"  [{idx+1}/{min(max_crawl, len(articles))}] {article['title'][:50]}...")
            
            # 단일 기사 크롤링 시도
            content = self._crawl_single_article(article['url'])
            
            # 크롤링 성공 시 본문 사용, 실패 시 설명 사용
            crawled.append({
                **article,
                'full_content': content if content else article.get('description', '')
            })
        
        print(f"✓ {len(crawled)}개 기사 크롤링 완료")
        return crawled
    
    def _crawl_single_article(self, url: str) -> Optional[str]:
        """
        단일 기사 크롤링
        
        Playwright를 사용하여 단일 기사의 본문을 추출합니다.
        여러 일반적인 HTML 셀렉터를 시도하여 본문을 찾습니다.
        
        Args:
            url: 크롤링할 기사 URL
        
        Returns:
            Optional[str]: 추출된 본문 텍스트 (최대 3000자) 또는 None (실패 시)
        """
        try:
            with sync_playwright() as p:
                # 헤드리스 브라우저 실행
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # 페이지 로드 (10초 타임아웃)
                page.goto(url, timeout=10000)
                page.wait_for_timeout(1500)  # 동적 콘텐츠 로딩 대기
                
                # 본문 추출 - 여러 셀렉터 시도
                content = ""
                # 일반적인 기사 본문 셀렉터 리스트 (우선순위 순)
                selectors = ['article', '[role="article"]', '.article-content', 'main', 'body']
                
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            content = element.inner_text()
                            # 충분한 내용이 있으면 (200자 이상) 중단
                            if len(content) > 200:
                                break
                    except:
                        continue
                
                browser.close()
                
                # 토큰 제한을 위해 최대 3000자로 제한
                return content[:3000] if content else None
                
        except Exception as e:
            # 크롤링 실패 시 None 반환 (폴백으로 description 사용)
            return None
