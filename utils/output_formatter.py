"""
출력 포맷팅 유틸리티 모듈

워크플로우 실행 결과를 사용자 친화적인 형식으로 출력하는 함수들을 제공합니다.
최종 예측 결과, 반복 비교, 에러 요약, 타이밍 정보 등을 포맷팅합니다.
"""
from typing import Dict, Any, List


def print_final_result(result: Dict[str, Any]) -> None:
    """
    최종 예측 결과를 보기 좋게 출력
    
    예측 방향, 신뢰도, 긍정/부정 요인, 분석 요약 등을 포맷팅하여 출력합니다.
    신뢰도가 임계치 미만인 경우 예측 보류 메시지를 표시합니다.
    
    Args:
        result: 최종 결과 딕셔너리
            - prediction: 예측 정보 (direction, confidence, timeframe 등)
            - analysis_details: 분석 상세 정보 (선택적)
    
    Example:
        >>> print_final_result({
        ...     'prediction': {
        ...         'direction': 'Up',
        ...         'confidence': 75,
        ...         'is_valid': True,
        ...         'positive_factors': ['실적 호조'],
        ...         'negative_factors': ['규제 리스크']
        ...     }
        ... })
    """
    
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


def print_iteration_comparison(all_results: List[Dict[str, Any]]) -> None:
    """
    반복 간 비교 테이블 출력
    
    각 반복의 신뢰도, 방향, 기사 수, 키워드 수를 테이블 형식으로 출력하고,
    첫 번째와 마지막 반복을 비교하여 개선 메트릭을 표시합니다.
    
    Args:
        all_results: 모든 반복의 결과 리스트
            각 결과는 iteration, confidence, analysis, article_count, keywords 포함
    
    Example:
        >>> print_iteration_comparison([
        ...     {'iteration': 1, 'confidence': 45, 'analysis': {'direction': 'Up'}},
        ...     {'iteration': 2, 'confidence': 65, 'analysis': {'direction': 'Up'}}
        ... ])
    """
    
    if not all_results:
        print("\n비교할 결과가 없습니다.")
        return
    
    print("\n" + "="*80)
    print("🔄 반복 비교 테이블")
    print("="*80)
    
    # 테이블 헤더
    print(f"\n{'반복':^6} | {'신뢰도':^8} | {'방향':^8} | {'기사수':^8} | {'키워드수':^10}")
    print("-" * 60)
    
    # 각 반복 결과
    for result in all_results:
        iteration = result.get('iteration', 0)
        confidence = result.get('confidence', 0)
        direction = result.get('analysis', {}).get('direction', 'N/A')
        article_count = result.get('article_count', 0)
        keyword_count = len(result.get('keywords', []))
        
        print(f"{iteration:^6} | {confidence:^8}% | {direction:^8} | {article_count:^8} | {keyword_count:^10}")
    
    # 개선 메트릭
    if len(all_results) > 1:
        first = all_results[0]
        last = all_results[-1]
        
        conf_improvement = last.get('confidence', 0) - first.get('confidence', 0)
        article_increase = last.get('article_count', 0) - first.get('article_count', 0)
        
        print("\n" + "-" * 60)
        print("📈 개선 메트릭:")
        print(f"   신뢰도 변화: {conf_improvement:+d}%")
        print(f"   기사 수 증가: {article_increase:+d}개")
        
        if conf_improvement > 0:
            print(f"   ✅ 피드백 루프가 {conf_improvement}% 신뢰도를 개선했습니다!")
        elif conf_improvement == 0:
            print(f"   ➡️  신뢰도 변화 없음")
        else:
            print(f"   ⚠️  신뢰도가 감소했습니다")
    
    print("="*80)


def print_iteration_summary(state: Dict[str, Any]) -> None:
    """
    현재 반복 상태 요약 출력
    
    현재 반복 번호, 이전 신뢰도, 부족한 점, 반대 근거 등을 출력합니다.
    피드백 루프 진행 상황을 사용자에게 알려줍니다.
    
    Args:
        state: 워크플로우 상태 딕셔너리
            - iteration: 현재 반복 번호
            - max_iterations: 최대 반복 횟수
            - iteration_contexts: 반복 컨텍스트 리스트
    
    Example:
        >>> print_iteration_summary({
        ...     'iteration': 2,
        ...     'max_iterations': 3,
        ...     'iteration_contexts': [context1]
        ... })
    """
    
    iteration = state.get('iteration', 0)
    max_iterations = state.get('max_iterations', 3)
    
    print(f"\n{'='*80}")
    print(f"🔄 반복 {iteration}/{max_iterations}")
    print(f"{'='*80}")
    
    # 현재 컨텍스트 정보
    contexts = state.get('iteration_contexts', [])
    if contexts:
        latest_context = contexts[-1]
        print(f"\n이전 신뢰도: {latest_context.previous_confidence}%")
        
        if latest_context.deficiencies:
            print(f"\n부족한 점:")
            for deficiency in latest_context.deficiencies:
                print(f"   • {deficiency}")
        
        if latest_context.contra_arguments:
            print(f"\n반대 근거:")
            for arg in latest_context.contra_arguments:
                print(f"   • {arg}")
    
    print(f"{'='*80}\n")


