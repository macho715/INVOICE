# Excel 라이브러리 통합 가이드

**작성일**: 2025-12-21  
**버전**: v1.0  
**적용 범위**: HVDC 파이프라인 Excel 처리 최적화

---

## 개요

최신 Python Excel 라이브러리를 통합하여 파이프라인 성능과 기능을 향상시킵니다.

## 통합된 라이브러리

### 1. xlwings (VBA-Python 통합)

**목적**: Excel VBA와 Python 간 양방향 통신

**파일**: `vba/python_bridge.py`

**주요 기능**:
- VBA에서 Python 함수 직접 호출
- 실시간 파이프라인 상태 조회
- 파이프라인 설정 검증

**사용 예시**:
```python
from vba.python_bridge import run_pipeline_stage, get_pipeline_status

# VBA에서 호출 가능한 함수
result = run_pipeline_stage(1)  # Stage 1 실행
status = get_pipeline_status()  # 상태 조회
```

**VBA에서 사용**:
```vb
' xlwings 추가 기능 설치 필요
Dim result As Variant
result = RunPython("run_pipeline_stage", 1)
MsgBox result("message")
```

**설치**:
```bash
pip install xlwings>=0.31.0
xlwings addin install  # Excel 추가 기능 설치
```

### 2. Polars (고성능 데이터 처리)

**목적**: 대용량 Excel 파일 처리 성능 향상 (pandas 대비 5-30배 빠름)

**파일**: `scripts/core/excel_io_polars.py`

**주요 기능**:
- 고성능 Excel 읽기/쓰기
- 대용량 파일 처리 최적화
- 메모리 효율적 처리

**사용 예시**:
```python
from scripts.core.excel_io_polars import (
    read_excel_polars,
    write_excel_polars,
    read_excel_polars_multi_sheet
)

# 단일 시트 읽기
df = read_excel_polars("input.xlsx", sheet_name="Sheet1")

# 여러 시트 읽기
sheets = read_excel_polars_multi_sheet("input.xlsx")

# Excel 쓰기
write_excel_polars(df, "output.xlsx", sheet_name="Sheet1")
```

**성능 비교**:
- 읽기: pandas 대비 5-10배 빠름
- 쓰기: pandas 대비 3-5배 빠름
- 메모리: 30-50% 절약

**적용 위치**:
- Stage 1: 대용량 Master/Warehouse 파일 읽기
- Stage 2: 파생 컬럼 계산 (벡터화 연산)
- Stage 3: 리포트 생성 (대용량 데이터 처리)

### 3. pywin32 (Windows COM 자동화)

**목적**: Excel COM 객체 직접 제어 (정밀한 포맷팅)

**파일**: `scripts/core/excel_com_automation.py`

**주요 기능**:
- Case 번호 기반 색상 포맷팅
- 특정 셀 색상 적용
- 차트 생성
- Excel 기능 직접 활용

**사용 예시**:
```python
from scripts.core.excel_com_automation import (
    ExcelCOMAutomation,
    ExcelColors,
    apply_color_to_cases
)

# Context manager 사용
with ExcelCOMAutomation(visible=False) as excel:
    excel.apply_color_formatting(
        "file.xlsx",
        "Sheet1",
        case_numbers=["207721", "207722"],
        color=ExcelColors.ORANGE,
        case_column="Case No."
    )

# 편의 함수 사용
apply_color_to_cases(
    "file.xlsx",
    "Sheet1",
    case_numbers=["207721", "207722"],
    color=ExcelColors.YELLOW
)
```

**색상 상수**:
```python
ExcelColors.ORANGE = 0xFFA500      # 주황색 (날짜 변경)
ExcelColors.YELLOW = 0xFFFF00      # 노란색 (신규 레코드)
ExcelColors.RED = 0xFF0000         # 빨간색 (CRITICAL)
ExcelColors.LIGHT_RED = 0xFF6B6B   # 연한 빨강 (HIGH)
ExcelColors.LIGHT_YELLOW = 0xFFFFE0  # 연한 노랑 (MEDIUM)
ExcelColors.LIGHT_GREEN = 0x90EE90   # 연한 초록 (LOW)
```

**적용 위치**:
- Stage 1: 색상 포맷팅 정밀도 향상
- Stage 4: 이상치 색상 시각화

---

## 통합 전략

### 단계별 적용

#### Phase 1: xlwings 통합 (완료)
- ✅ `vba/python_bridge.py` 생성
- ✅ VBA-Python 브리지 함수 구현
- ✅ 파이프라인 실행 함수 제공

#### Phase 2: Polars 확장 (완료)
- ✅ `scripts/core/excel_io_polars.py` 생성
- ✅ 고성능 Excel I/O 함수 구현
- ✅ 멀티시트 지원

#### Phase 3: pywin32 통합 (완료)
- ✅ `scripts/core/excel_com_automation.py` 생성
- ✅ COM 자동화 클래스 구현
- ✅ 색상 포맷팅 함수 제공

### 기존 코드와의 통합

