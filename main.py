"""
NVIDIA 주가 예측 멀티-에이전트 시스템 with LangGraph Feedback Loop

LangGraph를 사용한 피드백 루프 기반 주가 예측 시스템의 메인 실행 파일입니다.
신뢰도가 낮은 분석 결과를 자동으로 개선하는 피드백 메커니즘을 제공합니다.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from google import genai
from newsapi import NewsApiClient

# 설정 및 상수
from config.settings import (
    GEMINI_API_KEY,
    NEWS_API_KEY,
    MAX_ITERATIONS,
    CONFIDENCE_THRESHOLD
)

# 워크플로우 관련
from workflow.graph import get_workflow_graph, print_workflow_diagram
from workflow.state import create_initial_state

# 유틸리티
from utils.output_formatter import (
    print_final_result,
    print_iteration_comparison,
    print_iteration_summary,
    print_error_summary,
    print_timing_summary
)
from utils.file_handler import (
    save_result_to_json,
    save_iteration_history,
    save_workflow_state
)


def setup_logging():
    """
    로깅 설정 초기화
    
    콘솔과 파일에 로그를 기록하도록 설정합니다.
    각 실행마다 타임스탬프가 포함된 로그 파일을 생성합니다.
    """
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 타임스탬프가 포함된 로그 파일명
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"nvidia_predictor_{timestamp}.log"
    
    # 로깅 포맷 설정
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 루트 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 파일 핸들러
            logging.FileHandler(log_file, encoding='utf-8'),
            # 콘솔 핸들러 (WARNING 이상만 출력)
            logging.StreamHandler()
        ]
    )
    
    # 콘솔 핸들러는 WARNING 이상만 출력하도록 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # 루트 로거에 핸들러 추가
    logger = logging.getLogger()
    logger.handlers = [
        logging.FileHandler(log_file, encoding='utf-8'),
        console_handler
    ]
    
    return log_file


def initialize_clients():
    """
    API 클라이언트 초기화
    
    Returns:
        tuple: (genai_client, news_api_client)
    """
    print("\n" + "="*80)
    print("🚀 NVIDIA 주가 예측 멀티-에이전트 시스템 초기화")
    print("="*80)
    
    # Gemini API 클라이언트 초기화
    print("\n📡 Gemini API 클라이언트 초기화 중...")
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini API 클라이언트 초기화 완료")
    
    # NewsAPI 클라이언트 초기화
    print("\n📰 NewsAPI 클라이언트 초기화 중...")
    news_api_client = NewsApiClient(api_key=NEWS_API_KEY)
    print("✅ NewsAPI 클라이언트 초기화 완료")
    
    return genai_client, news_api_client


def run_workflow(max_iterations: int = MAX_ITERATIONS):
    """
    LangGraph 워크플로우 실행
    
    Args:
        max_iterations: 최대 반복 횟수 (기본값: config에서 로드)
    
    Returns:
        dict: 최종 워크플로우 상태
    """
    logger = logging.getLogger(__name__)
    
    # 시작 시간 기록
    start_time = time.time()
    logger.info("="*80)
    logger.info("워크플로우 실행 시작")
    logger.info(f"최대 반복 횟수: {max_iterations}")
    logger.info(f"신뢰도 임계치: {CONFIDENCE_THRESHOLD}%")
    logger.info("="*80)
    
    # 클라이언트 초기화
    genai_client, news_api_client = initialize_clients()
    logger.info("API 클라이언트 초기화 완료")
    
    # 워크플로우 다이어그램 출력
    print_workflow_diagram()
    
    # 워크플로우 그래프 생성
    print("\n🔧 LangGraph 워크플로우 생성 중...")
    logger.info("LangGraph 워크플로우 생성 시작")
    workflow = get_workflow_graph()
    print("✅ 워크플로우 생성 완료")
    logger.info("LangGraph 워크플로우 생성 완료")
    
    # 초기 상태 생성
    print(f"\n📋 초기 상태 생성 (최대 반복: {max_iterations}회)")
    logger.info(f"초기 상태 생성 (최대 반복: {max_iterations}회)")
    initial_state = create_initial_state(max_iterations=max_iterations)
    print(f"✅ 초기 상태 생성 완료")
    print(f"   - 신뢰도 임계치: {CONFIDENCE_THRESHOLD}%")
    print(f"   - 최대 반복 횟수: {max_iterations}회")
    logger.info("초기 상태 생성 완료")
    
    # 워크플로우 실행
    print("\n" + "="*80)
    print("🔄 워크플로우 실행 시작")
    print("="*80)
    
    try:
        # LangGraph 실행 - 클라이언트를 상태에 추가
        initial_state['genai_client'] = genai_client
        initial_state['news_api_client'] = news_api_client
        
        logger.info("LangGraph 워크플로우 실행 시작")
        final_state = workflow.invoke(initial_state)
        
        # 실행 시간 계산
        end_time = time.time()
        execution_time = end_time - start_time
        
        print("\n" + "="*80)
        print("✅ 워크플로우 실행 완료")
        print("="*80)
        print(f"⏱️  총 실행 시간: {execution_time:.2f}초")
        print(f"🔄 총 반복 횟수: {len(final_state.get('all_results', []))}회")
        
        logger.info("="*80)
        logger.info("워크플로우 실행 완료")
        logger.info(f"총 실행 시간: {execution_time:.2f}초")
        logger.info(f"총 반복 횟수: {len(final_state.get('all_results', []))}회")
        
        # 각 반복의 신뢰도 로그
        for result in final_state.get('all_results', []):
            iteration = result.get('iteration', 0)
            confidence = result.get('confidence', 0)
            direction = result.get('analysis', {}).get('direction', 'N/A')
            logger.info(f"반복 {iteration}: 신뢰도 {confidence}%, 방향 {direction}")
        
        logger.info("="*80)
        
        # 실행 시간을 상태에 추가
        final_state['execution_time'] = execution_time
        final_state['timestamp'] = datetime.now().isoformat()
        
        return final_state
        
    except Exception as e:
        print(f"\n❌ 워크플로우 실행 중 오류 발생: {e}")
        logger.error(f"워크플로우 실행 중 오류 발생: {e}", exc_info=True)
        raise


def process_results(final_state: dict):
    """
    워크플로우 결과 처리 및 출력
    
    Args:
        final_state: 최종 워크플로우 상태
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("📊 결과 처리 중...")
    print("="*80)
    
    logger.info("결과 처리 시작")
    
    # 타이밍 요약 출력
    print_timing_summary(final_state)
    
    # 에러 요약 출력
    errors = final_state.get('errors', [])
    if errors:
        print_error_summary(errors)
    
    # 반복 비교 테이블 출력
    all_results = final_state.get('all_results', [])
    if len(all_results) > 1:
        print_iteration_comparison(all_results)
    
    # 최고 결과 선택
    best_result = final_state.get('best_result')
    
    if not best_result:
        print("\n⚠️  유효한 결과를 찾을 수 없습니다.")
        logger.warning("유효한 결과를 찾을 수 없습니다")
        return
    
    # 최종 결과 구성
    final_result = {
        'timestamp': final_state.get('timestamp'),
        'execution_time': final_state.get('execution_time'),
        'total_iterations': len(all_results),
        'best_iteration': best_result.get('iteration'),
        'prediction': {
            'direction': best_result.get('analysis', {}).get('direction', 'Unknown'),
            'confidence': best_result.get('confidence', 0),
            'timeframe': best_result.get('analysis', {}).get('timeframe', 'N/A'),
            'is_valid': best_result.get('confidence', 0) >= CONFIDENCE_THRESHOLD,
            'reason_if_invalid': f"신뢰도 {best_result.get('confidence', 0)}%로 임계치 {CONFIDENCE_THRESHOLD}% 미만" if best_result.get('confidence', 0) < CONFIDENCE_THRESHOLD else None,
            'positive_factors': [e.get('sentence', '') for e in best_result.get('analysis', {}).get('evidences', []) if e.get('sentiment', 0) > 0],
            'negative_factors': [e.get('sentence', '') for e in best_result.get('analysis', {}).get('evidences', []) if e.get('sentiment', 0) < 0],
            'summary': best_result.get('analysis', {}).get('summary', '')
        },
        'analysis_details': {
            'overall_sentiment': best_result.get('analysis', {}).get('overall_sentiment', 0),
            'evidences': best_result.get('analysis', {}).get('evidences', []),
            'validation_notes': best_result.get('validation', {}).get('validation_notes', []),
            'contra_arguments': best_result.get('validation', {}).get('contra_arguments', []),
            'article_count': best_result.get('article_count', 0),
            'keywords_used': best_result.get('keywords', [])
        },
        'iteration_history': all_results
    }
    
    # 최종 결과 출력
    print_final_result(final_result)
    
    # 최종 결과 로그
    logger.info("="*80)
    logger.info("최종 예측 결과")
    logger.info(f"방향: {final_result['prediction']['direction']}")
    logger.info(f"신뢰도: {final_result['prediction']['confidence']}%")
    logger.info(f"예측 기간: {final_result['prediction']['timeframe']}일")
    logger.info(f"유효성: {final_result['prediction']['is_valid']}")
    logger.info(f"최고 반복: {final_result['best_iteration']}/{final_result['total_iterations']}")
    logger.info("="*80)
    
    return final_result


