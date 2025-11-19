"""
LangGraph 노드 함수 모듈

워크플로우의 각 단계를 구현하는 노드 함수들을 제공합니다.
각 노드는 WorkflowState를 입력받아 처리 후 업데이트된 상태를 반환합니다.
"""

from typing import Dict, Any
from workflow.state import (
    WorkflowState, 
    IterationContext, 
    merge_articles,
    create_iteration_context
)
from agents.keyword_agent import KeywordAgent
from agents.crawler_agent import CrawlerAgent
from agents.merge_agent import MergeAgent
from agents.analysis_agent import AnalysisAgent
from agents.validation_agent import ValidationAgent
from google import genai
from newsapi import NewsApiClient
from config.settings import (
    GEMINI_API_KEY,
    NEWS_API_KEY,
    MAX_CRAWL_ARTICLES,
    NEWS_DAYS_BACK,
    CONFIDENCE_THRESHOLD
)


# 전역 클라이언트 초기화 (노드 함수에서 재사용)
_genai_client = None
_news_api_client = None


def _get_genai_client() -> genai.Client:
    """Gemini 클라이언트 싱글톤"""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
    return _genai_client


def _get_news_api_client() -> NewsApiClient:
    """NewsAPI 클라이언트 싱글톤"""
    global _news_api_client
    if _news_api_client is None:
        _news_api_client = NewsApiClient(api_key=NEWS_API_KEY)
    return _news_api_client


# ============================================================================
# 기본 노드들 (Subtask 6.1)
# ============================================================================

def keyword_node(state: WorkflowState) -> Dict[str, Any]:
    """
    키워드 생성 노드
    
    이전 컨텍스트를 활용하여 검색 키워드를 생성합니다.
    첫 번째 반복에서는 기본 키워드를 생성하고,
    이후 반복에서는 피드백을 반영한 개선된 키워드를 생성합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (keywords 필드 포함)
    """
    try:
        client = _get_genai_client()
        agent = KeywordAgent(client)
        
        # 이전 컨텍스트 확인
        iteration_contexts = state.get("iteration_contexts", [])
        
        if iteration_contexts:
            # 피드백을 반영한 키워드 생성
            context = iteration_contexts[-1]
            keywords = agent.generate_keywords_with_context(context)
        else:
            # 첫 시도 - 기본 키워드 생성
            keywords = agent.generate_keywords()
        
        return {"keywords": keywords}
        
    except Exception as e:
        # 에러 발생 시 기본 키워드 사용
        print(f"\n⚠️ 키워드 생성 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "keyword_generation",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "default_keywords"
        })
        
        # 기본 키워드 사용
        default_keywords = [
            "NVIDIA earnings report",
            "NVDA stock forecast",
            "NVIDIA AI chip demand",
            "NVIDIA data center revenue",
            "NVIDIA China export ban"
        ]
        
        print(f"기본 키워드 사용: {len(default_keywords)}개")
        
        return {
            "keywords": default_keywords,
            "errors": errors
        }


def crawler_node(state: WorkflowState) -> Dict[str, Any]:
    """
    뉴스 수집 노드
    
    생성된 키워드로 뉴스를 수집하고 본문을 크롤링합니다.
    이전 반복에서 수집한 기사와 병합하여 중복을 제거합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (articles 필드 포함)
    """
    try:
        genai_client = _get_genai_client()
        news_api_client = _get_news_api_client()
        agent = CrawlerAgent(news_api_client, genai_client)
        
        keywords = state.get("keywords", [])
        
        if not keywords:
            raise ValueError("키워드가 없습니다")
        
        # 새 뉴스 수집 (NewsAPI 사용)
        new_articles = agent.fetch_news(keywords, days_back=NEWS_DAYS_BACK)
        
        # 본문 크롤링 (Playwright 사용)
        crawled_articles = agent.crawl_articles(new_articles, max_crawl=MAX_CRAWL_ARTICLES)
        
        # 이전 기사와 병합 (URL 기반 중복 제거)
        # 피드백 루프에서 이전 반복의 기사를 유지하면서 새 기사 추가
        existing_articles = state.get("articles", [])
        merged_articles = merge_articles(existing_articles, crawled_articles)
        
        print(f"\n기사 병합 결과: 기존 {len(existing_articles)}개 + 신규 {len(crawled_articles)}개 = 총 {len(merged_articles)}개")
        
        return {"articles": merged_articles}
        
    except Exception as e:
        # 에러 발생 시 기존 기사 유지
        print(f"\n⚠️ 뉴스 수집 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "news_collection",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "keep_existing_articles"
        })
        
        existing_articles = state.get("articles", [])
        
        if not existing_articles:
            # 기존 기사도 없으면 치명적 에러
            print("⚠️ 수집된 기사가 없습니다. 워크플로우를 계속할 수 없습니다.")
            return {
                "articles": [],
                "errors": errors,
                "has_critical_error": True
            }
        
        print(f"기존 기사 유지: {len(existing_articles)}개")
        
        return {
            "articles": existing_articles,
            "errors": errors
        }