#### Polars 어댑터 활용
기존 `scripts/core/polars_adapter.py`와 연동:
```python
from scripts.core.polars_adapter import to_polars, to_pandas
from scripts.core.excel_io_polars import read_excel_polars

# Pandas → Polars → Excel
pd_df = pd.read_excel("input.xlsx")
pl_df = to_polars(pd_df)
# Polars로 처리 후 Excel 쓰기
```

#### XlsxWriter와의 조합
기존 `scripts/core/excel_writer_optimized.py`와 함께 사용:
- 읽기: Polars (빠름)
- 쓰기: XlsxWriter (고성능)
- 포맷팅: pywin32 (정밀)

---

## 성능 개선 예상

### Stage 1 (데이터 동기화)
- **현재**: ~299초 (8,930행)
- **예상**: ~150-200초 (Polars 적용 시 30-50% 개선)

### Stage 2 (파생 컬럼)
- **현재**: ~29초 (8,930행)
- **예상**: ~15-20초 (Polars 벡터화 연산)

### Stage 3 (리포트 생성)
- **현재**: ~106초 (12개 시트)
- **예상**: ~60-80초 (Polars + XlsxWriter 조합)

### Stage 4 (이상치 탐지)
- **현재**: ~58초
- **예상**: ~50-55초 (변화 미미, ML 연산이 주)

---

## 사용 가이드

### 1. xlwings 설정

**Excel 추가 기능 설치**:
```bash
pip install xlwings
xlwings addin install
```

**Excel에서 확인**:
1. Excel → 파일 → 옵션 → 추가 기능
2. "xlwings" 확인

**VBA에서 사용**:
```vb
' Python 함수 호출
Dim result As Variant
result = RunPython("run_pipeline_stage", 1)
```

### 2. Polars 사용

**기존 코드 마이그레이션**:
```python
# 기존 (Pandas)
df = pd.read_excel("file.xlsx")

# 새로운 (Polars)
from scripts.core.excel_io_polars import read_excel_polars
df = read_excel_polars("file.xlsx")
```

**점진적 전환**:
- 기존 Pandas 코드는 그대로 유지
- 새로운 코드는 Polars 우선 사용
- 필요시 `polars_adapter`로 변환

### 3. pywin32 사용

**기본 사용**:
```python
from scripts.core.excel_com_automation import ExcelCOMAutomation, ExcelColors

with ExcelCOMAutomation(visible=False) as excel:
    excel.apply_color_formatting(
        "output.xlsx",
        "Sheet1",
        case_numbers=["207721", "207722"],
        color=ExcelColors.ORANGE
    )
```

**주의사항**:
- Excel 파일이 열려있으면 오류 발생 가능
- 대량 처리 시 배치 업데이트로 최적화됨
- COM 객체는 반드시 종료 필요 (context manager 사용 권장)

---

## 의존성 관리

### 설치

```bash
pip install -r requirements.txt
```

또는

```bash
pip install xlwings>=0.31.0 pywin32>=306
```

### 버전 확인

```python
import xlwings
import win32com.client
import polars as pl

print(f"xlwings: {xlwings.__version__}")
print(f"polars: {pl.__version__}")
```

---

## 문제 해결

### xlwings 관련

**문제**: "RunPython 함수를 찾을 수 없습니다"
- **해결**: Excel 추가 기능 설치 확인
- **명령**: `xlwings addin install`

**문제**: Python 함수 호출 실패
- **해결**: Python 경로 확인, 모듈 임포트 경로 확인

### Polars 관련

**문제**: "Polars Excel reading failed"
- **해결**: `polars[excel]` 설치 확인
- **명령**: `pip install "polars[excel]"`

**문제**: 성능 개선이 미미함
- **해결**: 파일 크기 확인, calamine 엔진 사용 확인

### pywin32 관련

**문제**: "Excel.Application을 찾을 수 없습니다"
- **해결**: Excel이 설치되어 있는지 확인
- **해결**: Windows 환경인지 확인

**문제**: 파일이 열려있다는 오류
- **해결**: Excel에서 파일 닫기
- **해결**: 다른 프로세스에서 파일 사용 중인지 확인

---

## 향후 확장 계획

### 단기 (1-2주)
- [ ] xlwings UDF 등록 자동화
- [ ] Polars 성능 벤치마크
- [ ] pywin32 색상 포맷팅 통합 테스트

### 중기 (1개월)
- [ ] calamine 엔진 통합 (Rust 기반 초고속 읽기)
- [ ] Stage별 성능 최적화 적용
- [ ] 자동 폴백 메커니즘 구현

### 장기 (3개월)
- [ ] 완전한 Polars 마이그레이션
- [ ] Excel 템플릿 자동 생성
- [ ] 실시간 대시보드 통합

---

## 참고 문서

- [xlwings 공식 문서](https://docs.xlwings.org/)
- [Polars 공식 문서](https://pola-rs.github.io/polars/)
- [pywin32 문서](https://github.com/mhammond/pywin32)
- [VBA 런처 가이드](../technical/vba.md)

---

**최종 업데이트**: 2025-12-21  
**작성자**: HVDC 파이프라인 개발팀

