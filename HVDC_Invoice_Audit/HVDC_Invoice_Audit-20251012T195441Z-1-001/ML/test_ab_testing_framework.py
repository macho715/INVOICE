#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABTestingFramework 테스트
TDD Red-Green-Refactor 사이클
"""

import pytest
import pandas as pd
import numpy as np
from ab_testing_framework import ABTestingFramework


class TestABTestingFramework:
    """ABTestingFramework 클래스 테스트"""
    
    @pytest.fixture
    def sample_test_data(self):
        """테스트용 데이터"""
        np.random.seed(42)
        n_samples = 200
        
        data = []
        for i in range(n_samples):
            # 실제 매칭 여부 (ground truth)
            is_match = np.random.choice([0, 1], p=[0.3, 0.7])  # 70% 매칭
            
            if is_match:
                # 실제 매칭인 경우: 높은 유사도
                token_set = np.random.uniform(0.7, 1.0)
                levenshtein = np.random.uniform(0.7, 1.0) 
                fuzzy_sort = np.random.uniform(0.7, 1.0)
            else:
                # 실제 매칭이 아닌 경우: 낮은 유사도
                token_set = np.random.uniform(0.0, 0.6)
                levenshtein = np.random.uniform(0.0, 0.6)
                fuzzy_sort = np.random.uniform(0.0, 0.6)
            
            data.append({
                'token_set': token_set,
                'levenshtein': levenshtein,
                'fuzzy_sort': fuzzy_sort,
                'actual_match': is_match
            })
        
        return pd.DataFrame(data)
    
    def test_should_initialize_with_default_threshold(self):
        """초기화 시 기본 임계값 설정"""
        framework = ABTestingFramework()
        
        assert hasattr(framework, 'threshold')
        assert framework.threshold == 0.65  # 기본 임계값
    
    def test_should_calculate_hybrid_scores(self, sample_test_data):
        """하이브리드 점수 계산"""
        framework = ABTestingFramework()
        
        # Default weights
        default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        scores = framework.calculate_hybrid_scores(sample_test_data, default_weights)
        
        assert len(scores) == len(sample_test_data)
        assert all(0 <= score <= 1 for score in scores)
    
    def test_should_predict_matches_with_threshold(self, sample_test_data):
        """임계값 기반 매칭 예측"""
        framework = ABTestingFramework(threshold=0.65)
        
        weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        predictions = framework.predict_matches(sample_test_data, weights)
        
        assert len(predictions) == len(sample_test_data)
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_should_calculate_performance_metrics(self, sample_test_data):
        """성능 메트릭 계산"""
        framework = ABTestingFramework()
        
        # 실제값과 예측값
        y_true = sample_test_data['actual_match'].values
        y_pred = np.random.choice([0, 1], size=len(y_true))  # 랜덤 예측
        
        metrics = framework.calculate_metrics(y_true, y_pred)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        
        # 메트릭 범위 확인
        for metric_name, value in metrics.items():
            assert 0 <= value <= 1, f"{metric_name}: {value}"
    
    def test_should_compare_two_weight_sets(self, sample_test_data):
        """두 가중치 세트 성능 비교"""
        framework = ABTestingFramework()
        
        default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        optimized_weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}
        
        result = framework.compare_weights(sample_test_data, default_weights, optimized_weights)
        
        assert 'default' in result
        assert 'optimized' in result
        assert 'improvement' in result
        
        # 각 결과에 메트릭 포함 확인
        for weight_type in ['default', 'optimized']:
            metrics = result[weight_type]
            assert 'accuracy' in metrics
            assert 'precision' in metrics
            assert 'recall' in metrics
            assert 'f1' in metrics
        
        # 개선도 계산 확인
        improvement = result['improvement']
        assert 'accuracy' in improvement
        assert 'precision' in improvement
        assert 'recall' in improvement
        assert 'f1' in improvement
    
    def test_should_perform_statistical_significance_test(self, sample_test_data):
        """통계적 유의성 검증"""
        framework = ABTestingFramework()
        
        # 두 그룹의 정확도 시뮬레이션
        accuracies_A = np.random.uniform(0.80, 0.85, 50)  # Group A
        accuracies_B = np.random.uniform(0.85, 0.90, 50)  # Group B (더 높음)
        
        p_value = framework.statistical_significance_test(accuracies_A, accuracies_B)
        
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1
    
    def test_should_generate_comparison_report(self, sample_test_data):
        """비교 리포트 생성"""
        framework = ABTestingFramework()
        
        default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        optimized_weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}
        
        report = framework.generate_report(sample_test_data, default_weights, optimized_weights)
        
        assert isinstance(report, str)
        assert 'Default' in report
        assert 'Optimized' in report
        assert 'Improvement' in report
        assert 'Accuracy' in report
    
    def test_should_recommend_best_weights(self, sample_test_data):
        """최적 가중치 추천"""
        framework = ABTestingFramework()
        
        default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        optimized_weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}
        
        recommendation = framework.recommend_best(
            sample_test_data, 
            default_weights, 
            optimized_weights,
            min_improvement=0.02  # 최소 2% 개선 필요
        )
        
        assert 'recommended_weights' in recommendation
        assert 'reason' in recommendation
        assert 'improvement_achieved' in recommendation
        
        # 추천된 가중치가 둘 중 하나여야 함
        recommended = recommendation['recommended_weights']
        assert recommended == default_weights or recommended == optimized_weights