def print_error_summary(errors: List[Dict[str, Any]]) -> None:
    """
    에러 요약 출력
    
    워크플로우 실행 중 발생한 에러를 노드별로 그룹화하여 출력합니다.
    각 에러의 발생 반복, 에러 메시지, 폴백 전략을 표시합니다.
    
    Args:
        errors: 에러 리스트
            각 에러는 node, iteration, error, fallback 필드 포함
    
    Example:
        >>> print_error_summary([
        ...     {'node': 'keyword_generation', 'iteration': 1, 
        ...      'error': 'API timeout', 'fallback': 'default_keywords'}
        ... ])
    """
    
    if not errors:
        return
    
    print("\n" + "="*80)
    print("⚠️  워크플로우 에러 요약")
    print("="*80)
    
    # 노드별 에러 그룹화
    errors_by_node = {}
    for error in errors:
        node = error.get('node', 'unknown')
        if node not in errors_by_node:
            errors_by_node[node] = []
        errors_by_node[node].append(error)
    
    # 노드별 출력
    for node, node_errors in errors_by_node.items():
        print(f"\n📍 {node}:")
        for error in node_errors:
            iteration = error.get('iteration', '?')
            error_msg = error.get('error', 'Unknown error')
            fallback = error.get('fallback', 'none')
            print(f"   반복 {iteration}: {error_msg}")
            print(f"   → 폴백: {fallback}")
    
    print("\n" + "="*80)


def print_timing_summary(state: Dict[str, Any]) -> None:
    """
    타이밍 요약 출력
    
    워크플로우 시작 시간, 각 반복의 타임스탬프, 총 실행 시간, 평균 반복 시간을 출력합니다.
    성능 분석과 디버깅에 유용합니다.
    
    Args:
        state: 워크플로우 상태 딕셔너리
            - start_time: 시작 시간 (ISO 형식)
            - iteration_timestamps: 반복별 타임스탬프 리스트
    
    Example:
        >>> print_timing_summary({
        ...     'start_time': '2024-01-01T10:00:00',
        ...     'iteration_timestamps': [
        ...         {'iteration': 1, 'timestamp': '2024-01-01T10:05:00', 'confidence': 45}
        ...     ]
        ... })
    """
    
    start_time_str = state.get('start_time')
    iteration_timestamps = state.get('iteration_timestamps', [])
    
    if not start_time_str or not iteration_timestamps:
        return
    
    from datetime import datetime
    
    print("\n" + "="*80)
    print("⏱️  타이밍 요약")
    print("="*80)
    
    start_time = datetime.fromisoformat(start_time_str)
    
    print(f"\n시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 각 반복의 타임스탬프
    print(f"\n반복별 타임스탬프:")
    for ts_info in iteration_timestamps:
        iteration = ts_info.get('iteration', '?')
        timestamp = datetime.fromisoformat(ts_info.get('timestamp', ''))
        confidence = ts_info.get('confidence', 0)
        has_error = ts_info.get('has_error', False)
        
        elapsed = (timestamp - start_time).total_seconds()
        error_marker = " ⚠️" if has_error else ""
        
        print(f"   반복 {iteration}: {timestamp.strftime('%H:%M:%S')} "
              f"(+{elapsed:.1f}초) - 신뢰도 {confidence}%{error_marker}")
    
    # 총 실행 시간
    if iteration_timestamps:
        last_timestamp = datetime.fromisoformat(iteration_timestamps[-1].get('timestamp', ''))
        total_elapsed = (last_timestamp - start_time).total_seconds()
        print(f"\n총 실행 시간: {total_elapsed:.1f}초")
        print(f"평균 반복 시간: {total_elapsed / len(iteration_timestamps):.1f}초")
    
    print("="*80)
