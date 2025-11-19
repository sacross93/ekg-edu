import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
from newsapi import NewsApiClient
from playwright.sync_api import sync_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# .env 파일 로드
load_dotenv()

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_JY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_JY가 .env 파일에 설정되지 않았습니다.")

# LLM 초기화
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

# NewsAPI 클라이언트 초기화
NEWS_API_KEY = 'dcc50abaec994513939365149361eee1'
news_api = NewsApiClient(api_key=NEWS_API_KEY)


# Pydantic 모델 정의
class SearchKeywords(BaseModel):
    keywords: List[str] = Field(description="NVIDIA 주가 예측에 유용한 검색어 리스트")


class NewsIndices(BaseModel):
    selected_indices: List[int] = Field(description="주가 예측에 유용한 뉴스의 인덱스 리스트")
    reasoning: str = Field(description="선택한 이유")


class StockPrediction(BaseModel):
    prediction: str = Field(description="주가 예측 (상승/하락/보합)")
    confidence: int = Field(description="신뢰도 (0-100)")
    positive_factors: List[str] = Field(description="긍정적 요인들")
    negative_factors: List[str] = Field(description="부정적 요인들")
    summary: str = Field(description="전체 분석 요약")
    timeframe: str = Field(description="예측 기간 (단기/중기/장기)")


# 1단계: LLM이 검색어 생성
def generate_search_keywords() -> List[str]:
    """LLM이 NVIDIA 주가 예측을 위한 검색어를 생성합니다."""
    print("\n[1단계] 검색어 생성 중...")
    
    parser = JsonOutputParser(pydantic_object=SearchKeywords)
    
    prompt = PromptTemplate(
        template="""당신은 금융 분석 전문가입니다. NVIDIA 주가 예측을 위해 뉴스 검색에 사용할 최적의 검색어를 생성하세요.

현재 날짜: {current_date}

다음을 고려하여 5-10개의 검색어를 생성하세요:
1. NVIDIA의 주요 사업 분야 (GPU, AI, 데이터센터)
2. 경쟁사 및 시장 동향
3. 주요 인물 (CEO, 임원)
4. 재무 실적 및 전망
5. 기술 혁신 및 제품 출시
6. 규제 및 정책 변화

{format_instructions}
""",
        input_variables=["current_date"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({"current_date": datetime.now().strftime("%Y-%m-%d")})
    
    print(f"생성된 검색어: {result['keywords']}")
    return result['keywords']


# 2단계: NewsAPI로 뉴스 수집
def fetch_news(keywords: List[str]) -> List[Dict[str, Any]]:
    """생성된 검색어로 뉴스를 수집하고 중복을 제거합니다."""
    print("\n[2단계] 뉴스 수집 중...")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    all_articles = []
    seen_urls = set()
    
    for keyword in keywords:
        try:
            print(f"  - '{keyword}' 검색 중...")
            response = news_api.get_everything(
                q=keyword,
                from_param=start_date,
                to=end_date,
                language='en',
                sort_by='relevancy',
                page_size=10
            )
            
            for article in response.get('articles', []):
                url = article.get('url')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': url,
                        'publishedAt': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', '')
                    })
        except Exception as e:
            print(f"  ! '{keyword}' 검색 실패: {e}")
            continue
    
    print(f"총 {len(all_articles)}개의 고유한 뉴스를 수집했습니다.")
    return all_articles


# 3단계: LLM이 유용한 뉴스 필터링
def filter_news(articles: List[Dict[str, Any]]) -> List[int]:
    """LLM이 주가 예측에 유용한 뉴스의 인덱스만 선택합니다."""
    print("\n[3단계] 뉴스 필터링 중...")
    
    parser = JsonOutputParser(pydantic_object=NewsIndices)
    
    # 뉴스 목록을 텍스트로 변환
    news_list = ""
    for idx, article in enumerate(articles):
        news_list += f"[{idx}] {article['title']}\n"
        news_list += f"    {article['description'][:200] if article['description'] else '설명 없음'}...\n"
        news_list += f"    출처: {article['source']} | 날짜: {article['publishedAt']}\n\n"
    
    prompt = PromptTemplate(
        template="""당신은 금융 분석 전문가입니다. 다음 뉴스 목록에서 NVIDIA 주가 예측에 실제로 도움이 될 뉴스들만 선택하세요.

현재 날짜: {current_date}

뉴스 목록:
{news_list}

선택 기준:
1. NVIDIA의 실적, 제품, 기술에 직접적인 영향
2. AI/GPU 시장 동향 및 경쟁 상황
3. 주요 고객사 및 파트너십 소식
4. 규제, 정책 변화
5. 애널리스트 전망 및 주가 분석

광고성, 중복, 관련성 낮은 뉴스는 제외하세요.
최대 15개까지 선택하세요.

{format_instructions}
""",
        input_variables=["current_date", "news_list"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "news_list": news_list[:15000]  # 토큰 제한 고려
    })
    
    selected_indices = result['selected_indices']
    print(f"{len(selected_indices)}개의 뉴스가 선택되었습니다.")
    print(f"선택 이유: {result['reasoning']}")
    
    return selected_indices


