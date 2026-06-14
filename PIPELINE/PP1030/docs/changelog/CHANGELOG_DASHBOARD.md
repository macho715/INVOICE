CHANGELOG_DASHBOARD.MD
## [4.0.48] - 2025-10-28

### ✨ Added - DSV Al Markaz Dashboard Ultimate Edition with Aisle Map & Bottleneck Analysis

#### 주요 기능

- **Aisle Map 통합**: `almk_aisle_map.csv` 데이터를 대시보드에 병합 (523 cases matched)
- **Aisle별 점유율 차트**: A1-A8 Aisle별 케이스 수 및 SQM 사용량 시각화
- **병목 구간 분석**: 90일 이상 체류 케이스를 Aisle별로 분석하여 색상 코드로 표시
  - 빨강: 365일 이상 (1년+)
  - 주황: 180-365일 (6개월-1년)
  - 연주황: 90-180일 (3-6개월)
- **대시보드 레이아웃 확장**: 3x2 → 4x2 그리드 (Aisle Map 데이터가 있을 경우)

#### 기술 구현

- `load_data()` 함수에 `aisle_map_path` 매개변수 추가
- Case No.를 기준으로 `aisle_code`, `slot_code`, `side`, `area_sqm` 컬럼 병합
- Aisle별 집계: 케이스 수, Effective SQM, 평균 체류 시간
- 병목 케이스 필터링 (Dwell_Days >= 90) 및 시각화
- 동적 차트 행 번호 조정 (Heatmap을 row 3 또는 row 4로 배치)

#### 변경 파일

- `scripts/analysis/dsv_almarkaz_ultimate_dashboard.py`:
  - `load_data()`: Aisle Map CSV 로드 및 병합 로직 추가 (Lines 22-84)
  - `create_dashboard()`: Aisle 분석 데이터 생성 (Lines 246-268)
  - `create_dashboard()`: 동적 레이아웃 (4x2 vs 3x2) (Lines 270-317)
  - `create_dashboard()`: Aisle 차트 추가 (Lines 391-434)
  - `main()`: `--aisle-map` 인자 추가 (Lines 504-510)
- `almk_aisle_map.csv`: 신규 데이터 소스 (523 cases, 6 columns)

#### 실행 결과

```
[INFO] Loading Aisle Map from: almk_aisle_map.csv
[OK] Aisle Map merged: 523 cases matched
[Ultimate KPIs]
  - Total Cases: 5,039
  - Stackable: 13.6%
  - SQM Used: 18,260.3
  - Utilization: 576.4%
  - Avg Dwell: 297 days
```

#### 다음 단계 (미완료)

- Sankey diagram으로 Location 간 이동 흐름 시각화
- 임계값 기반 실시간 경고 시스템
- 데이터 캐싱 및 차트 렌더링 최적화

---