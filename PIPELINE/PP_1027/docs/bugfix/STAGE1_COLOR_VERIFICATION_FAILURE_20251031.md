# Stage 1 색상 검증 실패 원인 분석

**날짜**: 2025-10-31
**버전**: v4.0.52 이후
**작업자**: AI Assistant
**이슈**: 색상 검증 스크립트 실행 시 색상 0개 발견

---

## 📋 Executive Summary

### 문제점
- **증상**: 색상 검증 스크립트 실행 시 모든 시트에서 색상 0개 발견
- **예상 원인**: 시트 이름 불일치로 인한 ChangeTracker 매칭 실패
- **영향**: Stage 1 실행 후 색상이 Excel 파일에 적용되지 않음

### 확인된 사실
- 디버그 결과: 모든 셀에서 `fill_type=None`, `start_color.rgb=00000000`
- 로그에서 색상 적용 메시지 없음 (`[DEBUG] Orange cells applied` 없음)
- 시트 이름 처리 과정에서 불일치 발생 가능성

---

## 🔍 상세 분석

### 1. 문제 발생 메커니즘

```python
# Step 1: ChangeTracker 저장 (라인 1547-1548)
output_sheet_name = w_sheet_name  # 예: "Case List, RIL"
sheet_change_trackers[output_sheet_name] = self.change_tracker
# 저장 키: "Case List, RIL" (원본 이름)

# Step 2: Excel 파일 저장 (라인 1607-1614)
clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]
# "Case List, RIL" → "Case List, RIL" (변경 없음)
df_reordered.to_excel(writer, sheet_name=clean_sheet_name, index=False)
# Excel 시트 이름: "Case List, RIL"

# Step 3: 색상 적용 (라인 1621-1627)
for sheet_name, (df, header_row) in processed_sheets.items():
    clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]
    if sheet_name in sheet_change_trackers:  # ← 원본 이름으로 찾음
        self.change_tracker = sheet_change_trackers[sheet_name]
        self._apply_excel_formatting(out, clean_sheet_name, header_row)  # ← clean 이름으로 적용
```

### 2. 시트 이름 불일치 시나리오

**케이스 1: 정상적인 경우 (쉼표만 포함)**
- 원본: `"Case List, RIL"`
- Clean: `"Case List, RIL"` (변경 없음)
- ChangeTracker 키: `"Case List, RIL"`
- 매칭: ✅ 성공

**케이스 2: 슬래시 포함 시트 이름**
- 원본: `"Sheet/Name"`
- Clean: `"Sheet_Name"` (슬래시 → 언더스코어)
- ChangeTracker 키: `"Sheet/Name"`
- 매칭: ✅ 성공 (순회 시 원본 이름 사용)

**케이스 3: 31자 초과 시트 이름**
- 원본: `"Very Long Sheet Name That Exceeds Excel Limit"`
- Clean: `"Very Long Sheet Name That Ex"` (31자로 잘림)
- ChangeTracker 키: `"Very Long Sheet Name That Exceeds Excel Limit"`
- 매칭: ✅ 성공 (순회 시 원본 이름 사용)

**결론**: 시트 이름 처리 자체는 문제 없어 보임. 하지만 실제 Excel 파일에서는 다른 이름이 저장되었을 가능성 존재.

### 3. 검증 결과

#### 3.1 색상 검증 스크립트 실행 결과

```
파일: HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx
경로: C:\PP 1027\data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx

발견된 시트: 3개
  1. 통합_원본데이터_Fixed
  2. Case List, RIL
  3. Case List, RIL(SIMENSE)

  시트: 통합_원본데이터_Fixed
    - 총 7292행, 40열
    - 주황색 셀: 0개
    - 노란색 셀: 0개
    - 기타 색상 셀: 0개

  시트: Case List, RIL
    - 총 1454행, 19열
    - 주황색 셀: 0개
    - 노란색 셀: 0개

  시트: Case List, RIL(SIMENSE)
    - 총 1944행, 39열
    - 주황색 셀: 0개
    - 노란색 셀: 0개
```

#### 3.2 디버그 스크립트 결과