def merge_node(state: WorkflowState) -> Dict[str, Any]:
    """
    뉴스 병합 노드
    
    수집된 기사들을 이벤트별로 그룹화하고 뉴스팩으로 정제합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (news_packs 필드 포함)
    """
    try:
        # 치명적 에러가 있으면 스킵
        if state.get("has_critical_error"):
            return {"news_packs": []}
        
        client = _get_genai_client()
        agent = MergeAgent(client)
        
        articles = state.get("articles", [])
        
        if not articles:
            raise ValueError("병합할 기사가 없습니다")
        
        news_packs = agent.merge_and_refine(articles)
        
        return {"news_packs": news_packs}
        
    except Exception as e:
        # 에러 발생 시 기본 뉴스팩 생성
        print(f"\n⚠️ 뉴스 병합 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "news_merge",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "simple_news_packs"
        })
        
        # 간단한 뉴스팩 생성 (폴백)
        articles = state.get("articles", [])
        simple_packs = []
        
        for idx, article in enumerate(articles[:5]):
            simple_packs.append({
                'pack_id': f'pack_{idx:03d}',
                'event_type': 'general',
                'summary': article.get('title', '') + ". " + article.get('description', '')[:200],
                'relevance_score': 0.5,
                'article_indices': [idx]
            })
        
        print(f"간단한 뉴스팩 생성: {len(simple_packs)}개")
        
        return {
            "news_packs": simple_packs,
            "errors": errors
        }


# ============================================================================
# 분석 및 검증 노드들 (Subtask 6.2)
# ============================================================================

def analysis_node(state: WorkflowState) -> Dict[str, Any]:
    """
    감성 분석 노드
    
    뉴스팩을 분석하여 감성 점수와 이벤트 점수를 계산합니다.
    이전 분석 결과가 있으면 참고하여 더 정확한 분석을 수행합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (analysis 필드 포함)
    """
    try:
        # 치명적 에러가 있으면 스킵
        if state.get("has_critical_error"):
            return {"analysis": None}
        
        client = _get_genai_client()
        agent = AnalysisAgent(client)
        
        news_packs = state.get("news_packs", [])
        articles = state.get("articles", [])
        
        if not news_packs:
            raise ValueError("분석할 뉴스팩이 없습니다")
        
        # 이전 분석 결과 참고
        previous_analysis = None
        all_results = state.get("all_results", [])
        if all_results:
            previous_analysis = all_results[-1].get("analysis")
        
        # 감성 분석 수행
        analysis = agent.analyze(
            news_packs=news_packs,
            articles=articles,
            previous_analysis=previous_analysis
        )
        
        return {"analysis": analysis}
        
    except Exception as e:
        # 에러 발생 시 중립 분석 반환
        print(f"\n⚠️ 감성 분석 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "sentiment_analysis",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "neutral_analysis"
        })
        
        # 중립 분석 (폴백)
        neutral_analysis = {
            'overall_sentiment': 0.0,
            'event_scores': {'general': 0.0},
            'evidences': [{'event_type': 'general', 'sentence': '분석 실패로 인한 중립 결과'}],
            'optimal_timeframe': 7,
            'direction': 'Hold'
        }
        
        print("중립 분석 결과 사용")
        
        return {
            "analysis": neutral_analysis,
            "errors": errors
        }


