"""
뉴스 병합 및 정제 에이전트 모듈

수집된 뉴스 기사들을 이벤트별로 그룹화하고 정제하여 뉴스팩으로 변환합니다.
중복 및 재탕 기사를 통합하고, 각 이벤트의 핵심 내용을 요약합니다.
"""

from typing import List, Dict, Any
from google import genai
from pydantic import BaseModel, Field


class NewsPack(BaseModel):
    """
    뉴스팩 구조
    
    관련된 여러 기사를 하나의 이벤트로 그룹화한 단위입니다.
    
    Attributes:
        pack_id: 뉴스팩 고유 ID (예: pack_001)
        event_type: 이벤트 유형 (earnings/policy/product/supply/partnership/general)
        summary: 핵심 내용 요약 (3-5문장)
        relevance_score: NVIDIA 관련성 점수 (0.0-1.0)
        article_indices: 포함된 기사의 인덱스 리스트
    """
    pack_id: str = Field(description="뉴스팩 ID (예: pack_001)")
    event_type: str = Field(description="이벤트 유형: earnings/policy/product/supply/partnership/general")
    summary: str = Field(description="핵심 내용 요약 (3-5문장)")
    relevance_score: float = Field(description="NVIDIA 관련성 점수 (0.0-1.0)")
    article_indices: List[int] = Field(description="포함된 기사 인덱스")


class NewsPacks(BaseModel):
    """
    병합 에이전트 출력 모델
    
    Attributes:
        packs: 생성된 뉴스팩 리스트 (5-10개)
    """
    packs: List[NewsPack] = Field(description="뉴스팩 리스트 (5-10개)")


class MergeAgent:
    """
    뉴스 병합 및 정제 에이전트
    
    수집된 뉴스 기사들을 분석하여 이벤트별로 그룹화하고 뉴스팩으로 정제합니다.
    중복/재탕 기사를 같은 이벤트로 묶고, 각 뉴스팩의 핵심 내용을 요약하며,
    NVIDIA 관련성 점수를 부여합니다.
    
    Attributes:
        client: Gemini API 클라이언트
        model: 사용할 Gemini 모델명 (gemini-2.0-flash-exp)
    """
    
    def __init__(self, client: genai.Client) -> None:
        """
        MergeAgent 초기화
        
        Args:
            client: Gemini API 클라이언트 인스턴스
        """
        self.client = client
        self.model = "gemini-2.5-flash-preview-09-2025"
    
    def merge_and_refine(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        뉴스를 뉴스팩으로 병합 및 정제
        
        수집된 기사들을 분석하여 이벤트별로 그룹화하고 뉴스팩으로 변환합니다.
        중복/재탕 기사를 통합하고, 각 이벤트의 핵심 내용을 요약하며,
        NVIDIA 관련성 점수를 부여합니다.
        
        Args:
            articles: 수집된 뉴스 기사 리스트
        
        Returns:
            List[Dict[str, Any]]: 생성된 뉴스팩 리스트 (5-10개)
                각 뉴스팩은 pack_id, event_type, summary, relevance_score, article_indices 포함
        """
        print("\n" + "="*80)
        print("[에이전트 3] 뉴스 병합 및 정제")
        print("="*80)
        
        if not articles:
            return []
        
        # 기사가 너무 많으면 상위 20개만 선택 (토큰 제한)
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
