#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeightOptimizer 테스트
TDD Red-Green-Refactor 사이클
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from weight_optimizer import WeightOptimizer


class TestWeightOptimizer:
    """WeightOptimizer 클래스 테스트"""
    
    @pytest.fixture
    def sample_training_data(self):
        """테스트용 학습 데이터"""
        np.random.seed(42)
        n_samples = 100
        
        data = []
        for i in range(n_samples):
            # Positive samples (label=1): 높은 유사도
            if i < 50:
                token_set = np.random.uniform(0.7, 1.0)
                levenshtein = np.random.uniform(0.7, 1.0)
                fuzzy_sort = np.random.uniform(0.7, 1.0)
                label = 1
            # Negative samples (label=0): 낮은 유사도
            else:
                token_set = np.random.uniform(0.0, 0.5)
                levenshtein = np.random.uniform(0.0, 0.5)
                fuzzy_sort = np.random.uniform(0.0, 0.5)
                label = 0
            
            data.append({
                'token_set': token_set,
                'levenshtein': levenshtein,
                'fuzzy_sort': fuzzy_sort,
                'label': label
            })
        
        return pd.DataFrame(data)
    
    def test_should_initialize_with_default_models(self):
        """초기화 시 3가지 모델을 가져야 함"""
        optimizer = WeightOptimizer()
        
        assert hasattr(optimizer, 'models')
        assert 'logistic' in optimizer.models
        assert 'random_forest' in optimizer.models
        assert 'gradient_boosting' in optimizer.models
    
    def test_should_train_models_successfully(self, sample_training_data):
        """모델 학습 성공"""
        optimizer = WeightOptimizer()
        
        results = optimizer.train(sample_training_data, test_size=0.2)
        
        assert 'logistic' in results
        assert 'random_forest' in results
        assert 'gradient_boosting' in results
        
        # 각 모델의 정확도 확인
        for model_name, metrics in results.items():
            assert 'accuracy' in metrics
            assert 'precision' in metrics
            assert 'recall' in metrics
            assert 'f1' in metrics
            assert metrics['accuracy'] > 0.5  # 최소 50% 이상
    
    def test_should_extract_optimized_weights(self, sample_training_data):
        """Feature importance 기반 가중치 추출"""
        optimizer = WeightOptimizer()
        optimizer.train(sample_training_data, test_size=0.2)
        
        weights = optimizer.extract_weights()
        
        assert 'token_set' in weights
        assert 'levenshtein' in weights
        assert 'fuzzy_sort' in weights
        
        # 가중치 합이 1.0이어야 함
        assert abs(sum(weights.values()) - 1.0) < 0.01
        
        # 모든 가중치가 양수여야 함
        for weight in weights.values():
            assert weight > 0
    
    def test_should_save_and_load_model(self, sample_training_data, tmp_path):
        """모델 저장 및 로드"""
        optimizer = WeightOptimizer()
        optimizer.train(sample_training_data, test_size=0.2)
        
        model_path = tmp_path / "test_model.pkl"
        optimizer.save_model(str(model_path))
        
        assert model_path.exists()
        
        # 로드
        new_optimizer = WeightOptimizer()
        new_optimizer.load_model(str(model_path))
        
        # 가중치가 동일한지 확인
        original_weights = optimizer.extract_weights()
        loaded_weights = new_optimizer.extract_weights()
        
        for key in original_weights:
            assert abs(original_weights[key] - loaded_weights[key]) < 0.01
    
    def test_should_predict_match_probability(self, sample_training_data):
        """매칭 확률 예측"""
        optimizer = WeightOptimizer()
        optimizer.train(sample_training_data, test_size=0.2)
        
        # 높은 유사도 → 높은 확률
        high_similarity = {
            'token_set': 0.9,
            'levenshtein': 0.85,
            'fuzzy_sort': 0.88
        }
        prob_high = optimizer.predict_probability(high_similarity)
        assert prob_high > 0.7
        
        # 낮은 유사도 → 낮은 확률
        low_similarity = {
            'token_set': 0.3,
            'levenshtein': 0.2,
            'fuzzy_sort': 0.25
        }
        prob_low = optimizer.predict_probability(low_similarity)
        assert prob_low < 0.5
    
    def test_should_return_best_model_name(self, sample_training_data):
        """최고 성능 모델 이름 반환"""
        optimizer = WeightOptimizer()
        results = optimizer.train(sample_training_data, test_size=0.2)
        
        best_model = optimizer.get_best_model_name()
        
        assert best_model in ['logistic', 'random_forest', 'gradient_boosting']
        
        # 최고 성능 모델의 정확도가 다른 모델보다 높거나 같아야 함
        best_accuracy = results[best_model]['accuracy']
        for model_name, metrics in results.items():
            assert best_accuracy >= metrics['accuracy']

