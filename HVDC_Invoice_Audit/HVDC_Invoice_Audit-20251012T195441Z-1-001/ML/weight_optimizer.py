#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeightOptimizer - ML 가중치 최적화
TDD로 구현됨
"""

import pickle
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class WeightOptimizer:
    """
    ML 모델 학습 및 가중치 최적화 클래스
    
    Features:
    - 3가지 모델 학습 (Logistic Regression, Random Forest, Gradient Boosting)
    - Feature importance 기반 가중치 추출
    - 모델 저장/로드
    - 매칭 확률 예측
    """
    
    def __init__(self):
        """초기화"""
        self.models = {
            'logistic': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=5,
                learning_rate=0.1
            )
        }
        self.trained_models = {}
        self.feature_names = ['token_set', 'levenshtein', 'fuzzy_sort']
        self.training_results = {}
        self.X_train = None
        self.y_train = None
    
    def train(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2
    ) -> Dict[str, Dict[str, float]]:
        """
        모델 학습
        
        Args:
            df: 학습 데이터 (columns: token_set, levenshtein, fuzzy_sort, label)
            test_size: 테스트 세트 비율
        
        Returns:
            각 모델의 성능 메트릭
        """
        # 데이터 준비
        X = df[self.feature_names].values
        y = df['label'].values
        
        # Train-Test 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        self.X_train = X_train
        self.y_train = y_train
        
        results = {}
        
        # 각 모델 학습 및 평가
        for model_name, model in self.models.items():
            # 학습
            model.fit(X_train, y_train)
            self.trained_models[model_name] = model
            
            # 예측
            y_pred = model.predict(X_test)
            
            # 메트릭 계산
            results[model_name] = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'f1': f1_score(y_test, y_pred, zero_division=0)
            }
        
        self.training_results = results
        return results
    
    def extract_weights(self, model_name: str = 'random_forest') -> Dict[str, float]:
        """
        Feature importance 기반 가중치 추출
        
        Args:
            model_name: 사용할 모델 이름 (기본: random_forest)
        
        Returns:
            정규화된 가중치 딕셔너리
        """
        if model_name not in self.trained_models:
            raise ValueError(f"모델 '{model_name}'이 학습되지 않았습니다")
        
        model = self.trained_models[model_name]
        
        # Feature importance 추출
        if hasattr(model, 'feature_importances_'):
            # Random Forest, Gradient Boosting
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            # Logistic Regression
            importances = np.abs(model.coef_[0])
        else:
            raise ValueError(f"모델 '{model_name}'에서 feature importance를 추출할 수 없습니다")
        
        # 정규화 (합이 1.0이 되도록)
        normalized = importances / importances.sum()
        
        weights = {
            feature: float(weight)
            for feature, weight in zip(self.feature_names, normalized)
        }
        
        return weights
    
    def save_model(self, output_path: str):
        """
        모델 및 가중치 저장
        
        Args:
            output_path: 출력 파일 경로 (.pkl)
        """
        data = {
            'models': self.trained_models,
            'weights': self.extract_weights(),
            'training_results': self.training_results,
            'feature_names': self.feature_names
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
    
    def load_model(self, input_path: str):
        """
        모델 및 가중치 로드
        
        Args:
            input_path: 입력 파일 경로 (.pkl)
        """
        with open(input_path, 'rb') as f:
            data = pickle.load(f)
        
        self.trained_models = data['models']
        self.training_results = data.get('training_results', {})
        self.feature_names = data.get('feature_names', self.feature_names)
    
    def predict_probability(
        self,
        features: Dict[str, float],
        model_name: str = 'random_forest'
    ) -> float:
        """
        매칭 확률 예측
        
        Args:
            features: 특징 딕셔너리 (token_set, levenshtein, fuzzy_sort)
            model_name: 사용할 모델 이름
        
        Returns:
            매칭 확률 (0~1)
        """
        if model_name not in self.trained_models:
            raise ValueError(f"모델 '{model_name}'이 학습되지 않았습니다")
        
        model = self.trained_models[model_name]
        
        # 특징 벡터 생성
        X = np.array([[
            features['token_set'],
            features['levenshtein'],
            features['fuzzy_sort']
        ]])
        
        # 확률 예측
        prob = model.predict_proba(X)[0][1]  # Positive class 확률
        
        return float(prob)
    
    def get_best_model_name(self) -> str:
        """
        최고 성능 모델 이름 반환
        
        Returns:
            accuracy가 가장 높은 모델 이름
        """
        if not self.training_results:
            raise ValueError("학습된 모델이 없습니다")
        
        best_model = max(
            self.training_results.items(),
            key=lambda x: x[1]['accuracy']
        )[0]
        
        return best_model

