# SCT 화물 업데이트 누락 문제 조사 보고서

**작성일**: 2025-10-31  
**버전**: HVDC Pipeline v4.0.44  
**문제**: Stage 1에서 SCT 화물이 업데이트되지 않음

---

## Executive Summary

### 문제 발견

- **Master 파일**: SCT Ref.No 컬럼이 **없음**
- **Warehouse 파일**: SCT Ref.No 컬럼이 **99.8% 존재** (7,278건 / 7,291건)
- **Synced 파일**: SCT Ref.No 컬럼이 **대부분 존재** (9,221건 / 9,234건)

### 근본 원인

1. **Case No 형식 불일치**: Master의 Vendor="SCT" 화물의 Case No 형식이 Warehouse와 완전히 다름
   - Master SCT Case No: "DCS NETWORK-04", "38-EMERSON", "SCT-0115/ 7 OF 18" 등
   - Warehouse Case No: "191221", "191222" 등 (숫자 형식)
   - **매칭 결과: 0건** (90건 모두 매칭 실패)

2. **매칭 키 한계**: Stage 1은 Case No만 사용하여 매칭
   - SCT Ref.No를 보조 키로 사용하지 않음
   - 결과적으로 Vendor="SCT"인 90건 화물이 완전히 업데이트 누락

3. **데이터 손실**: 
   - Master SCT에 날짜 데이터 있음 (DSV Al Markaz: 39건, DSV Indoor: 39건, DSV Outdoor: 90건)
   - 하지만 Warehouse와 매칭이 안 되어 업데이트가 안 됨
   - Synced 파일에도 반영되지 않음

---

## 조사 결과

### 1. 파일별 컬럼 구조

#### Master 파일: `Case List_Hitachi.xlsx`
```
컬럼 구성:
1. no.
2. Shipment Invoice No.
3. Vendor
4. Description
5. Case No.
6. DSV Al Markaz
7. DSV Indoor
8. DSV Outdoor
...
❌ SCT Ref.No 컬럼 없음
```

#### Warehouse 파일: `HVDC WAREHOUSE_HITACHI(HE).xlsx`
```
컬럼 구성:
1. no.
2. Shipment Invoice No.
3. SCT Ref.No ← ✅ 존재
4. Site
5. EQ No
6. Case No.
...
✅ SCT Ref.No 컬럼 존재 (99.8% 데이터 있음)
```

### 2. 데이터 통계

| 파일 | 총 레코드 | SCT Ref.No 있음 | 비율 |
|------|----------|----------------|------|
| Master | ~1,453건 | 0건 | 0% |
| Warehouse | 7,291건 | 7,278건 | **99.8%** |
| Synced | 9,234건 | 9,221건 | **99.9%** |

### 3. 영향 분석

#### 문제 1: Master에 SCT Ref.No가 없음
- **영향**: Master 파일의 데이터로 SCT Ref.No 값을 업데이트할 수 없음
- **결과**: Warehouse의 기존 SCT Ref.No 값이 그대로 유지됨

#### 문제 2: Case No 없이 SCT Ref.No만 있는 경우
- **현재 로직**: Stage 1은 Case No만 사용하여 Master-Warehouse 매칭
- **잠재적 문제**: Case No가 없고 SCT Ref.No만 있는 화물은 매칭 실패 가능

---

## 해결 방안

### 구현: Stage 1 Fallback 매칭 로직 추가 ✅

**파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`

**수정 내용**:
- Case No 매칭 실패 시, Vendor="SCT"인 경우 보조 매칭 시도
- Description 키워드 매칭
- Case No 패턴과 SCT Ref.No 매칭
- Description substring 매칭

**위치**: Line 1281-1325

```python
# ✅ FALLBACK: Try to match using SCT Ref.No or Description for Vendor="SCT" cargo
if "Vendor" in master.columns and str(mrow.get("Vendor", "")).upper() == "SCT":
    # Multiple matching strategies...
```

### 방안 1 (대안): Master 파일에 SCT Ref.No 컬럼 추가

**장점**:
- 가장 직접적인 해결책
- Master 데이터로 SCT Ref.No 업데이트 가능

**방법**:
1. 원본 Master 파일 구조 확인
2. SCT Ref.No 컬럼 추가 여부 결정
3. 필요한 경우 Master 파일 수정 또는 새 버전 사용

### 방안 2: Stage 1 매칭 로직 개선

**현재**: Case No만 사용
```python
wh_index = self._build_case_index(wh, wh_case_col)
```

**개선**: SCT Ref.No를 보조 키로 사용
```python
# Case No가 없으면 SCT Ref.No로 매칭 시도
if key not in wh_index and sct_ref_col:
    sct_ref_key = str(mrow[sct_ref_col]).strip().upper() if pd.notna(mrow[sct_ref_col]) else ""
    if sct_ref_key:
        # SCT Ref.No로 매칭 시도
        pass
```

### 방안 3: Master-only 컬럼 처리 개선

**현재**: Master-only 컬럼이 Warehouse에 추가되지만, 값 업데이트는 안 됨

**개선**: Master에 없는 컬럼도 Warehouse에서 유지하되, 로깅 강화

---

## 다음 단계

1. **원본 Master 파일 확인**: SCT Ref.No가 실제로 없어야 하는 컬럼인지, 누락된 것인지 확인
2. **매칭 실패 케이스 조사**: Case No 없이 SCT Ref.No만 있는 화물 존재 여부 확인
3. **Master 파일 수정 또는 로직 개선**: 상황에 맞는 해결책 선택

---

## 참고 사항

- SCT = Samsung C&T의 약자로 추정
- SCT Ref.No는 내부 참조 번호일 가능성
- Warehouse 파일에는 대부분의 레코드에 SCT Ref.No가 존재하므로 중요한 식별자로 보임

---

## 실행 결과 및 검증

### 전체 파이프라인 실행 결과 (2025-10-31)

**Stage 1 실행**:
- ✅ SCT Fallback 매칭 로직 작동 확인
- 로그에서 다수의 "[SCT FALLBACK] Matched..." 메시지 확인
- 445개 셀 업데이트 (날짜: 370건, 필드: 75건)
- 2120개 신규 레코드 추가

**문제점**:
- ⚠️ 검증 스크립트 결과: Synced 파일에서 Vendor='SCT' 레코드가 **0건**
- Fallback 매칭은 발생했지만, 최종 파일에 반영되지 않음

**원인 추정**:
1. Fallback 매칭된 row가 업데이트는 되었지만 Vendor 컬럼이 업데이트되지 않음
2. 여러 SCT 케이스가 동일 Warehouse row로 매칭되어 덮어쓰기 발생
3. Description 키워드 매칭이 너무 광범위하여 잘못된 매칭 발생

### 개선 필요 사항

1. **매칭 정확도 향상**: Description 키워드 매칭이 너무 느슨함
2. **Vendor 컬럼 업데이트 확인**: Fallback 매칭 시 Source_Vendor도 업데이트 필요
3. **중복 매칭 방지**: 여러 Master 케이스가 같은 Warehouse row로 매칭되지 않도록 제한 필요

---

**작성자**: HVDC Pipeline AI Assistant  
**상태**: ✅ Fallback 로직 구현 완료, ⚠️ 검증 필요 (매칭 정확도 개선 필요)

