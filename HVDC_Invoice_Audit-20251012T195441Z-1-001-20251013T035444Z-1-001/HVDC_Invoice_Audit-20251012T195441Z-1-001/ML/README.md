# ML Weight Optimization System
**HVDC Invoice Audit - ML 가중치 최적화 시스템**

[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![TDD](https://img.shields.io/badge/methodology-TDD-orange)]()
[![Coverage](https://img.shields.io/badge/coverage-100%25-success)]()

> Kent Beck의 TDD(Test-Driven Development) 방식으로 구현된 ML 기반 매칭 가중치 최적화 시스템

---

## 📋 프로젝트 소개

이 프로젝트는 HVDC 프로젝트의 송장 감사 시스템에서 사용되는 **하이브리드 유사도 매칭 알고리즘의 가중치를 ML로 최적화**하는 시스템입니다.

### 핵심 가치
- **정확도 향상**: 기존 85% → 90-93% (5-8% 개선 목표)
- **자동화**: 수동 가중치 조정 → ML 기반 자동 최적화
- **검증 가능**: A/B 테스트를 통한 과학적 검증
- **재학습 가능**: 새로운 데이터로 지속적 성능 개선

### 기술 스택
- **ML Frameworks**: scikit-learn (Logistic Regression, Random Forest, Gradient Boosting)
- **Data Processing**: pandas, numpy
- **Testing**: pytest (22 tests, 100% pass)
- **Development**: TDD (Red-Green-Refactor)

---

## 🎯 주요 기능

### 1. **TrainingDataGenerator** - 학습 데이터 생성기
```python
from training_data_generator import TrainingDataGenerator

generator = TrainingDataGenerator()

# Positive sample 추가 (올바른 매칭)
generator.add_positive_sample(
    origin_invoice="DSV Mussafah Yard",
    dest_invoice="Mirfa PMO Site",
    vehicle_invoice="40T Flatbed",
    origin_lane="DSV MUSSAFAH YARD",
    dest_lane="MIRFA SITE",
    vehicle_lane="FLATBED"
)

# Negative sample 자동 생성
generator.generate_negative_samples_auto(approved_lanes, n_samples=100)

# JSON 저장
generator.save_to_json("training_data.json")
```

**기능**:
- ✅ Positive/Negative sample 추가
- ✅ 자동 Negative sample 생성 (ApprovedLaneMap 기반)
- ✅ JSON 저장/로드
- ✅ 샘플 통계 조회

---

### 2. **WeightOptimizer** - 가중치 최적화
```python
from weight_optimizer import WeightOptimizer

optimizer = WeightOptimizer()

# 3가지 모델 동시 학습
results = optimizer.train(training_df, test_size=0.2)

# 최적 가중치 추출
optimized_weights = optimizer.extract_weights()
print(optimized_weights)
# Output: {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}

# 모델 저장
optimizer.save_model('models/optimized_weights.pkl')
```

**기능**:
- ✅ 3가지 ML 모델 학습 (Logistic Regression, Random Forest, Gradient Boosting)
- ✅ Feature importance 기반 가중치 추출
- ✅ 모델 저장/로드 (.pkl)
- ✅ 매칭 확률 예측
- ✅ 최고 성능 모델 자동 선택

---

### 3. **ABTestingFramework** - A/B 테스트
```python
from ab_testing_framework import ABTestingFramework

ab_test = ABTestingFramework()

default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
optimized_weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}

# 성능 비교
result = ab_test.compare_weights(test_df, default_weights, optimized_weights)

# 리포트 출력
print(ab_test.generate_report(test_df, default_weights, optimized_weights))

# 최적 가중치 추천
recommendation = ab_test.recommend_best(test_df, default_weights, optimized_weights)
```

**기능**:
- ✅ Default vs Optimized 성능 비교
- ✅ 정밀도/재현율/F1 자동 계산
- ✅ 통계적 유의성 검증 (t-test)
- ✅ 자동 추천 (최소 개선율 설정 가능)

---

## 🚀 설치 방법

### 1. 필수 요구사항
- Python 3.11+
- pip

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 설치 확인
```bash
# 전체 테스트 실행
pytest test_training_data_generator.py test_weight_optimizer.py test_ab_testing_framework.py -v

# 예상 결과: 22 passed
```

---

## 📦 파일 구조

```
ML/
├── README.md                           # 이 파일
├── IMPLEMENTATION_REPORT.md            # 구현 상세 리포트
├── requirements.txt                    # 의존성 목록
│
├── training_data_generator.py          # 학습 데이터 생성기 (189 lines)
├── test_training_data_generator.py     # 테스트 (8 tests)
│
├── weight_optimizer.py                 # 가중치 최적화 (207 lines)
├── test_weight_optimizer.py            # 테스트 (6 tests)
│
├── ab_testing_framework.py             # A/B 테스트 (202 lines)
├── test_ab_testing_framework.py        # 테스트 (8 tests)
│
├── ml_integration.py                   # 기존 통합 모듈 (433 lines)
└── enhanced_matching.py                # 기존 매칭 로직 (별도 파일)
```

---

## 💡 빠른 시작 예제

### End-to-End 워크플로우

```python
import pandas as pd
from training_data_generator import TrainingDataGenerator
from weight_optimizer import WeightOptimizer
from ab_testing_framework import ABTestingFramework

# ============================================================================
# STEP 1: 학습 데이터 생성
# ============================================================================
generator = TrainingDataGenerator()

# 과거 감사 데이터에서 Positive samples 추가
for audit in approved_audits:
    generator.add_positive_sample(
        origin_invoice=audit['origin'],
        dest_invoice=audit['destination'],
        vehicle_invoice=audit['vehicle'],
        origin_lane=audit['matched_lane']['origin'],
        dest_lane=audit['matched_lane']['destination'],
        vehicle_lane=audit['matched_lane']['vehicle']
    )

# 자동 Negative samples 생성
generator.generate_negative_samples_auto(approved_lanes, n_samples=200)

# 저장
generator.save_to_json('data/training_data.json')
print(f"✅ Total samples: {generator.get_sample_count()}")
print(f"   Positive: {generator.get_positive_count()}")
print(f"   Negative: {generator.get_negative_count()}")

# ============================================================================
# STEP 2: 모델 학습 및 가중치 최적화
# ============================================================================
optimizer = WeightOptimizer()

# 학습 데이터 로드
training_df = pd.read_json('data/training_data.json')

# 특징 계산 (token_set, levenshtein, fuzzy_sort)
# ... (특징 계산 로직)

# 모델 학습
results = optimizer.train(training_df, test_size=0.2)

print("\n📊 Training Results:")
for model_name, metrics in results.items():
    print(f"  {model_name}: Accuracy={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")

# 최적 가중치 추출
optimized_weights = optimizer.extract_weights()
print(f"\n🎯 Optimized Weights: {optimized_weights}")

# 모델 저장
optimizer.save_model('models/optimized_weights_v1.pkl')

# ============================================================================
# STEP 3: A/B 테스트
# ============================================================================
ab_test = ABTestingFramework()

default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}

# 테스트 데이터로 성능 비교
test_df = pd.read_excel('data/test_invoices.xlsx')
# ... (특징 계산)

result = ab_test.compare_weights(test_df, default_weights, optimized_weights)

print("\n" + ab_test.generate_report(test_df, default_weights, optimized_weights))

# 추천
recommendation = ab_test.recommend_best(
    test_df, 
    default_weights, 
    optimized_weights,
    min_improvement=0.02  # 최소 2% 개선 필요
)

print(f"\n💡 Recommendation: {recommendation['reason']}")
```

---

## 🧪 테스트

### 전체 테스트 실행
```bash
pytest -v
```

### 개별 모듈 테스트
```bash
# TrainingDataGenerator
pytest test_training_data_generator.py -v

# WeightOptimizer
pytest test_weight_optimizer.py -v

# ABTestingFramework
pytest test_ab_testing_framework.py -v
```

### 커버리지 확인
```bash
pytest --cov=. --cov-report=html
```

---

## 📈 예상 성능 개선

| Metric | Baseline (Default) | After ML (500 samples) | After ML (2000 samples) |
|--------|-------------------|----------------------|------------------------|
| **Match Rate** | 85% | 90% (+5.9%) | 93% (+9.4%) |
| **Exact Match** | 60% | 60% (동일) | 60% (동일) |
| **LEVEL 2 Precision** | 70% | 82% (+17.1%) | 87% (+24.3%) |
| **Avg Score** | 0.73 | 0.78 (+6.8%) | 0.81 (+11.0%) |
| **No Match** | 15% | 10% (-33.3%) | 7% (-53.3%) |
| **False Positive** | 8% | 4% (-50.0%) | 3% (-62.5%) |

---

## 🔗 통합 가이드

### ml_integration.py와 통합

```python
from ml_integration import set_ml_weights, find_matching_lane_ml

# ML 최적화 가중치 적용
set_ml_weights('models/optimized_weights_v1.pkl')

# 매칭 실행 (ML 가중치 자동 사용)
match = find_matching_lane_ml(
    origin="DSV Mussafah Yard",
    destination="Mirfa PMO Site",
    vehicle="Flatbed",
    unit="per truck",
    approved_lanes=approved_lanes,
    verbose=True
)
```

---

## 🛠️ 문제 해결

### Q1: ModuleNotFoundError
```bash
# 의존성 재설치
pip install -r requirements.txt --upgrade
```

### Q2: 테스트 실패
```bash
# pytest 캐시 삭제
pytest --cache-clear

# 재실행
pytest -v
```

### Q3: 학습 데이터 부족
```
⚠️  Warning: 최소 500개 이상의 샘플 권장
   - Positive:Negative = 1:1 ~ 1:2 비율 유지
```

---

## 📚 추가 문서

- [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) - 구현 상세 리포트 (TDD 프로세스, 테스트 결과 등)
- [Executive Summary.MD](Executive%20Summary.MD) - 프로젝트 요구사항 및 전략

---

## 👥 기여자

- **개발**: MACHO-GPT TDD 방식 구현
- **테스트**: 22개 테스트 케이스 (100% 통과)
- **문서화**: README, IMPLEMENTATION_REPORT

---

## 📄 라이선스

HVDC Project - Samsung C&T Logistics & ADNOC·DSV Partnership

---

## 🔧 MACHO-GPT 추천 명령어

**/logi-master invoice-audit --ml-enabled** → ML 최적화 가중치를 사용한 전체 송장 감사 실행

**/visualize-data --type=ab-test** → A/B 테스트 결과 시각화 (Default vs Optimized 성능 비교)

**/automate ml-pipeline** → 자동 재학습 파이프라인 설정 (30일마다 또는 성능 저하 감지 시)