# 4단계: Playwright로 뉴스 상세 내용 크롤링
def crawl_article_content(url: str) -> Dict[str, str]:
    """Playwright를 사용하여 기사의 상세 내용을 크롤링합니다."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_timeout(2000)
            
            # 본문 추출 시도 (다양한 선택자 사용)
            content = ""
            selectors = [
                'article',
                '[role="article"]',
                '.article-content',
                '.post-content',
                'main',
            ]
            
            for selector in selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        content = element.inner_text()
                        break
                except:
                    continue
            
            # 선택자로 찾지 못한 경우 body 사용
            if not content:
                content = page.query_selector('body').inner_text()
            
            browser.close()
            
            return {
                'content': content[:5000],  # 토큰 제한을 위해 5000자로 제한
                'success': True
            }
    except Exception as e:
        return {
            'content': '',
            'success': False,
            'error': str(e)
        }


def crawl_selected_news(articles: List[Dict[str, Any]], indices: List[int]) -> List[Dict[str, Any]]:
    """선택된 뉴스들의 상세 내용을 크롤링합니다."""
    print("\n[4단계] 선택된 뉴스 크롤링 중...")
    
    crawled_articles = []
    
    for idx in indices:
        if idx >= len(articles):
            continue
            
        article = articles[idx]
        print(f"  - [{idx}] {article['title'][:50]}... 크롤링 중")
        
        crawl_result = crawl_article_content(article['url'])
        
        if crawl_result['success']:
            crawled_articles.append({
                **article,
                'full_content': crawl_result['content']
            })
            print(f"    ✓ 성공")
        else:
            print(f"    ✗ 실패: {crawl_result.get('error', 'Unknown')}")
            # 실패해도 제목과 설명은 포함
            crawled_articles.append({
                **article,
                'full_content': article.get('description', '')
            })
    
    print(f"총 {len(crawled_articles)}개의 기사를 크롤링했습니다.")
    return crawled_articles


# 5단계: LLM이 주가 예측 분석
def predict_stock(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """수집된 뉴스를 바탕으로 NVIDIA 주가를 예측합니다."""
    print("\n[5단계] 주가 예측 분석 중...")
    
    parser = JsonOutputParser(pydantic_object=StockPrediction)
    
    # 뉴스 컨텍스트 생성
    news_context = ""
    for idx, article in enumerate(articles, 1):
        news_context += f"\n[기사 {idx}] {article['title']}\n"
        news_context += f"출처: {article['source']} | 날짜: {article['publishedAt']}\n"
        news_context += f"{article['full_content'][:1000]}\n"
        news_context += "-" * 80 + "\n"
    
    prompt = PromptTemplate(
        template="""당신은 전문 금융 애널리스트입니다. 다음 뉴스들을 분석하여 NVIDIA 주가를 예측하세요.

현재 날짜: {current_date}

수집된 뉴스:
{news_context}

다음을 수행하세요:
1. 뉴스에서 주가에 영향을 줄 긍정적/부정적 요인 추출
2. 각 요인의 중요도 평가
3. 장기적 관점(6개월 이상)에서 주가 방향성 예측
4. 예측의 신뢰도 평가 (0-100)
5. 전체 분석을 요약

{format_instructions}
""",
        input_variables=["current_date", "news_context"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "news_context": news_context[:30000]  # 토큰 제한 고려
    })
    
    return result


# 메인 파이프라인
def main():
    """전체 파이프라인을 실행합니다."""
    print("=" * 80)
    print("NVIDIA 주가 예측 시스템")
    print("=" * 80)
    
    try:
        # 1단계: 검색어 생성
        keywords = generate_search_keywords()
        
        # 2단계: 뉴스 수집
        articles = fetch_news(keywords)
        
        if not articles:
            print("\n수집된 뉴스가 없습니다. 프로그램을 종료합니다.")
            return
        
        # 3단계: 뉴스 필터링
        selected_indices = filter_news(articles)
        
        if not selected_indices:
            print("\n선택된 뉴스가 없습니다. 프로그램을 종료합니다.")
            return
        
        # 4단계: 상세 내용 크롤링
        crawled_articles = crawl_selected_news(articles, selected_indices)
        
        # 5단계: 주가 예측
        prediction = predict_stock(crawled_articles)
        
        # 결과 출력
        print("\n" + "=" * 80)
        print("예측 결과")
        print("=" * 80)
        print(f"\n예측: {prediction['prediction']}")
        print(f"신뢰도: {prediction['confidence']}%")
        print(f"예측 기간: {prediction['timeframe']}")
        
        print(f"\n긍정적 요인:")
        for factor in prediction['positive_factors']:
            print(f"  + {factor}")
        
        print(f"\n부정적 요인:")
        for factor in prediction['negative_factors']:
            print(f"  - {factor}")
        
        print(f"\n분석 요약:")
        print(f"{prediction['summary']}")
        
        # JSON 파일로 저장
        output = {
            'timestamp': datetime.now().isoformat(),
            'keywords': keywords,
            'total_articles': len(articles),
            'selected_articles': len(selected_indices),
            'crawled_articles': len(crawled_articles),
            'prediction': prediction,
            'articles': crawled_articles
        }
        
        output_file = f"nvidia_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n결과가 {output_file}에 저장되었습니다.")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

