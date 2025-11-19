"""
감성 및 이벤트 분석 에이전트 모듈

뉴스팩을 분석하여 감성 점수, 이벤트별 점수, 예측 방향을 도출합니다.
이벤트 유형별 가중치를 적용하여 최적 예측 기간을 계산합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from google import genai
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """
    근거 정보 모델
    
    Attributes:
        event_type: 이벤트 유형 (earnings/policy/product/supply/partnership/general)
        sentence: 근거가 되는 문장
    """
    event_type: str = Field(description="이벤트 유형")
    sentence: str = Field(description="근거 문장")


class EventScores(BaseModel):
    """
    이벤트별 점수 모델
    
    각 이벤트 유형별로 감성 점수를 명시적 필드로 관리합니다.
    Dict 대신 명시적 필드를 사용하여 타입 안정성을 보장합니다.
    
    Attributes:
        earnings: 실적 관련 점수 (-3.0 ~ +3.0)
        policy: 정책/규제 점수 (-3.0 ~ +3.0)
        product: 제품 관련 점수 (-3.0 ~ +3.0)
        supply: 공급망 점수 (-3.0 ~ +3.0)
        partnership: 파트너십 점수 (-3.0 ~ +3.0)
    """
    earnings: float = Field(default=0.0, description="실적 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    policy: float = Field(default=0.0, description="정책/규제 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    product: float = Field(default=0.0, description="제품 관련 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    supply: float = Field(default=0.0, description="공급망 점수 (-3 ~ +3)", ge=-3.0, le=3.0)
    partnership: float = Field(default=0.0, description="파트너십 점수 (-3 ~ +3)", ge=-3.0, le=3.0)


class SentimentAnalysis(BaseModel):
    """
    분석 에이전트 출력 모델
    
    Attributes:
        overall_sentiment: 전체 감성 점수 (-3.0 ~ +3.0)
        event_scores: 이벤트별 점수 객체
        evidences: 근거 리스트 (최소 3개)
        optimal_timeframe: 최적 예측 기간 (1-14일)
        direction: 예측 방향 (Up/Down/Hold)
    """
    overall_sentiment: float = Field(description="전체 감성 점수 (-3.0 ~ +3.0)", ge=-3.0, le=3.0)
    event_scores: EventScores = Field(description="이벤트별 점수")
    evidences: List[Evidence] = Field(description="근거 리스트 (최소 3개)")
    optimal_timeframe: int = Field(description="최적 예측 기간 (1-14일)", ge=1, le=14)
    direction: str = Field(description="예측 방향: Up/Down/Hold 중 하나")


class AnalysisAgent:
    """
    감성 및 이벤트 분석 에이전트
    
    뉴스팩을 분석하여 NVIDIA 주가에 대한 감성 점수와 예측 방향을 도출합니다.
    이벤트 유형별로 가중치를 적용하고, 최적 예측 기간을 계산합니다.
    피드백 루프를 통해 이전 분석 결과를 참고하여 더 정확한 분석을 수행합니다.
    
    Attributes:
        client: Gemini API 클라이언트
        model: 사용할 Gemini 모델명 (gemini-2.0-flash-exp)
        event_settings: 이벤트별 가중치 및 예측 기간 설정
    """
    
    def __init__(self, client: genai.Client) -> None:
        """
        AnalysisAgent 초기화
        
        Args:
            client: Gemini API 클라이언트 인스턴스
        """
        self.client = client
        self.model = "gemini-2.5-flash-preview-09-2025"
        
        # 이벤트별 가중치 및 예측 기간 설정
        self.event_settings = {
            'earnings': {'weight': 3.0, 'days': (3, 7)},
            'guidance': {'weight': 2.5, 'days': (5, 10)},
            'policy': {'weight': 2.0, 'days': (7, 14)},
            'product': {'weight': 1.5, 'days': (5, 10)},
            'supply': {'weight': 1.0, 'days': (7, 14)},
            'partnership': {'weight': 1.2, 'days': (3, 7)},
            'general': {'weight': 0.5, 'days': (5, 10)}
        }
    
    def analyze(self, 
                news_packs: List[Dict[str, Any]], 
                articles: List[Dict[str, Any]],
                previous_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """감성 분석 및 이벤트 추출
        
        Args:
            news_packs: 뉴스팩 리스트
            articles: 원본 기사 리스트
            previous_analysis: 이전 분석 결과 (피드백 루프용)
            
        Returns:
            분석 결과 딕셔너리
        """
        print("\n" + "="*80)
        print("[에이전트 4] 감성 및 이벤트 분석")
        print("="*80)
        
        # 뉴스팩 컨텍스트 생성
        context = ""
        for pack in news_packs[:10]:
            context += f"\n[{pack['event_type'].upper()}] 관련성: {pack.get('relevance_score', 0.5):.2f}\n"
            context += f"{pack['summary'][:400]}\n"
            context += "-" * 60 + "\n"
        
        # 이전 분석 결과를 프롬프트에 통합 (피드백 루프용)
        # 이전 반복의 분석 결과를 참고하여 더 정확한 분석 수행
        previous_context = ""
        if previous_analysis:
            previous_context = f"""

**이전 분석 결과**:
- 전체 감성: {previous_analysis.get('overall_sentiment', 0)}
- 예측 방향: {previous_analysis.get('direction', 'Unknown')}
- 주요 근거: {', '.join(e.get('sentence', '')[:50] for e in previous_analysis.get('evidences', [])[:3])}

이전 분석을 참고하되, 새로운 정보를 통합하여 더 정확한 분석을 제공하세요.
"""
        
        try:
            prompt = f"""당신은 NVIDIA 주가 분석 전문가입니다. 뉴스를 분석하고 주가 예측을 제공하세요.

현재 날짜: {datetime.now().strftime("%Y-%m-%d")}

분석 대상 뉴스:
{context[:8000]}
{previous_context}

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
            
            # 구조화된 출력 파싱 (자동으로 SentimentAnalysis 객체로 변환됨)
            result: SentimentAnalysis = response.parsed
            
            if result:
                # Pydantic 모델을 딕셔너리로 변환 (JSON 직렬화 가능하도록)
                event_scores_dict = result.event_scores.model_dump()
                
                # 최종 결과 딕셔너리 구성
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
        """
        간단한 감성 추정 (폴백용)
        
        API 실패 시 사용하는 간단한 감성 추정 방법입니다.
        뉴스팩의 평균 관련성 점수를 기반으로 감성을 추정합니다.
        
        Args:
            news_packs: 뉴스팩 리스트
        
        Returns:
            float: 추정된 감성 점수 (-1.0 ~ 1.0)
        """
        if not news_packs:
            return 0.0
        
        # 평균 관련성 점수 계산
        avg_relevance = sum(pack.get('relevance_score', 0.5) for pack in news_packs) / len(news_packs)
        
        # 관련성 점수를 감성 점수로 변환 (-1 ~ 1 범위)
        # 0.5를 중립으로 간주하고 스케일 조정
        return (avg_relevance - 0.5) * 2
