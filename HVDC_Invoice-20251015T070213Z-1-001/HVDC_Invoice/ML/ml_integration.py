#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Matching + ML Integration
===================================
ML 최적화 가중치를 적용한 하이브리드 매칭 시스템
"""

import pickle
from pathlib import Path
from typing import Dict, Optional
from enhanced_matching import (
    token_set_similarity,
    levenshtein_similarity,
    fuzzy_token_sort_similarity,
    normalize_location,
    normalize_vehicle,
    get_region,
    get_vehicle_group,
    REGION_MAP,
    VEHICLE_GROUPS
)


# ============================================================================
# ML WEIGHTS LOADER
# ============================================================================

class MLWeightsManager:
    """
    ML 학습된 가중치 관리 클래스
    - 가중치 로드/저장
    - Fallback to default weights
    """
    
    DEFAULT_WEIGHTS = {
        'token_set': 0.4,
        'levenshtein': 0.3,
        'fuzzy_sort': 0.3
    }
    
    def __init__(self, model_path: Optional[str] = None):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.is_ml_optimized = False
        
        if model_path and Path(model_path).exists():
            self.load_weights(model_path)
    
    def load_weights(self, model_path: str):
        """
        ML 학습된 가중치 로드
        
        Args:
            model_path: .pkl 모델 파일 경로
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            if 'weights' in model_data:
                self.weights = model_data['weights']
                self.is_ml_optimized = True
                print(f"✅ ML optimized weights loaded from {model_path}")
                print(f"  Weights: {self.weights}")
            else:
                print(f"⚠️  No weights found in {model_path}, using default")
        
        except Exception as e:
            print(f"❌ Failed to load weights: {e}")
            print(f"   Using default weights: {self.DEFAULT_WEIGHTS}")
    
    def get_weights(self) -> Dict[str, float]:
        """현재 가중치 반환"""
        return self.weights
    
    def is_optimized(self) -> bool:
        """ML 최적화 여부"""
        return self.is_ml_optimized


# ============================================================================
# ENHANCED HYBRID SIMILARITY WITH ML WEIGHTS
# ============================================================================

# Global weights manager (singleton pattern)
_weights_manager = MLWeightsManager()


def set_ml_weights(model_path: str):
    """
    ML 최적화 가중치 적용
    
    Usage:
        set_ml_weights('models/optimized_weights.pkl')
        # 이후 모든 hybrid_similarity_ml 호출에 적용됨
    """
    global _weights_manager
    _weights_manager = MLWeightsManager(model_path)


def get_current_weights() -> Dict[str, float]:
    """현재 사용 중인 가중치 반환"""
    return _weights_manager.get_weights()


def hybrid_similarity_ml(s1: str, s2: str) -> float:
    """
    ML 최적화 가중치를 사용하는 하이브리드 유사도
    
    Args:
        s1, s2: 비교할 문자열
    
    Returns:
        가중 평균 유사도 (0~1)
    """
    weights = _weights_manager.get_weights()
    
    scores = {
        "token_set": token_set_similarity(s1, s2),
        "levenshtein": levenshtein_similarity(s1, s2),
        "fuzzy_sort": fuzzy_token_sort_similarity(s1, s2)
    }
    
    # ML 학습된 가중치로 계산
    total_score = sum(scores[key] * weights[key] for key in weights)
    
    return total_score


# ============================================================================
# ENHANCED MATCHING WITH ML
# ============================================================================

