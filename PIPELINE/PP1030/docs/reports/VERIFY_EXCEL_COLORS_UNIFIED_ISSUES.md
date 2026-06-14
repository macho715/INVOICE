# verify_excel_colors_unified.py 문제점 보고서

**생성일**: 2025-11-03  
**스크립트**: `verify_excel_colors_unified.py`  
**문제 유형**: 실행 중단, 성능 문제, 에러 처리 부족

---

## 🔴 발견된 문제점 요약

### 1. **성능 문제: 무한 루프 위험**
**위치**: `scan_one_sheet_basic` 함수 (368-451줄)

**문제**:
- `row_indices` 생성 로직에서 매우 큰 범위의 행을 생성할 수 있음
- `full_scan` 모드에서 `total_rows > 10000`일 때도 `skip_step = 2`로 모든 행을 순회
- 예: 10,000행 × 12컬럼 = 120,000개 셀 스캔 가능 (max_cells_limit=2000 초과)

**영향**:
- 스캔 시간이 매우 오래 걸림 (수 분 ~ 수십 분)
- 사용자가 스크립트가 멈춘 것으로 착각

**코드 위치**:
```python
# 370-373줄
if full_scan:
    skip_step = 2 if total_rows > 10000 else 1
    row_indices = list(range(data_start, data_end + 1, skip_step))
```

**해결책**:
- `max_cells_limit` 체크를 `row_indices` 생성 단계에서 수행
- 생성 전에 예상 스캔 셀 수 계산: `len(row_indices) * len(target_cols)`
- 초과 시 샘플링 자동 적용

---

### 2. **에러 처리: 조용한 실패**
**위치**: `scan_one_sheet_basic` 함수 (465-470줄)

**문제**:
- 예외 발생 시 빈 `SheetScanResult`를 반환만 하고 에러 메시지를 출력하지 않음
- 병렬 처리 시 에러가 묻힘

**코드 위치**:
```python
# 465-470줄
except Exception:
    return SheetScanResult(
        sheet=sheet_name, header_row=1, total_rows=0, total_columns=0,
        case_col_idx=None, orange_cells=0, yellow_cells=0,
        yellow_rows=[], sample_cases=[]
    )
```

**영향**:
- 실제 오류 원인을 알 수 없음
- 디버깅 어려움

**해결책**:
- 예외 메시지를 로그/출력으로 남기기
- 최소한 스텁 메시지 출력 (`print(f"[WARN] {sheet_name}: {e}")`)

---

### 3. **진행 상황 표시 부재**
**위치**: `main` 함수 (712-775줄)

**문제**:
- 스캔 중 진행 상황을 출력하지 않음
- 사용자가 작업 진행 여부를 알 수 없음

**영향**:
- 스크립트가 멈춘 것으로 오인
- 사용자 취소 및 재실행 빈발

**해결책**:
- 시트별 스캔 시작/완료 메시지 출력
- 예: `print(f"[진행중] {sheet_name} 스캔 시작...")`, `print(f"[완료] {sheet_name}: ORANGE={o}, YELLOW={y}")`

---

### 4. **인자 검증 부족**
**위치**: `main` 함수 (665줄 이후)

**문제**:
- `--max-cells` 값이 0이거나 음수일 때 처리 없음
- `--sheets` 값이 실제 시트 수보다 클 때 처리 없음

**영향**:
- 예상치 못한 동작 가능

**해결책**:
- 인자 유효성 검사 추가
- 기본값으로 자동 보정

---

### 5. **메모리 사용: 대용량 파일 처리**
**위치**: 전체 스크립트

**문제**:
- `read_only=True` 모드 사용 중이지만, 셀 접근 시 메모리 적재
- 매우 큰 파일(수만 행)에서 메모리 부족 가능

**영향**:
- 대용량 파일에서 실행 중단/크래시

**해결책**:
- 배치 처리로 셀 접근 제한
- 진행 중 메모리 사용량 모니터링

---