def validation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    검증 노드
    
    분석 결과를 검증하고 신뢰도를 계산합니다.
    결과를 all_results에 저장하고 최고 결과를 업데이트합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (validation, all_results, best_result 필드 포함)
    """
    try:
        # 치명적 에러가 있으면 낮은 신뢰도 반환
        if state.get("has_critical_error"):
            validation = {
                "confidence": 0,
                "is_valid": False,
                "validation_notes": ["치명적 에러 발생"],
                "contra_arguments": []
            }
            
            result = {
                "iteration": state.get("iteration", 1),
                "confidence": 0,
                "analysis": None,
                "validation": validation,
                "keywords": state.get("keywords", []),
                "article_count": 0,
                "news_pack_count": 0,
                "has_error": True
            }
            
            all_results = state.get("all_results", []).copy()
            all_results.append(result)
            
            return {
                "validation": validation,
                "all_results": all_results,
                "best_result": state.get("best_result")
            }
        
        client = _get_genai_client()
        agent = ValidationAgent(client, confidence_threshold=CONFIDENCE_THRESHOLD)
        
        analysis = state.get("analysis")
        news_packs = state.get("news_packs", [])
        articles = state.get("articles", [])
        
        if not analysis:
            raise ValueError("검증할 분석 결과가 없습니다")
        
        # 검증 수행
        validation = agent.validate(
            analysis=analysis,
            news_packs=news_packs,
            articles=articles
        )
        
        # 현재 반복 결과 저장 (히스토리 추적용)
        iteration = state.get("iteration", 1)
        keywords = state.get("keywords", [])
        
        result = {
            "iteration": iteration,
            "confidence": validation["confidence"],
            "analysis": analysis,
            "validation": validation,
            "keywords": keywords,
            "article_count": len(articles),
            "news_pack_count": len(news_packs)
        }
        
        # all_results에 추가 (모든 반복의 결과 누적)
        all_results = state.get("all_results", []).copy()
        all_results.append(result)
        
        # 최고 결과 업데이트 (신뢰도 기준)
        # 피드백 루프 종료 시 최고 신뢰도 결과를 최종 결과로 사용
        best_result = state.get("best_result")
        if not best_result or validation["confidence"] > best_result["confidence"]:
            best_result = result
        
        return {
            "validation": validation,
            "all_results": all_results,
            "best_result": best_result
        }
        
    except Exception as e:
        # 에러 발생 시 낮은 신뢰도 반환
        print(f"\n⚠️ 검증 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "validation",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "low_confidence"
        })
        
        # 낮은 신뢰도 검증 결과 (폴백)
        validation = {
            "confidence": 20,
            "is_valid": False,
            "validation_notes": [f"검증 실패: {str(e)}"],
            "contra_arguments": []
        }
        
        result = {
            "iteration": state.get("iteration", 1),
            "confidence": 20,
            "analysis": state.get("analysis"),
            "validation": validation,
            "keywords": state.get("keywords", []),
            "article_count": len(state.get("articles", [])),
            "news_pack_count": len(state.get("news_packs", [])),
            "has_error": True
        }
        
        all_results = state.get("all_results", []).copy()
        all_results.append(result)
        
        best_result = state.get("best_result")
        if not best_result:
            best_result = result
        
        print("낮은 신뢰도 결과 사용 (20%)")
        
        return {
            "validation": validation,
            "all_results": all_results,
            "best_result": best_result,
            "errors": errors
        }


# ============================================================================
# 피드백 및 제어 노드들 (Subtask 6.3)
# ============================================================================

def feedback_node(state: WorkflowState) -> Dict[str, Any]:
    """
    피드백 노드
    
    검증 결과를 분석하여 다음 반복을 위한 컨텍스트를 생성합니다.
    부족한 점과 반대 근거를 추출하여 다음 키워드 생성에 활용합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        업데이트된 상태 (iteration_contexts, iteration 필드 포함)
    """
    try:
        validation = state.get("validation", {})
        keywords = state.get("keywords", [])
        articles = state.get("articles", [])
        analysis = state.get("analysis")
        iteration = state.get("iteration", 1)
        
        # 다음 반복을 위한 컨텍스트 생성
        # 부족한 점과 반대 근거를 추출하여 다음 키워드 생성에 활용
        context = create_iteration_context(
            iteration=iteration,
            validation=validation,
            keywords=keywords,
            article_count=len(articles),
            analysis=analysis
        )
        
        # 컨텍스트 리스트에 추가 (누적)
        iteration_contexts = state.get("iteration_contexts", []).copy()
        iteration_contexts.append(context)
        
        # 반복 횟수 증가 (다음 반복 준비)
        next_iteration = iteration + 1
        
        print(f"\n{'='*80}")
        print(f"피드백 생성 완료 - 다음 반복 {next_iteration}로 진행")
        print(f"{'='*80}")
        print(f"부족한 점 ({len(context.deficiencies)}개):")
        for deficiency in context.deficiencies:
            print(f"  - {deficiency}")
        
        if context.contra_arguments:
            print(f"\n반대 근거 ({len(context.contra_arguments)}개):")
            for arg in context.contra_arguments:
                print(f"  - {arg}")
        
        # 타임스탬프 기록
        from datetime import datetime
        iteration_timestamps = state.get("iteration_timestamps", []).copy()
        iteration_timestamps.append({
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "confidence": validation.get("confidence", 0)
        })
        
        return {
            "iteration_contexts": iteration_contexts,
            "iteration": next_iteration,
            "iteration_timestamps": iteration_timestamps
        }
        
    except Exception as e:
        # 에러 발생 시 기본 컨텍스트 생성
        print(f"\n⚠️ 피드백 노드 에러: {e}")
        
        # 에러 기록
        errors = state.get("errors", []).copy()
        errors.append({
            "node": "feedback",
            "iteration": state.get("iteration", 1),
            "error": str(e),
            "fallback": "basic_context"
        })
        
        # 기본 컨텍스트 생성
        from workflow.state import IterationContext
        
        basic_context = IterationContext(
            iteration=state.get("iteration", 1),
            deficiencies=["피드백 생성 실패 - 다양한 키워드 시도"],
            contra_arguments=[],
            previous_keywords=state.get("keywords", []),
            previous_confidence=state.get("validation", {}).get("confidence", 0)
        )
        
        iteration_contexts = state.get("iteration_contexts", []).copy()
        iteration_contexts.append(basic_context)
        
        next_iteration = state.get("iteration", 1) + 1
        
        print(f"기본 피드백 컨텍스트 사용 - 다음 반복 {next_iteration}로 진행")
        
        # 타임스탬프 기록
        from datetime import datetime
        iteration_timestamps = state.get("iteration_timestamps", []).copy()
        iteration_timestamps.append({
            "iteration": state.get("iteration", 1),
            "timestamp": datetime.now().isoformat(),
            "confidence": state.get("validation", {}).get("confidence", 0),
            "has_error": True
        })
        
        return {
            "iteration_contexts": iteration_contexts,
            "iteration": next_iteration,
            "errors": errors,
            "iteration_timestamps": iteration_timestamps
        }


def should_continue_or_end(state: WorkflowState) -> str:
    """
    계속 진행할지 종료할지 결정하는 조건 함수
    
    신뢰도가 임계치를 넘거나 최대 반복 횟수에 도달하면 종료합니다.
    그렇지 않으면 피드백 노드로 이동하여 다음 반복을 준비합니다.
    
    Args:
        state: 현재 워크플로우 상태
    
    Returns:
        "continue" 또는 "end"
    """
    validation = state.get("validation", {})
    confidence = validation.get("confidence", 0)
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)
    has_critical_error = state.get("has_critical_error", False)
    
    # 종료 조건 1: 치명적 에러 발생 시 즉시 종료
    if has_critical_error:
        print(f"\n✗ 치명적 에러 발생 - 워크플로우 강제 종료")
        return "end"
    
    # 종료 조건 2: 신뢰도 충족 시 종료 (성공)
    if confidence >= CONFIDENCE_THRESHOLD:
        print(f"\n✓ 신뢰도 임계치 달성 ({confidence}% >= {CONFIDENCE_THRESHOLD}%) - 워크플로우 종료")
        return "end"
    
    # 종료 조건 3: 최대 반복 도달 시 종료 (무한 루프 방지)
    if iteration >= max_iterations:
        print(f"\n✓ 최대 반복 횟수 도달 ({iteration}/{max_iterations}) - 워크플로우 종료")
        print(f"   무한 루프 방지: 최대 {max_iterations}회 반복 제한 적용됨")
        return "end"
    
    # 안전 장치: 반복 횟수가 max_iterations를 초과하는 경우 (버그 방지)
    # 정상적으로는 발생하지 않아야 하지만, 예외 상황 대비
    if iteration > max_iterations:
        print(f"\n⚠️  경고: 반복 횟수 초과 감지 ({iteration} > {max_iterations}) - 강제 종료")
        return "end"
    
    # 계속 진행: 신뢰도 부족하고 반복 가능
    print(f"\n{'='*80}")
    print(f"⚠️  신뢰도 부족 - 피드백 루프 계속")
    print(f"{'='*80}")
    print(f"현재 신뢰도: {confidence}% (임계치: {CONFIDENCE_THRESHOLD}%)")
    print(f"진행 상황: {iteration}/{max_iterations} 반복")
    
    # 신뢰도 부족 원인 상세 분석
    print(f"\n[신뢰도 부족 원인 분석]")
    validation_notes = validation.get("validation_notes", [])
    if validation_notes:
        print("검증 점수:")
        for note in validation_notes:
            print(f"  • {note}")
    
    contra_arguments = validation.get("contra_arguments", [])
    if contra_arguments:
        print(f"\n반대 근거 ({len(contra_arguments)}개):")
        for arg in contra_arguments:
            print(f"  • {arg}")
    
    # 부족한 점 분석
    iteration_contexts = state.get("iteration_contexts", [])
    if iteration_contexts:
        latest_context = iteration_contexts[-1]
        if latest_context.deficiencies:
            print(f"\n부족한 점 ({len(latest_context.deficiencies)}개):")
            for deficiency in latest_context.deficiencies:
                print(f"  • {deficiency}")
    
    print(f"\n→ 다음 반복에서 개선된 키워드로 재시도합니다...")
    print(f"{'='*80}\n")
    
    return "continue"
