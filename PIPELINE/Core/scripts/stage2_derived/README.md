# Stage 2 - 파생 컬럼 처리 (Derived Columns)

**Samsung C&T Logistics | ADNOC·DSV Partnership**

## 개요

Stage 2는 Stage 1의 동기화된 데이터에 **13개 파생 컬럼**을 자동으로 계산하여 추가합니다.

## 파일 구성

```
stage2_derived/
├── __init__.py                      # 패키지 초기화
├── column_definitions.py            # 컬럼 정의
└── derived_columns_processor.py     # 파생 컬럼 처리 메인 로직
```

## 파생 컬럼 목록 (13개)

### 상태 관련 (6개)
1. **Status_SITE**: 사이트 상태 판별
2. **Status_WAREHOUSE**: 창고 상태 판별
3. **Status_Current**: 현재 상태 (최신 위치)
4. **Status_Location**: 최종 위치
5. **Status_Location_Date**: 위치 변경 날짜
6. **Status_Storage**: 저장 상태 (Indoor/Outdoor)

### 처리량 관련 (5개)
7. **Site_AGI_handling**: 사이트별 처리량
8. **WH_AGI_handling**: 창고별 처리량
9. **Total_AGI_handling**: 총 처리량
10. **Minus**: 차감량
11. **Final_AGI_handling**: 최종 처리량

### 분석 관련 (2개)
12. **Stack_Status**: 적재 상태
13. **SQM**: 면적 계산

## 사용 방법

### 파이프라인 통합 실행
```bash
python run_pipeline.py --stage 2
```

### 입력/출력
- **입력**: `data/processed/synced/*.synced_v3.4.xlsx`
- **출력**: `data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx`

## 기술적 세부사항

- **벡터화 연산**: pandas의 벡터화 연산으로 고성능 처리
- **처리 시간**: 약 16초
- **컬럼 순서 보존**: Stage 1의 컬럼 순서 완벽 유지

---

**버전**: v4.0.12
**최종 업데이트**: 2025-10-22