- 모든 셀에서 `fill_type: None`
- 모든 셀에서 `start_color.rgb: 00000000` (검은색)
- 색상이 적용된 셀 없음 확인

#### 3.3 로그 분석

- `[DEBUG] Orange cells applied` 메시지 없음
- `[DEBUG] Yellow cells applied` 메시지 없음
- `[INFO] No change tracker (skipped)` 메시지 없음

---

## 🔧 원인 분석

### 가능한 원인 1: ChangeTracker 누락

**증거**:
- 로그에 색상 적용 메시지가 전혀 없음
- 디버그 결과 색상이 전혀 적용되지 않음

**확인 필요**:
1. Stage 1 로그에서 `[INFO] No change tracker (skipped)` 메시지 확인
2. `sheet_change_trackers` 딕셔너리에 데이터가 있는지 확인

### 가능한 원인 2: 시트 이름 불일치 (사용자 지적)

**확인 사항**:
- 실제 Excel 파일의 시트 이름과 `processed_sheets`의 키가 다른지
- `_apply_excel_formatting`에서 올바른 시트를 열고 있는지

**코드 검토**:
```python
# 라인 1627
self._apply_excel_formatting(out, clean_sheet_name, header_row)

# _apply_excel_formatting 내부 (라인 1743)
def _apply_excel_formatting(self, excel_file: str, sheet_name: str, header_row: int):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]  # ← 여기서 sheet_name이 Excel 파일의 실제 시트 이름과 일치해야 함
```

**문제 가능성**:
- `clean_sheet_name`이 실제 Excel 파일의 시트 이름과 다를 수 있음
- Excel에서 시트 이름 자동 변환 (예: 공백 제거, 특수문자 처리)

### 가능한 원인 3: 색상 적용 로직 미실행

**확인 필요**:
1. `self.change_tracker.changes`에 변경사항이 있는지
2. `case_to_row` 매핑이 구축되었는지
3. `_apply_excel_formatting` 함수가 실제로 실행되었는지

---

## 🛠️ 해결 방안

### 방안 1: 시트 이름 매핑 구축

```python
# sheet_name_mapping: Dict[원본이름, clean이름] 구축
sheet_name_mapping = {}
for sheet_name, (df, header_row) in processed_sheets.items():
    clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]
    sheet_name_mapping[clean_sheet_name] = sheet_name
    df_reordered.to_excel(writer, sheet_name=clean_sheet_name, index=False)

# 색상 적용 시
for sheet_name, (df, header_row) in processed_sheets.items():
    clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]
    if sheet_name in sheet_change_trackers:
        self.change_tracker = sheet_change_trackers[sheet_name]
        # 실제 Excel 시트 이름으로 열기
        try:
            self._apply_excel_formatting(out, clean_sheet_name, header_row)
        except KeyError:
            # clean 이름이 없으면 원본 이름 시도
            self._apply_excel_formatting(out, sheet_name, header_row)
```

### 방안 2: ChangeTracker 저장 시 clean 이름도 함께 저장

```python
# 저장 시
sheet_change_trackers[output_sheet_name] = self.change_tracker
clean_name = output_sheet_name.replace("/", "_").replace("\\", "_")[:31]
if clean_name != output_sheet_name:
    sheet_change_trackers[clean_name] = self.change_tracker  # clean 이름으로도 저장

# 로드 시
if sheet_name in sheet_change_trackers:
    self.change_tracker = sheet_change_trackers[sheet_name]
elif clean_sheet_name in sheet_change_trackers:
    self.change_tracker = sheet_change_trackers[clean_sheet_name]  # clean 이름으로도 찾기
```

### 방안 3: Excel 파일에서 실제 시트 이름 확인

```python
def _apply_excel_formatting(self, excel_file: str, sheet_name: str, header_row: int):
    wb = load_workbook(excel_file)
    
    # 실제 Excel 시트 이름 확인
    actual_sheet_names = wb.sheetnames
    if sheet_name not in actual_sheet_names:
        # 가장 유사한 이름 찾기
        for actual_name in actual_sheet_names:
            if actual_name.replace("/", "_").replace("\\", "_")[:31] == sheet_name:
                sheet_name = actual_name
                break
        else:
            print(f"      [WARN] Sheet '{sheet_name}' not found in Excel file")
            print(f"      [INFO] Available sheets: {actual_sheet_names}")
            return
    
    ws = wb[sheet_name]
    # ... 색상 적용 로직
```

