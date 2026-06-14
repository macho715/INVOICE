# DN_NOT_FOUND 미매칭 원인 상세 분석 보고서

**생성 일시**: 2025-10-13 21:52:00
**시스템**: HVDC Invoice Audit - DN PDF 검증 (PATCH2)
**분석 대상**: 24개 미매칭 인보이스 항목

---

## 📊 미매칭 현황

| 항목 | 개수 | 비율 |
|------|------|------|
| 총 인보이스 | 44 | 100% |
| DN 파싱 성공 | 33 | - |
| **매칭 성공** | **20** | **45.5%** |
| **미매칭** | **24** | **54.5%** |

---

## 🔍 미매칭 원인 분석

### 원인별 분류

| 원인 | 건수 | 비율 | 설명 |
|------|------|------|------|
| **DN_CAPACITY_EXHAUSTED** | **22** | **91.7%** | DN이 이미 다른 인보이스에 할당됨 |
| **BELOW_MIN_SCORE** | **2** | **8.3%** | 최고 점수 < 0.40 (임계값 미달) |
| **NO_CANDIDATES** | **0** | **0%** | 후보 DN 없음 |

### 핵심 발견 🎯

**대부분(91.7%)이 DN capacity 소진 때문!**

즉, 미매칭 인보이스들도 높은 점수를 받았지만:
- 점수가 더 높은 다른 인보이스가 먼저 DN을 선점
- 1:1 매칭 제약으로 할당받지 못함

---

## 📈 미매칭 항목의 점수 분포

### 통계

| 지표 | 값 |
|------|-----|
| 평균 최고 점수 | **0.612** |
| 중앙값 | **0.613** |
| 최소 | 0.113 |
| 최대 | **0.900** |

### 점수 구간별 분포

| 구간 | 건수 | 비율 | 평가 |
|------|------|------|------|
| < 0.20 | 1 | 4.2% | 매우 낮음 (매칭 어려움) |
| 0.20~0.30 | 0 | 0% | 낮음 |
| 0.30~0.40 | 1 | 4.2% | 임계값 직전 (조정 시 매칭 가능) |
| **>= 0.40** | **22** | **91.7%** | **임계값 충족했으나 DN 소진** ⭐ |

---

## 💡 구체적 사례

### 케이스 #1: 고점수 미매칭 (점수 0.900)

```
Invoice:
  Origin: SAMSUNG MOSB YARD
  Destination: DSV MUSSAFAH YARD
  Vehicle: LOWBED

최고 DN 후보: HVDC-DSV-SKM-MOSB-212
최고 점수: 0.900 (임계값 0.40 대폭 초과)

미매칭 이유:
  → HVDC-DSV-SKM-MOSB-212가 이미 다른 인보이스(FLATBED)에 할당됨
  → Vehicle이 다름: LOWBED vs FLATBED
  → 1:1 매칭 제약으로 할당 불가
```

### 케이스 #2-5: PRESTIGE → MIRFA/SHU (점수 0.775)

```
4개 인보이스 모두:
  Origin: PRESTIGE MUSSAFAH
  Destination: MIRFA PMO SAMSUNG / SHUWEIHAT
  Vehicle: FLATBED

최고 DN 후보: HVDC-DSV-PRE-MIR-SHU-230
최고 점수: 0.775

미매칭 이유:
  → HVDC-DSV-PRE-MIR-SHU-230가 2개만 있음 (Prestige-Mirfa, Prestige-Shuweihat)
  → 4개 인보이스가 경쟁
  → 2개만 할당, 나머지 2개 미매칭
```

### 케이스 #6-9: DSV MUSSAFAH → 여러 경로 (점수 0.700)