def find_matching_lane_ml(
    origin: str,
    destination: str,
    vehicle: str,
    unit: str,
    approved_lanes: list,
    verbose: bool = False
) -> Optional[Dict]:
    """
    ML 최적화 가중치를 사용하는 4단계 매칭 시스템
    
    기존 find_matching_lane_enhanced()와 동일하지만
    hybrid_similarity 대신 hybrid_similarity_ml 사용
    """
    
    # 정규화
    origin_norm = normalize_location(origin)
    dest_norm = normalize_location(destination)
    vehicle_norm = normalize_vehicle(vehicle)
    
    if verbose:
        print(f"\n[ML MATCHING] {origin} → {destination} ({vehicle})")
        print(f"  Normalized: {origin_norm} → {dest_norm} ({vehicle_norm})")
        print(f"  Using weights: {get_current_weights()}")
    
    best_match = None
    best_score = 0.0
    
    # ========================================================================
    # LEVEL 1: 정확 매칭 (변경 없음)
    # ========================================================================
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        if (lane_origin == origin_norm and
            lane_dest == dest_norm and
            lane_vehicle == vehicle_norm and
            lane_unit == str(unit)):
            
            if verbose:
                print(f"  ✅ LEVEL 1 (EXACT): Lane {i} matched!")
            
            return {
                "row_index": i + 2,
                "match_score": 1.0,
                "match_level": "EXACT",
                "lane_data": lane
            }
    
    # ========================================================================
    # LEVEL 2: ML 최적화 유사도 매칭
    # ========================================================================
    for i, lane in enumerate(approved_lanes):
        lane_origin = lane.get("origin", "")
        lane_dest = lane.get("destination", "")
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        if lane_vehicle != vehicle_norm or lane_unit != str(unit):
            continue
        
        # 🆕 ML 최적화 하이브리드 유사도 사용
        origin_sim = hybrid_similarity_ml(origin, lane_origin)
        dest_sim = hybrid_similarity_ml(destination, lane_dest)
        
        # 가중 평균 (Origin 60%, Destination 40%)
        total_sim = 0.6 * origin_sim + 0.4 * dest_sim
        
        # 임계값: 0.65 이상
        if total_sim > best_score and total_sim >= 0.65:
            best_match = {
                "row_index": i + 2,
                "match_score": total_sim,
                "match_level": "SIMILARITY_ML",  # ML 사용 표시
                "lane_data": lane
            }
            best_score = total_sim
    
    if best_match and verbose:
        print(f"  ✅ LEVEL 2 (ML SIMILARITY): Lane {best_match['row_index']-2} "
              f"matched (score: {best_score:.2f})")
    
    if best_match:
        return best_match
    
    # ========================================================================
    # LEVEL 3: 권역별 매칭 (변경 없음)
    # ========================================================================
    origin_region = get_region(origin_norm)
    dest_region = get_region(dest_norm)
    
    if origin_region and dest_region:
        for i, lane in enumerate(approved_lanes):
            lane_origin = normalize_location(lane.get("origin", ""))
            lane_dest = normalize_location(lane.get("destination", ""))
            lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
            lane_unit = str(lane.get("unit", "per truck"))
            
            if lane_vehicle != vehicle_norm or lane_unit != str(unit):
                continue
            
            lane_origin_region = get_region(lane_origin)
            lane_dest_region = get_region(lane_dest)
            
            if lane_origin_region == origin_region and lane_dest_region == dest_region:
                score = 0.5
                
                if score > best_score:
                    best_match = {
                        "row_index": i + 2,
                        "match_score": score,
                        "match_level": "REGION",
                        "lane_data": lane
                    }
                    best_score = score
        
        if best_match and verbose:
            print(f"  ✅ LEVEL 3 (REGION): Lane {best_match['row_index']-2} "
                  f"matched (region: {origin_region}→{dest_region})")
    
    if best_match:
        return best_match
    
    # ========================================================================
    # LEVEL 4: 차량 타입별 매칭 (ML 유사도 적용)
    # ========================================================================
    vehicle_group = get_vehicle_group(vehicle_norm)
    
    if vehicle_group:
        for i, lane in enumerate(approved_lanes):
            lane_origin = normalize_location(lane.get("origin", ""))
            lane_dest = normalize_location(lane.get("destination", ""))
            lane_vehicle = lane.get("vehicle", "")
            lane_unit = str(lane.get("unit", "per truck"))
            
            if lane_unit != str(unit):
                continue
            
            lane_vehicle_group = get_vehicle_group(lane_vehicle)
            
            if lane_vehicle_group == vehicle_group:
                # 🆕 ML 최적화 유사도 사용
                origin_sim = hybrid_similarity_ml(origin, lane_origin)
                dest_sim = hybrid_similarity_ml(destination, lane_dest)
                total_sim = 0.6 * origin_sim + 0.4 * dest_sim
                
                if total_sim >= 0.4 and total_sim > best_score:
                    best_match = {
                        "row_index": i + 2,
                        "match_score": total_sim,
                        "match_level": "VEHICLE_TYPE_ML",  # ML 사용 표시
                        "lane_data": lane
                    }
                    best_score = total_sim
        
        if best_match and verbose:
            print(f"  ✅ LEVEL 4 (ML VEHICLE_TYPE): Lane {best_match['row_index']-2} "
                  f"matched (group: {vehicle_group}, score: {best_score:.2f})")
    
    if best_match:
        return best_match
    
    if verbose:
        print(f"  ❌ NO MATCH")
    
    return None