def save_results(final_result: dict, final_state: dict):
    """
    결과를 파일로 저장
    
    Args:
        final_result: 최종 결과 딕셔너리
        final_state: 최종 워크플로우 상태
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("💾 결과 저장 중...")
    print("="*80)
    
    logger.info("결과 저장 시작")
    
    try:
        # 최종 결과 저장
        result_file = save_result_to_json(final_result)
        print(f"✅ 최종 결과 저장 완료: {result_file}")
        logger.info(f"최종 결과 저장 완료: {result_file}")
        
        # 반복 히스토리 저장
        all_results = final_state.get('all_results', [])
        if all_results:
            history_file = save_iteration_history(all_results)
            print(f"✅ 반복 히스토리 저장 완료: {history_file}")
            logger.info(f"반복 히스토리 저장 완료: {history_file}")
        
        # 워크플로우 상태 저장 (디버깅용)
        # 클라이언트 객체는 제외
        state_to_save = {k: v for k, v in final_state.items() 
                        if k not in ['genai_client', 'news_api_client']}
        state_file = save_workflow_state(state_to_save)
        print(f"✅ 워크플로우 상태 저장 완료: {state_file}")
        logger.info(f"워크플로우 상태 저장 완료: {state_file}")
        
        print("\n" + "="*80)
        print("✅ 모든 결과 저장 완료")
        print("="*80)
        logger.info("모든 결과 저장 완료")
        
    except Exception as e:
        print(f"\n⚠️  결과 저장 중 오류 발생: {e}")
        print("결과는 출력되었지만 파일 저장에 실패했습니다.")
        logger.error(f"결과 저장 중 오류 발생: {e}", exc_info=True)


def main():
    """
    메인 실행 함수
    """
    # 로깅 설정
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    print(f"\n📝 로그 파일: {log_file}")
    logger.info("="*80)
    logger.info("NVIDIA 주가 예측 멀티-에이전트 시스템 시작")
    logger.info(f"로그 파일: {log_file}")
    logger.info("="*80)
    
    try:
        # 워크플로우 실행
        final_state = run_workflow(max_iterations=MAX_ITERATIONS)
        
        # 결과 처리
        final_result = process_results(final_state)
        
        # 결과 저장
        if final_result:
            save_results(final_result, final_state)
        
        print("\n" + "="*80)
        print("🎉 프로그램 실행 완료")
        print("="*80 + "\n")
        
        logger.info("="*80)
        logger.info("프로그램 실행 완료")
        logger.info("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        logger.warning("사용자에 의해 중단되었습니다")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        logger.error(f"오류 발생: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()