### 6. **병렬 처리: 프로세스 간 데이터 전달**
**위치**: `main` 함수 (738-739줄)

**문제**:
- `multiprocessing.Pool` 사용 시 각 워커가 전체 워크북을 다시 열어야 함
- 파일이 크면 워커 초기화 시간이 길어짐

**영향**:
- 병렬 처리 이점이 줄어듦
- 시작 지연

**해결책**:
- 워커 수를 `cpu_count() // 4`에서 더 줄이거나 (`cpu_count() // 8`)
- 단일 프로세스 모드(`--no-parallel`)를 기본값으로 권장

---

### 7. **로깅/디버깅 정보 부족**
**위치**: 전체 스크립트

**문제**:
- 디버그 모드 없음
- 상세 에러 정보 출력 없음

**영향**:
- 문제 진단 어려움

**해결책**:
- `--verbose` / `--debug` 옵션 추가
- 에러 발생 시 스택 트레이스 출력 옵션

---

## 📊 우선순위별 수정 권장사항

### 🔴 긴급 (즉시 수정)
1. **진행 상황 표시 추가** (사용자 경험 개선)
2. **에러 메시지 출력** (디버깅 개선)

### 🟡 중요 (가까운 시일 내)
3. **성능 최적화: max_cells_limit 사전 체크** (실행 시간 단축)
4. **인자 유효성 검사** (안정성 개선)

### 🟢 선택 (향후 개선)
5. **메모리 최적화**
6. **로깅/디버깅 모드 추가**

---

## 🔧 즉시 적용 가능한 임시 해결책

1. **기본 모드를 `ultra_fast`로 변경**
   ```python
   ap.add_argument("--mode", type=str, default="ultra_fast", ...)
   ```

2. **병렬 처리 비활성화 기본값**
   ```python
   ap.add_argument("--parallel", action="store_true")  # 기본값 False
   ```

3. **타임아웃 추가**
   ```python
   import signal
   signal.alarm(300)  # 5분 타임아웃
   ```

---

## 📝 수정 예시 코드

### 진행 상황 표시 추가
```python
# main 함수 내부
if args.mode == "basic" or args.mode == "full":
    print(f"대상 시트: {target_sheets}\n")
    
    # 진행 상황 표시
    for i, s in enumerate(target_sheets, 1):
        print(f"[{i}/{len(target_sheets)}] {s} 스캔 중...")
        # ... 스캔 로직 ...
        print(f"[완료] {s}: ORANGE={r.orange_cells}, YELLOW={r.yellow_cells}")
```

### 에러 메시지 출력
```python
# scan_one_sheet_basic 함수 내부
except Exception as e:
    print(f"[WARN] {sheet_name} 스캔 실패: {e}", file=sys.stderr)
    return SheetScanResult(...)
```

### max_cells_limit 사전 체크
```python
# scan_one_sheet_basic 함수 시작 부분
expected_cells = len(row_indices) * len(target_cols) if row_indices and target_cols else 0
if expected_cells > max_cells_limit * 1.5:  # 50% 여유
    # 샘플링 자동 적용
    skip_factor = max(1, int(expected_cells / max_cells_limit))
    row_indices = row_indices[::skip_factor]
    print(f"[INFO] {sheet_name}: 샘플링 적용 (skip={skip_factor})")
```

---

## ✅ 검증 방법

수정 후 다음 명령어로 테스트:

```bash
# 1. 기본 실행 (빠른 테스트)
python verify_excel_colors_unified.py --mode=ultra_fast --sheets=1

# 2. 기본 모드 (5초 타임아웃)
timeout 5 python verify_excel_colors_unified.py --mode=basic --sheets=1 || echo "타임아웃"

# 3. 에러 확인
python verify_excel_colors_unified.py --mode=basic --sheets=1 --max-cells=10 2>&1 | grep -i "error\|warn"
```

---

**보고서 작성**: 2025-11-03  
**분석 기준**: 코드 리뷰 + 실제 실행 테스트

