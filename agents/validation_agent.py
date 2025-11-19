"""
검증 에이전트 모듈

분석 결과를 검증하고 신뢰도를 계산합니다.
출처 품질, 일관성, 최신성을 평가하고, Devil's Advocate 방식으로 반대 근거를 찾습니다.
"""

from typing import List, Dict, Any
from datetime import datetime
from google import genai
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """
    검증 에이전트 출력 모델
    
    Attributes:
        confidence: 최종 신뢰도 점수 (0-100)
        is_valid: 임계치 통과 여부
        validation_notes: 검증 사항 리스트
        contra_arguments: 반대 근거 리스트
    """
    confidence: int = Field(description="최종 신뢰도 (0-100)", ge=0, le=100)
    is_valid: bool = Field(description="임계치 통과 여부")
    validation_notes: List[str] = Field(description="검증 사항")
    contra_arguments: List[str] = Field(description="반대 근거")


class ValidationAgent:
    """
    검증 에이전트
    
    분석 결과를 다각도로 검증하고 신뢰도를 계산합니다.
    출처 신뢰도, 일관성, 최신성을 평가하고, Devil's Advocate 방식으로
    반대 근거를 찾아 분석의 객관성을 높입니다.
    
    신뢰도 계산 공식:
    - 출처 품질: 40%
    - 일관성: 30%
    - 최신성: 20%
    - 감성 강도: 10%
    
    Attributes:
        client: Gemini API 클라이언트
        model: 사용할 Gemini 모델명
        confidence_threshold: 신뢰도 임계치 (기본값: 60)
        trusted_sources: 신뢰할 수 있는 뉴스 소스와 가중치 딕셔너리
    """
    
    def __init__(self, client: genai.Client, confidence_threshold: int = 60) -> None:
        """
        ValidationAgent 초기화
        
        Args:
            client: Gemini API 클라이언트 인스턴스
            confidence_threshold: 신뢰도 임계치 (0-100, 기본값: 60)
        """
        self.client = client
        self.model = "gemini-2.5-flash-preview-09-2025"
        self.confidence_threshold = confidence_threshold
        
        # 신뢰 소스 화이트리스트 (소스명: 신뢰도 가중치)
        self.trusted_sources = {
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
    
    def validate(self, 
                 analysis: Dict[str, Any],
                 news_packs: List[Dict[str, Any]],
                 articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        분석 결과 검증 및 신뢰도 계산
        
        분석 결과를 다각도로 검증하고 최종 신뢰도를 계산합니다.
        출처 품질(40%), 일관성(30%), 최신성(20%), 감성 강도(10%)를 종합하여
        0-100 범위의 신뢰도 점수를 산출합니다.
        
        Args:
            analysis: 감성 분석 결과
            news_packs: 뉴스팩 리스트
            articles: 원본 기사 리스트
        
        Returns:
            Dict[str, Any]: 검증 결과
                - confidence: 최종 신뢰도 (0-100)
                - is_valid: 임계치 통과 여부
                - validation_notes: 검증 사항 리스트
                - contra_arguments: 반대 근거 리스트
        """
        print("\n" + "="*80)
        print("[에이전트 5] 결과 검증")
        print("="*80)
        
        # 1. 출처 신뢰도 계산 (가중치 40%)
        source_score = self._calculate_source_quality(articles)
        
        # 2. 일관성 점수 계산 (가중치 30%)
        consistency_score = self._calculate_consistency(news_packs)
        
        # 3. 최신성 점수 계산 (가중치 20%)
        recency_score = self._calculate_recency(articles)
        
        # 4. Devil's Advocate - 반대 근거 찾기
        contra_args = self._find_counter_arguments(analysis, news_packs)
        
        # 5. 최종 신뢰도 계산 (가중 평균)
        # 감성 강도는 최대 10%까지 기여 (절대값 3.0 = 10%)
        # 강한 감성(긍정 또는 부정)은 신뢰도를 높임
        sentiment_contribution = min(abs(analysis.get('overall_sentiment', 0)) * 3.33, 10)
        
        # 가중 평균 계산: 출처(40%) + 일관성(30%) + 최신성(20%) + 감성(10%)
        confidence = int(
            source_score * 40 +        # 출처 품질 40%
            consistency_score * 30 +   # 일관성 30%
            recency_score * 20 +       # 최신성 20%
            sentiment_contribution     # 감성 강도 10%
        )
        
        # 임계치 통과 여부 판단
        is_valid = confidence >= self.confidence_threshold
        
        print(f"\n[신뢰도 상세 분석]")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 각 요소별 점수와 기여도 계산
        source_contribution = source_score * 40
        consistency_contribution = consistency_score * 30
        recency_contribution = recency_score * 20
        
        print(f"\n1. 출처 품질 점수: {source_score:.1%}")
        print(f"   → 기여도: {source_contribution:.1f}점 (가중치 40%)")
        if source_score < 0.7:
            print(f"   ⚠️  개선 필요: 신뢰할 수 있는 출처(Reuters, Bloomberg 등)의 기사가 부족합니다")
        
        print(f"\n2. 일관성 점수: {consistency_score:.1%}")
        print(f"   → 기여도: {consistency_contribution:.1f}점 (가중치 30%)")
        if consistency_score < 0.7:
            print(f"   ⚠️  개선 필요: 뉴스팩의 다양성 또는 관련성이 낮습니다")
        
        print(f"\n3. 최신성 점수: {recency_score:.1%}")
        print(f"   → 기여도: {recency_contribution:.1f}점 (가중치 20%)")
        if recency_score < 0.5:
            print(f"   ⚠️  개선 필요: 최근 1주일 이내의 기사가 부족합니다")
        
        print(f"\n4. 감성 강도: {abs(analysis.get('overall_sentiment', 0)):.2f}/3.0")
        print(f"   → 기여도: {sentiment_contribution:.1f}점 (가중치 10%)")
        if abs(analysis.get('overall_sentiment', 0)) < 1.0:
            print(f"   ⚠️  개선 필요: 감성이 약해 예측 신뢰도가 낮습니다")
        
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"최종 신뢰도: {confidence}% (임계치: {self.confidence_threshold}%)")
        print(f"결과: {'✓ 통과' if is_valid else '✗ 부족 (피드백 루프 필요)'}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if contra_args:
            print(f"\n[반대 근거 - Devil's Advocate]")
            for i, arg in enumerate(contra_args, 1):
                print(f"  {i}. {arg}")
        
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
        """
        출처 신뢰도 점수 계산
        
        각 기사의 출처를 신뢰 소스 화이트리스트와 비교하여 신뢰도를 평가합니다.
        화이트리스트에 있는 소스는 높은 가중치를, 그 외는 기본값(0.5)을 부여합니다.
        
        Args:
            articles: 기사 리스트
        
        Returns:
            float: 평균 출처 신뢰도 (0.0-1.0)
        """
        if not articles:
            return 0.0
        
        scores = []
        for article in articles:
            source = article.get('source', '').lower()
            score = 0.5  # 기본값 (알 수 없는 소스)
            
            # 신뢰 소스 화이트리스트와 매칭
            for trusted, weight in self.trusted_sources.items():
                if trusted in source:
                    score = weight
                    break
            
            scores.append(score)
        
        # 평균 신뢰도 반환
        return sum(scores) / len(scores)
    
    def _calculate_consistency(self, news_packs: List[Dict[str, Any]]) -> float:
        """
        일관성 점수 계산
        
        뉴스팩의 다양성과 관련성을 평가하여 일관성 점수를 계산합니다.
        이벤트 타입이 다양하고 관련성 점수가 높을수록 높은 점수를 받습니다.
        
        Args:
            news_packs: 뉴스팩 리스트
        
        Returns:
            float: 일관성 점수 (0.0-1.0)
        """
        if len(news_packs) < 2:
            return 0.6  # 뉴스가 적으면 중간 점수 부여
        
        # 이벤트 타입 다양성 계산 (다양할수록 좋음)
        event_types = set(pack.get('event_type', '') for pack in news_packs)
        diversity = len(event_types) / len(news_packs)
        
        # 평균 관련성 점수 계산
        relevance = sum(pack.get('relevance_score', 0) for pack in news_packs) / len(news_packs)
        
        # 다양성 30%, 관련성 70%로 가중 평균
        return (diversity * 0.3 + relevance * 0.7)
    
    def _calculate_recency(self, articles: List[Dict[str, Any]]) -> float:
        """
        최신성 점수 계산
        
        1주일 이내에 발행된 기사의 비율을 계산하여 최신성을 평가합니다.
        최신 뉴스일수록 주가 예측에 더 유용합니다.
        
        Args:
            articles: 기사 리스트
        
        Returns:
            float: 최신성 점수 (0.0-1.0)
        """
        if not articles:
            return 0.0
        
        now = datetime.now()
        recent_count = 0
        
        for article in articles:
            pub_date = article.get('publishedAt', '')
            try:
                # ISO 형식 날짜 파싱 (Z를 +00:00으로 변환)
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                days_ago = (now - pub_dt).days
                
                # 1주일 이내 기사 카운트
                if days_ago <= 7:
                    recent_count += 1
            except:
                # 날짜 파싱 실패 시 무시
                continue
        
        # 최신 기사 비율 반환
        return recent_count / len(articles)
    
    def _find_counter_arguments(self, analysis: Dict[str, Any], news_packs: List[Dict[str, Any]]) -> List[str]:
        """
        Devil's Advocate - 반대 근거 찾기
        
        분석 결과에 대한 반대 의견을 찾아 객관성을 높입니다.
        LLM을 사용하여 간과된 부정적 요인, 과대평가된 긍정적 요인,
        놓친 리스크 등을 식별합니다.
        
        Args:
            analysis: 감성 분석 결과
            news_packs: 뉴스팩 리스트
        
        Returns:
            List[str]: 반대 근거 리스트 (최대 3개)
        """
        # 상위 3개 뉴스팩의 요약 추출
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
            
            # 줄바꿈으로 분리하고 정제
            # 빈 줄과 너무 짧은 줄(10자 미만) 제거
            args = [line.strip('- ').strip() for line in text.split('\n') 
                   if line.strip() and len(line.strip()) > 10]
            
            # 최대 3개까지만 반환
            return args[:3]
            
        except:
            return []
