#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABTestingFramework - A/B 테스트 프레임워크
TDD로 구현됨
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class ABTestingFramework:
    """
    A/B 테스트 프레임워크 - 가중치 성능 비교
    
    Features:
    - Default vs Optimized weights 성능 비교
    - 정밀도/재현율/F1 계산
    - 통계적 유의성 검증
    - 성능 리포트 생성
    """
    
    def __init__(self, threshold: float = 0.65):
        """
        초기화
        
        Args:
            threshold: 매칭 판정 임계값
        """
        self.threshold = threshold
    
    def calculate_hybrid_scores(
        self,
        df: pd.DataFrame,
        weights: Dict[str, float]
    ) -> np.ndarray:
        """
        하이브리드 유사도 점수 계산
        
        Args:
            df: 특징 데이터 (token_set, levenshtein, fuzzy_sort 컬럼)
            weights: 가중치 딕셔너리
        
        Returns:
            하이브리드 점수 배열
        """
        scores = (
            df['token_set'] * weights['token_set'] +
            df['levenshtein'] * weights['levenshtein'] + 
            df['fuzzy_sort'] * weights['fuzzy_sort']
        )
        
        return scores.values
    
    def predict_matches(
        self,
        df: pd.DataFrame,
        weights: Dict[str, float]
    ) -> np.ndarray:
        """
        매칭 예측 (임계값 기반)
        
        Args:
            df: 특징 데이터
            weights: 가중치 딕셔너리
        
        Returns:
            매칭 예측 결과 (0 또는 1)
        """
        scores = self.calculate_hybrid_scores(df, weights)
        predictions = (scores >= self.threshold).astype(int)
        
        return predictions
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """
        성능 메트릭 계산
        
        Args:
            y_true: 실제값
            y_pred: 예측값
        
        Returns:
            메트릭 딕셔너리 (accuracy, precision, recall, f1)
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0)
        }
        
        return metrics
    
    def compare_weights(
        self,
        df: pd.DataFrame,
        default_weights: Dict[str, float],
        optimized_weights: Dict[str, float]
    ) -> Dict:
        """
        두 가중치 세트 성능 비교
        
        Args:
            df: 테스트 데이터 (actual_match 컬럼 포함)
            default_weights: 기본 가중치
            optimized_weights: 최적화된 가중치
        
        Returns:
            비교 결과 딕셔너리
        """
        y_true = df['actual_match'].values
        
        # Default weights 성능
        pred_default = self.predict_matches(df, default_weights)
        metrics_default = self.calculate_metrics(y_true, pred_default)
        
        # Optimized weights 성능
        pred_optimized = self.predict_matches(df, optimized_weights)
        metrics_optimized = self.calculate_metrics(y_true, pred_optimized)
        
        # 개선도 계산
        improvement = {}
        for metric in metrics_default:
            default_val = metrics_default[metric]
            optimized_val = metrics_optimized[metric]
            
            if default_val > 0:
                improvement[metric] = (optimized_val - default_val) / default_val
            else:
                improvement[metric] = 0.0
        
        return {
            'default': metrics_default,
            'optimized': metrics_optimized,
            'improvement': improvement
        }
    
    def statistical_significance_test(
        self,
        accuracies_A: np.ndarray,
        accuracies_B: np.ndarray
    ) -> float:
        """
        통계적 유의성 검증 (t-test)
        
        Args:
            accuracies_A: 그룹 A의 정확도 배열
            accuracies_B: 그룹 B의 정확도 배열
        
        Returns:
            p-value
        """
        try:
            statistic, p_value = stats.ttest_ind(accuracies_A, accuracies_B)
            return float(p_value)
        except:
            return 1.0  # 테스트 실패 시 유의하지 않음으로 처리
    
    def generate_report(
        self,
        df: pd.DataFrame,
        default_weights: Dict[str, float],
        optimized_weights: Dict[str, float]
    ) -> str:
        """
        비교 리포트 생성
        
        Args:
            df: 테스트 데이터
            default_weights: 기본 가중치
            optimized_weights: 최적화된 가중치
        
        Returns:
            리포트 문자열
        """
        comparison = self.compare_weights(df, default_weights, optimized_weights)
        
        report = f"""
A/B Testing Results
==================

Metric          Default      Optimized    Improvement
-------------------------------------------------------
Accuracy        {comparison['default']['accuracy']:.4f}       {comparison['optimized']['accuracy']:.4f}       {comparison['improvement']['accuracy']:+.2%}
Precision       {comparison['default']['precision']:.4f}       {comparison['optimized']['precision']:.4f}       {comparison['improvement']['precision']:+.2%}
Recall          {comparison['default']['recall']:.4f}       {comparison['optimized']['recall']:.4f}       {comparison['improvement']['recall']:+.2%}
F1              {comparison['default']['f1']:.4f}       {comparison['optimized']['f1']:.4f}       {comparison['improvement']['f1']:+.2%}

Weights Configuration:
Default:    {default_weights}
Optimized:  {optimized_weights}

Test Data: {len(df)} samples
Threshold: {self.threshold}
        """.strip()
        
        return report
    
    def recommend_best(
        self,
        df: pd.DataFrame,
        default_weights: Dict[str, float],
        optimized_weights: Dict[str, float],
        min_improvement: float = 0.02
    ) -> Dict:
        """
        최적 가중치 추천
        
        Args:
            df: 테스트 데이터
            default_weights: 기본 가중치
            optimized_weights: 최적화된 가중치
            min_improvement: 최소 개선 임계값 (2% = 0.02)
        
        Returns:
            추천 결과
        """
        comparison = self.compare_weights(df, default_weights, optimized_weights)
        
        # F1 점수 기준으로 판단
        f1_improvement = comparison['improvement']['f1']
        accuracy_improvement = comparison['improvement']['accuracy']
        
        if f1_improvement >= min_improvement:
            return {
                'recommended_weights': optimized_weights,
                'reason': f'Optimized weights show {f1_improvement:.2%} F1 improvement',
                'improvement_achieved': f1_improvement
            }
        elif accuracy_improvement >= min_improvement:
            return {
                'recommended_weights': optimized_weights,
                'reason': f'Optimized weights show {accuracy_improvement:.2%} accuracy improvement',
                'improvement_achieved': accuracy_improvement
            }
        else:
            return {
                'recommended_weights': default_weights,
                'reason': f'Insufficient improvement (F1: {f1_improvement:.2%}, min required: {min_improvement:.2%})',
                'improvement_achieved': max(f1_improvement, accuracy_improvement)
            }