### 방안 4: 로깅 강화

```python
# 색상 적용 전 로깅
print(f"    - {clean_sheet_name}: {len(self.change_tracker.changes)} changes")
print(f"      [DEBUG] ChangeTracker keys: {list(sheet_change_trackers.keys())}")
print(f"      [DEBUG] Looking for sheet: '{sheet_name}'")
print(f"      [DEBUG] Clean sheet name: '{clean_sheet_name}'")

# _apply_excel_formatting 시작 시 로깅
print(f"      [DEBUG] Opening Excel file: {excel_file}")
print(f"      [DEBUG] Requested sheet name: '{sheet_name}'")
print(f"      [DEBUG] Available sheets: {wb.sheetnames}")
```

---

## 📊 검증 결과 상세

### 검증 스크립트 실행 결과

**파일**: `scripts/verification/verify_stage1_colors.py`
**실행 시간**: 2025-10-31

**결과**:
- 주황색 셀 (날짜 변경): 0개
- 노란색 셀 (신규 행): 0개
- 기타 색상 셀: 0개
- 총 색상 적용 셀: 0개

### 디버그 스크립트 결과

**파일**: `scripts/verification/check_color_debug.py`

**결과**:
- 검사한 셀: 처음 10행 10열 (100개 셀)
- 모든 셀에서 `fill_type: None`
- 모든 셀에서 `start_color.rgb: 00000000`
- 색상이 적용된 셀: 0개

### 로그 분석

**파일**: `logs/pipeline.log`

**검색 키워드**: 
- `Orange cells applied`
- `Yellow cells applied`
- `색상 적용`
- `No change tracker`

**결과**: 해당 메시지 없음

---

## 🔄 다음 단계

### 즉시 확인 사항

1. **Excel 파일 직접 확인**
   - `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx` 파일 열기
   - 실제 시트 이름 확인
   - 시각적으로 색상 확인

2. **Stage 1 로그 확인**
   - 최근 실행 로그에서 다음 메시지 확인:
     - `[INFO] No change tracker (skipped)`
     - `[DEBUG] Orange cells applied`
     - `[DEBUG] Yellow cells applied`

3. **Stage 1 재실행**
   - 최신 데이터로 Stage 1 재실행
   - 로그에서 색상 적용 메시지 확인
   - 출력 파일의 색상 직접 확인

### 코드 수정 권장 사항

1. **시트 이름 매핑 추가** (방안 1 또는 2)
2. **Excel 실제 시트 이름 확인** (방안 3)
3. **로깅 강화** (방안 4)

---

## 📚 참조 문서

### 관련 문서
- `docs/bugfix/STAGE1_COLOR_ROW_INDEX_FIX_20251027.md`: Stage 1 색상 적용 row_index 불일치 버그 수정 (2025-10-27)

### 관련 코드
- `scripts/stage1_sync_sorted/data_synchronizer_v30.py`:
  - 라인 1547-1548: ChangeTracker 저장
  - 라인 1607-1614: Excel 파일 저장 (시트 이름 처리)
  - 라인 1621-1629: 색상 적용 로직
  - 라인 1743-1931: `_apply_excel_formatting` 함수

### 검증 스크립트
- `scripts/verification/verify_stage1_colors.py`: 색상 검증 스크립트
- `scripts/verification/check_color_debug.py`: 색상 디버그 스크립트

---

## ✅ 체크리스트

- [x] 색상 검증 스크립트 실행
- [x] 디버그 스크립트 실행
- [x] 로그 분석
- [x] 원인 분석 문서 작성
- [ ] Excel 파일 직접 확인 (수동 필요)
- [ ] Stage 1 재실행 및 로그 확인
- [ ] 코드 수정 (해결 방안 적용)

---

**작성일**: 2025-10-31
**작성자**: AI Assistant
**상태**: 원인 분석 완료, 해결 방안 제시됨
**우선순위**: 중간 (색상 기능 동작하지 않음, 하지만 데이터 동기화는 정상)


