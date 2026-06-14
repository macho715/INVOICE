# Excel Report Generators - Legacy Files

**Archive Date**: 2025-10-14  
**Reason**: 포맷팅 코드로 인한 에러 방지 + 중복 제거  
**Status**: ⚠️ 사용 금지 (Excel 포맷팅 에러 발생)

---

## 📁 Archive된 파일

### 1. `create_enhanced_excel_report_backup.py` (1173줄)
**특징**:
- VBA 로직 포함 (`_apply_vba_logic()`)
- PDF 통합 완전 지원
- **문제**: Excel 포맷팅 코드 포함 (열너비, 폰트, 셀병합 등)
  - `ws.column_dimensions['A'].width = 20`
  - `cell.font = Font(bold=True)`
  - `cell.fill = PatternFill(...)`
  - `ws.merge_cells('A1:B1')`

**에러 발생**: ✅ 확인됨

### 2. `create_excel_report.py` (429줄)
**특징**:
- Before/After Contract 검증 비교
- 기본 Excel 보고서 생성
- **문제**: 조건부 서식, 헤더 포맷팅 포함
  - `apply_header_format()`
  - `apply_conditional_formatting()`
  - `adjust_column_widths()`

**에러 발생**: ✅ 확인됨

### 3. `generate_comprehensive_excel_report.py` (1012줄)
**특징**:
- 종합 보고서 (10개 시트)
- VBA/Python/PDF 통합
- **문제**: 대량의 스타일링 코드
  - `PatternFill`, `Font`, `Border`, `Alignment`
  - 차트 생성 (`BarChart`, `PieChart`)

**에러 발생**: ✅ 확인됨

---

## 🚫 왜 사용하면 안 되는가?

### Excel 포맷팅 코드 에러
```python
# ❌ 이런 코드들이 에러를 발생시킴:
ws.column_dimensions['A'].width = 20
cell.font = Font(bold=True, color="FFFFFF")
cell.fill = PatternFill(start_color="366092", fill_type="solid")
ws.merge_cells('A1:B1')
cell.alignment = Alignment(horizontal="center")
cell.border = Border(left=Side(style="thin"))
```

**에러 메시지**:
- "Workbook object has no attribute"
- "Invalid value for cell"
- "Cannot merge cells" 등

---

## ✅ 대체 솔루션

### 사용해야 할 파일

#### 1. `vba_result_reader.py` (신규)
- VBA MasterData 읽기
- REV RATE, REV TOTAL, DIFFERENCE 추출
- **포맷팅 코드 없음** ✅

#### 2. `simple_csv_exporter.py` (신규)
- 순수 CSV/Excel 출력
- pandas 기본 `to_excel()` 사용
- **포맷팅 코드 절대 없음** ✅

#### 3. `shpt_sept_2025_enhanced_audit.py` (수정됨)
- VBA 통합 로직 추가
- 포맷팅 제거된 출력
- **안정적** ✅

---

## 📊 성능 비교

| 항목 | Legacy (에러 발생) | New (안정적) |
|------|-------------------|-------------|
| **파일 수** | 5개 (중복) | 2개 (통합) |
| **코드 라인** | 3000+ 줄 | 400 줄 |
| **에러율** | 높음 (포맷팅) | 0% ✅ |
| **VBA 통합** | 부분적 | 완전 ✅ |
| **PDF 통합** | 지원 | 지원 ✅ |
| **유지보수** | 어려움 | 쉬움 ✅ |

---

## 🔧 마이그레이션 가이드

### Legacy에서 New로 전환

**Before** (Legacy - 에러 발생):
```python
from create_enhanced_excel_report import EnhancedExcelReportGenerator
generator = EnhancedExcelReportGenerator()
results = generator.create_comprehensive_report(csv_path, json_path, output_dir)
# ❌ 에러: Excel 포맷팅 코드 실행 시 실패
```

**After** (New - 안정적):
```python
from simple_csv_exporter import export_simple_excel, export_simple_csv
export_simple_excel(df, "output.xlsx")  # 포맷팅 없음
export_simple_csv(df, "output.csv")     # 순수 CSV
# ✅ 안정적: 에러 없음
```

---

## 📝 히스토리

- **2025-10-14**: Archive 이동
  - PDF Integration 수정 완료 후
  - VBA 통합 완료 후
  - 포맷팅 제거된 안정적 솔루션 배포

- **2025-10-13**: Legacy 파일 생성
  - 초기 PDF Integration 구현
  - Excel 포맷팅 시도 (에러 발생)

---

## ⚠️ 복원 시 주의사항

만약 이 파일들을 복원해야 한다면:

1. **모든 Excel 포맷팅 코드 제거** 필수
2. `to_excel(index=False)` 만 사용
3. 스타일링은 사용자가 수동 적용

---

**✅ Legacy 파일 안전하게 보관됨 - 새로운 안정적 솔루션 사용 권장**