# ============================================================================
# BATCH PROCESSING WITH ML
# ============================================================================

def batch_match_with_ml(
    items_df,
    approved_lanes: list,
    model_path: Optional[str] = None,
    verbose: bool = False
) -> list:
    """
    배치 매칭 (ML 가중치 적용)
    
    Args:
        items_df: 송장 아이템 DataFrame
        approved_lanes: ApprovedLaneMap 레인 리스트
        model_path: ML 모델 경로 (None이면 default weights 사용)
        verbose: 상세 로그
    
    Returns:
        매칭 결과 리스트
    """
    # ML 가중치 설정
    if model_path:
        set_ml_weights(model_path)
    
    results = []
    
    for i, row in items_df.iterrows():
        origin = row.get("origin", "")
        destination = row.get("destination", "")
        vehicle = row.get("vehicle", "")
        unit = row.get("unit", "per truck")
        
        match_result = find_matching_lane_ml(
            origin, destination, vehicle, unit,
            approved_lanes, verbose=verbose
        )
        
        results.append({
            'item_index': i,
            'origin': origin,
            'destination': destination,
            'vehicle': vehicle,
            'match_result': match_result
        })
    
    # 통계 출력
    if verbose:
        total = len(results)
        matched = sum(1 for r in results if r['match_result'] is not None)
        exact = sum(1 for r in results if r['match_result'] and 
                   r['match_result']['match_level'] == 'EXACT')
        ml_sim = sum(1 for r in results if r['match_result'] and 
                    'ML' in r['match_result']['match_level'])
        
        print(f"\n{'='*80}")
        print(f"📊 Batch Matching Results (ML)")
        print(f"{'='*80}")
        print(f"  Total items: {total}")
        print(f"  Matched: {matched} ({matched/total*100:.1f}%)")
        print(f"  - EXACT: {exact}")
        print(f"  - ML-enhanced: {ml_sim}")
        print(f"  No match: {total - matched}")
        print(f"  Using weights: {get_current_weights()}")
        print(f"  Optimized: {'✅' if _weights_manager.is_optimized() else '❌'}")
    
    return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import pandas as pd
    
    print("="*80)
    print("Enhanced Matching with ML Integration - Example")
    print("="*80)
    
    # 1. ML 가중치 로드
    print("\n[STEP 1] Loading ML optimized weights...")
    set_ml_weights('models/optimized_weights.pkl')  # 실제 경로로 변경
    
    # 2. 테스트 데이터
    test_items = pd.DataFrame([
        {
            'origin': 'DSV Mussafah Yard',
            'destination': 'Mirfa PMO Site',
            'vehicle': 'Flatbed',
            'unit': 'per truck'
        },
        {
            'origin': 'M44 WH',
            'destination': 'Shuweihat Power',
            'vehicle': 'Low Bed',
            'unit': 'per truck'
        }
    ])
    
    # 3. ApprovedLaneMap (예시)
    approved_lanes = [
        {
            'origin': 'DSV MUSSAFAH YARD',
            'destination': 'MIRFA SITE',
            'vehicle': 'FLATBED',
            'unit': 'per truck',
            'cost': 5000
        },
        {
            'origin': 'M44 WAREHOUSE',
            'destination': 'SHUWEIHAT SITE',
            'vehicle': 'TRAILER',
            'unit': 'per truck',
            'cost': 6500
        }
    ]
    
    # 4. 배치 매칭
    print("\n[STEP 2] Running batch matching with ML...")
    results = batch_match_with_ml(
        test_items,
        approved_lanes,
        verbose=True
    )
    
    print("\n✅ Example completed!")
