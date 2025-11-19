"""
파일 처리 유틸리티 모듈

워크플로우 실행 결과를 JSON 파일로 저장하고 로드하는 함수들을 제공합니다.
최종 결과, 반복 히스토리, 워크플로우 상태를 파일로 저장할 수 있습니다.
"""
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


def save_result_to_json(result: Dict[str, Any], filename: str = None) -> str:
    """
    결과를 JSON 파일로 저장
    
    Args:
        result: 저장할 결과 딕셔너리
        filename: 파일명 (None이면 자동 생성)
    
    Returns:
        저장된 파일 경로
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"nvidia_multi_agent_{timestamp}.json"
    
    # 파일 경로 생성
    filepath = Path(filename)
    
    # JSON으로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return str(filepath)


def save_iteration_history(all_results: List[Dict[str, Any]], filename: str = None) -> str:
    """
    반복 히스토리를 JSON 파일로 저장
    
    Args:
        all_results: 모든 반복의 결과 리스트
        filename: 파일명 (None이면 자동 생성)
    
    Returns:
        저장된 파일 경로
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"nvidia_iteration_history_{timestamp}.json"
    
    # 파일 경로 생성
    filepath = Path(filename)
    
    # 히스토리 데이터 구성
    history_data = {
        'timestamp': datetime.now().isoformat(),
        'total_iterations': len(all_results),
        'iterations': all_results,
        'summary': _create_history_summary(all_results)
    }
    
    # JSON으로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    return str(filepath)


def _create_history_summary(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    반복 히스토리 요약 생성
    
    모든 반복의 결과를 분석하여 요약 정보를 생성합니다.
    신뢰도 추이, 기사 수 추이, 최고 반복, 개선 메트릭을 포함합니다.
    
    Args:
        all_results: 모든 반복의 결과 리스트
    
    Returns:
        Dict[str, Any]: 요약 딕셔너리
            - confidence_trend: 신뢰도 추이 리스트
            - article_count_trend: 기사 수 추이 리스트
            - best_iteration: 최고 신뢰도 반복 정보
            - improvement_metrics: 개선 메트릭
    """
    if not all_results:
        return {}
    
    # 신뢰도 추이 추출
    confidence_trend = [r.get('confidence', 0) for r in all_results]
    
    # 기사 수 추이 추출
    article_count_trend = [r.get('article_count', 0) for r in all_results]
    
    # 최고 신뢰도 반복 찾기
    best_iteration = max(all_results, key=lambda x: x.get('confidence', 0))
    
    # 개선 메트릭 계산 (첫 번째 vs 마지막 반복)
    first_confidence = all_results[0].get('confidence', 0)
    last_confidence = all_results[-1].get('confidence', 0)
    confidence_improvement = last_confidence - first_confidence
    
    first_articles = all_results[0].get('article_count', 0)
    last_articles = all_results[-1].get('article_count', 0)
    article_increase = last_articles - first_articles
    
    return {
        'confidence_trend': confidence_trend,
        'article_count_trend': article_count_trend,
        'best_iteration': {
            'iteration': best_iteration.get('iteration', 0),
            'confidence': best_iteration.get('confidence', 0),
            'direction': best_iteration.get('analysis', {}).get('direction', 'N/A')
        },
        'improvement_metrics': {
            'confidence_improvement': confidence_improvement,
            'article_increase': article_increase,
            'improved': confidence_improvement > 0
        }
    }


def load_result_from_json(filename: str) -> Dict[str, Any]:
    """
    JSON 파일에서 결과 로드
    
    Args:
        filename: 파일명
    
    Returns:
        결과 딕셔너리
    """
    filepath = Path(filename)
    
    if not filepath.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_workflow_state(state: Dict[str, Any], filename: str = None) -> str:
    """
    워크플로우 상태를 JSON 파일로 저장
    
    Args:
        state: 워크플로우 상태 딕셔너리
        filename: 파일명 (None이면 자동 생성)
    
    Returns:
        저장된 파일 경로
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"workflow_state_{timestamp}.json"
    
    # 파일 경로 생성
    filepath = Path(filename)
    
    # 상태를 직렬화 가능한 형태로 변환
    serializable_state = _make_serializable(state)
    
    # JSON으로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_state, f, ensure_ascii=False, indent=2)
    
    return str(filepath)


def _make_serializable(obj: Any) -> Any:
    """
    객체를 JSON 직렬화 가능한 형태로 변환
    
    재귀적으로 객체를 순회하며 JSON 직렬화 가능한 형태로 변환합니다.
    딕셔너리, 리스트, 데이터클래스, 일반 객체를 처리합니다.
    
    Args:
        obj: 변환할 객체 (Any 타입)
    
    Returns:
        Any: JSON 직렬화 가능한 객체
            - dict, list, str, int, float, bool, None 등
    
    Note:
        데이터클래스나 __dict__ 속성을 가진 객체는 딕셔너리로 변환됩니다.
    """
    if isinstance(obj, dict):
        # 딕셔너리의 모든 값을 재귀적으로 변환
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # 리스트의 모든 항목을 재귀적으로 변환
        return [_make_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # 데이터클래스나 객체를 딕셔너리로 변환
        return _make_serializable(obj.__dict__)
    else:
        # 기본 타입은 그대로 반환
        return obj