```
4개 인보이스:
  Origin: DSV MUSSAFAH YARD
  Destination: SHUWEIHAT / SAMSUNG MOSB
  Vehicle: FLATBED

최고 DN 후보: HVDC-ADOPT-SCT-0126
최고 점수: 0.700

미매칭 이유:
  → HVDC-ADOPT-SCT-0126가 4개 버전 있음 (DSV-MIRFA, DSV-SHU, MOSB-DSV, DSV-MOSB)
  → 4개 모두 capacity=1
  → 4개만 할당, 나머지 미매칭
```

---

## 🎯 핵심 인사이트

### 인기 DN 목록

| DN Shipment Ref | 경쟁 인보이스 수 | 할당 가능 | 미매칭 발생 |
|-----------------|-----------------|----------|------------|
| HVDC-ADOPT-SCT-0126 | ~8개 | 4개 | 4개+ |
| HVDC-DSV-SKM-MOSB-212 | ~6개 | 2개 | 4개+ |
| HVDC-DSV-PRE-MIR-SHU-230 | ~6개 | 2개 | 4개+ |
| HVDC-DSV-MOSB-MIR-220 | ~4개 | 2개 | 2개+ |

**패턴**:
- 주요 경로(DSV↔SAMSUNG, PRESTIGE↔MIRFA/SHU)에 DN이 부족
- 인보이스는 다양한 Vehicle/경로이지만 DN은 제한적

---

## 💡 해결 방안

### 옵션 A: DN_MIN_SCORE 낮추기 (효과 제한적)

```bash
export DN_MIN_SCORE=0.30
python validate_sept_2025_with_pdf.py
```

**예상 효과**:
- +2개 매칭 (22 → 24)
- 여전히 DN 소진 문제 존재

### 옵션 B: DN capacity 선택적 증가 (권장) ⭐

```python
# parse_dn_pdfs에서 인기 DN의 capacity 증가
if "HVDC-ADOPT-SCT-0126" in pdf_info["folder"]:
    dn_data["capacity"] = 2  # 4개 버전 × 2 = 8개 인보이스 매칭 가능
```

**예상 효과**:
- +10~15개 매칭 (20 → 30~35)
- 품질 유지 (점수 0.60+ 항목들)

### 옵션 C: 현상 유지 (고품질 전략)

**현재 상태**:
- 매칭 20개: 평균 점수 0.613, PASS 60%, FAIL 0%
- 미매칭 24개: 수작업 검토

**장점**:
- 고품질 매칭만 자동화
- 복잡한 케이스는 인간 판단

---

## 📊 최종 통계

### DN capacity 소진 상세

```
미매칭 22건 중 대표 사례:

1. Origin이 완벽 일치하지만 Vehicle 다름
   - SAMSUNG MOSB → DSV MUSSAFAH (LOWBED) vs (FLATBED)
   - 점수 0.900이지만 FLATBED가 먼저 할당받음

2. 같은 DN의 여러 버전이 모두 소진
   - HVDC-ADOPT-SCT-0126: 4개 버전 모두 할당됨
   - 5~8번째 인보이스는 할당 불가

3. 인기 경로의 DN 부족
   - PRESTIGE → MIRFA/SHU: 6개 인보이스, 2개 DN
   - DSV ↔ SAMSUNG: 10개+ 인보이스, 6개 DN
```

---

## 🎯 결론

**미매칭 24개의 주요 원인**:

1. **DN capacity 소진 (22건, 91.7%)**:
   - 점수는 충분히 높음 (평균 0.612)
   - 1:1 그리디 매칭에서 경쟁 패배
   - 해결: DN capacity 증가 또는 추가 DN 확보

2. **DN 개수 부족 (불가피 11건)**:
   - 인보이스 44개 > DN 33개
   - 물리적 한계

3. **점수 미달 (2건, 8.3%)**:
   - 점수 < 0.40
   - 매칭 어려움

**권장**: DN capacity를 선택적으로 증가 (옵션 B) 또는 현상 유지 (옵션 C)

---

**보고서 작성**: 2025-10-13 21:52:00
**분석 완료**: ✅

