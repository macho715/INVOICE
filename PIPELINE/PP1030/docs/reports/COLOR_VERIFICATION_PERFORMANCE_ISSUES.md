# Excel 색상 검증 성능 문제점 분석 및 개선

**생성일**: 2025-11-03  
**문제**: 색상 검증 스크립트 실행 시간이 너무 오래 걸림

---

## 발견된 문제점

### 1. 셀 접근 오버헤드
**문제**:
- `ws.cell(row, col)` 호출이 매번 파일 I/O 발생
- 각 셀마다 색상 추출 함수 호출로 인한 오버헤드

**영향**: 
- 2000개 셀 스캔 시 매우 느림
- 하단 행(tail_rows) 스캔 시 더욱 느림

### 2. 색상 추출 로직 비효율
**문제**:
- `get_cell_argb()` 함수가 매번 `getattr()` 다중 호출
- theme 객체 처리 시 복잡한 로직 수행
- fill이 없는 셀도 전체 로직 실행

**개선 적용**:
```python
# 빠른 체크 먼저
if not hasattr(cell, 'fill') or not cell.fill:
    return None, None

# RGB 타입 우선 확인 (가장 일반적)
if hasattr(sc, 'rgb') and sc.rgb:
    return _argb_upper(sc.rgb), indexed_val
```

### 3. 하단 행 스캔 문제
**문제**:
- `tail_rows=500` 설정 시 실제로는 매우 많은 행 스캔
- 파일 크기가 클수록(8,945행) 하단 접근이 느림

**개선 적용**:
```python
# 큰 파일은 every 2nd row만 스캔
if total_rows > 5000:
    tail_start = max(data_start, data_end - tail_rows_limit * 2 + 1)
    row_indices.extend(range(tail_start, data_end + 1, 2))
```

### 4. 배치 처리 부재
**문제**:
- 한 번에 전체 범위 스캔 시도로 인한 타임아웃
- 사용자가 여러 번 나눠서 실행해야 함

**해결책**: `verify_excel_colors_fast_batch.py` 생성
- 2000개씩 여러 배치로 나눠서 실행
- 각 배치별로 결과 집계

---

## 적용된 최적화

### 1. 색상 추출 최적화
✅ fill 없는 셀 즉시 스킵  
✅ RGB 타입 우선 확인  
✅ 불필요한 getattr 호출 최소화

### 2. 하단 스캔 최적화
✅ 큰 파일(>5000행)은 2칸씩 스킵  
✅ tail_rows 최대 200행으로 제한

### 3. 조기 종료 로직
✅ 충분한 샘플 발견 시 즉시 종료  
✅ max_cells_limit 도달 시 종료

### 4. 배치 처리 스크립트
✅ 여러 배치로 나눠서 실행  
✅ 각 배치별 결과 집계  
✅ 30초 타임아웃 설정

---

## 성능 개선 결과

### 이전 (최적화 전)
- tail_rows=500: 타임아웃 또는 매우 느림
- 하단 스캔: 전체 행 로드로 인한 지연
- 색상 추출: 매 셀마다 전체 로직 실행

### 현재 (최적화 후)
- 상단 스캔 (200행): 수초 내 완료 ✅
- 하단 스캔 (200행, 스킵): 수초 내 완료 ✅
- 색상 추출: 빠른 스킵으로 속도 향상 ✅

---

## 권장 사용법

### 1. 빠른 검증 (기본)
```bash
python verify_excel_colors_optimized.py --rows 50 --cols 10 --max-cells 2000
```

### 2. 배치 처리 (전체 검증)
```bash
python verify_excel_colors_fast_batch.py
```
- 상단, 중간(랜덤), 하단을 각각 2000개씩 스캔
- 결과를 `excel_color_verification_batch.json`에 저장

### 3. 하단 확인
```bash
python verify_excel_colors_optimized.py --rows 0 --tail-rows 200 --cols 10 --max-cells 2000
```

---

## 남은 이슈

### 1. YELLOW 색상 미발견
- 샘플 범위 내에서 YELLOW 색상이 발견되지 않음
- 실제로는 8,000행 이후에 집중되어 있을 가능성
- 해결: 하단 스캔 배치 실행 필요

### 2. 전체 색상 확인
- 전체 파일 스캔은 여전히 시간 소요
- 해결: ChangeTracker 로그 활용 (`--change-log`) 권장

---

## 결론

✅ **성능 문제 해결**: 빠른 스킵 및 조기 종료 로직 적용  
✅ **배치 처리 추가**: 2000개씩 나눠서 실행 가능  
✅ **하단 스캔 최적화**: 큰 파일에서 스킵 로직 적용  

⚠️ **제한사항**: YELLOW 색상은 하단 배치에서 확인 필요

