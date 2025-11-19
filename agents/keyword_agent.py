"""
키워드 생성 에이전트 모듈

NVIDIA 주가 예측을 위한 검색 키워드를 생성하는 에이전트입니다.
Gemini의 구조화된 출력 기능을 사용하여 카테고리별로 최적화된 키워드를 생성합니다.
"""

from typing import List
from datetime import datetime
from google import genai
from pydantic import BaseModel, Field


class SearchKeywords(BaseModel):
    """
    키워드 에이전트 출력 모델
    
    Attributes:
        keywords: 검색 키워드 리스트 (최대 10개)
        reasoning: 키워드 선택 이유 및 전략 설명
    """
    keywords: List[str] = Field(description="검색 키워드 리스트 (10개)")
    reasoning: str = Field(description="키워드 선택 이유")


class KeywordAgent:
    """
    검색 키워드 생성 에이전트
    
    Gemini의 구조화된 출력 기능을 사용하여 NVIDIA 주가 예측에 최적화된
    검색 키워드를 생성합니다. 카테고리별(제품/기술, 정책/규제, 재무, 파트너십, 공급망)로
    균형잡힌 키워드를 생성하며, 피드백 루프를 통해 이전 시도의 부족한 점을 보완합니다.
    
    Attributes:
        client: Gemini API 클라이언트
        model: 사용할 Gemini 모델명 (기본: gemini-2.5-flash)
        default_keywords: API 실패 시 사용할 폴백 키워드 리스트
    """
    
    def __init__(self, client: genai.Client) -> None:
        """
        KeywordAgent 초기화
        
        Args:
            client: Gemini API 클라이언트 인스턴스
        """
        self.client = client
        self.model = "gemini-2.5-flash-preview-09-2025"
        
        # 폴백 기본 키워드 - API 실패 시 사용
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
        """
        카테고리별 검색 키워드 생성 (첫 번째 반복용)
        
        NVIDIA 주가 예측을 위한 검색 키워드를 카테고리별로 생성합니다.
        제품/기술, 정책/규제, 재무, 파트너십, 공급망 카테고리에서
        각각 2개씩 총 10개의 키워드를 생성합니다.
        
        Returns:
            List[str]: 생성된 검색 키워드 리스트 (최대 10개)
            
        Raises:
            Exception: API 호출 실패 시 기본 키워드 반환 (예외 발생하지 않음)
        """
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
    
    def generate_keywords_with_context(self, context) -> List[str]:
        """
        이전 컨텍스트를 반영한 키워드 생성 (피드백 루프용)
        
        이전 반복의 결과를 분석하여 부족한 점을 보완하는 새로운 키워드를 생성합니다.
        이전 키워드와 중복되지 않도록 하며, 신뢰도가 낮았던 원인을 해결할 수 있는
        더 구체적이고 다양한 관점의 키워드를 포함합니다.
        
        Args:
            context: IterationContext 객체 (이전 시도의 정보 포함)
                - iteration: 현재 반복 번호
                - previous_confidence: 이전 신뢰도 점수
                - previous_keywords: 이전에 사용한 키워드 리스트
                - deficiencies: 부족했던 점 리스트
                - contra_arguments: 반대 근거 리스트
            
        Returns:
            List[str]: 개선된 검색 키워드 리스트 (최대 10개)
            
        Raises:
            Exception: API 호출 실패 시 기본 키워드 반환 (예외 발생하지 않음)
        """
        print("\n" + "="*80)
        print(f"[에이전트 1] 키워드 생성 (반복 {context.iteration + 1})")
        print("="*80)
        
        try:
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
이전 키워드와 중복되지 않도록 하고, 더 구체적이고 다양한 관점의 키워드를 포함하세요.

카테고리별로 생성:
- 제품/기술 (2개): AI chip, GPU, Hopper, Blackwell
- 정책/규제 (2개): China, export control, regulation
- 재무 (2개): earnings, revenue, guidance
- 파트너십 (2개): partnership, deal, customer
- 공급망 (2개): TSMC, supply chain, manufacturing

각 키워드는 "NVIDIA" 또는 "NVDA"를 포함하고 영어로 작성하세요."""

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
                
                print(f"\n개선된 검색어 ({len(keywords)}개):")
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
