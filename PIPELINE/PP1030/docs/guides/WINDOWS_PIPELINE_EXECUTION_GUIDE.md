# HVDC 파이프라인 실행 가이드 (Windows PowerShell)

## 📋 개요

이 가이드는 Windows PowerShell 환경에서 HVDC 파이프라인(Stage 1→2→3)을 실행하는 방법을 설명합니다.  
**파일 자동탐지 기능**을 활용하여 파일명 변형(SIM/SIEMENS/simense, HITACHI/HE/(HE))을 자동으로 처리합니다.

---

## 0️⃣ 준비 작업 (최초 1회)

### 1. 프로젝트 루트로 이동

```powershell
cd C:\PP1030
```

### 2. 가상환경 설정 및 패키지 설치

```powershell
# 가상환경 생성 (아직 없다면)
py -3 -m venv .venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt
```

### 3. 원본 파일 배치

`data/raw/` 폴더에 다음 파일들을 준비합니다. 파일명은 유연하게 매칭됩니다.

```
data/
  raw/
    Case List(HE).xlsx           # HE vendor master file
    Case List(SIM_20251030).xlsm  # SIM vendor master file (선택)
    HVDC WAREHOUSE_HITACHI(HE).xlsx
    HVDC WAREHOUSE_SIMENSE(SIM).xlsm
    [선택] HVDC WAREHOUSE_SIEMENS.xlsx  # SIEMENS 토큰도 허용 (기본 ON)
```

**지원되는 토큰:**
- **SIM 그룹**: `sim`, `simense`, `siemens` (기본 포함)
- **HE 그룹**: `hitachi`, `he`

---

## 1️⃣ 자동탐지 옵션 설정 (선택)

### 기본값

- **SIEMENS 토큰 포함**: 기본적으로 `ON` (혼동 방지)

### SIEMENS 토큰 비활성화

SIEMENS와 SIMENSE를 구분하고 싶을 때:

```powershell
$env:HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS = "0"
```

### 확장자 제한 (선택)

특정 확장자만 허용하려면:

```powershell
$env:HVDC_FILE_FINDER_ALLOWED_SUFFIXES = ".xlsx,.xlsm"
```

---

## 2️⃣ 사전 점검 (10초)

자동탐지 결과를 먼저 확인합니다:

```powershell
python - << 'PY'
from pathlib import Path
from scripts.core.file_registry import FileRegistry

root = Path('.').resolve()
reg = FileRegistry(root)  # enable_siemens_alias 기본 ON

he_result = reg.get_raw_with_canonical("HE")
sim_result = reg.get_raw_with_canonical("SIM")

print("=" * 60)
print("자동탐지 결과:")
print("=" * 60)
print(f"HE  : {he_result}")
print(f"SIM : {sim_result}")

if he_result is None:
    print("\n[WARNING] HE vendor 파일을 찾을 수 없습니다.")
    print("  파일명에 'HE' 또는 'hitachi' 토큰이 포함되어 있는지 확인하세요.")
if sim_result is None:
    print("\n[WARNING] SIM vendor 파일을 찾을 수 없습니다.")
    print("  파일명에 'SIM', 'simense', 또는 'siemens' 토큰이 포함되어 있는지 확인하세요.")
PY
```

**예상 출력:**

```
============================================================
자동탐지 결과:
============================================================
HE  : (WindowsPath('C:/PP1030/data/raw/Case List(HE).xlsx'), 'hitachi')
SIM : (WindowsPath('C:/PP1030/data/raw/Case List(SIM_20251030).xlsm'), 'simense')
```

- `None`이 표시되면 `data/raw` 폴더에서 해당 토큰을 찾을 수 없습니다.
- 파일명에 토큰이 포함되어 있는지 확인하세요.

---

## 3️⃣ 실행 방법 A: 설정 파일 + 자동탐지 (권장)

### 설정 파일 수정

`config/pipeline_config.yaml`에서 경로를 `auto` 또는 실제 경로로 설정:

```yaml
stages:
  stage1:
    io:
      master_file: "auto"              # HE vendor 자동탐지
      warehouse_file: "auto"            # HE vendor 자동탐지
      output_file: "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
```

**또는 직접 경로 지정:**

```yaml
stages:
  stage1:
    io:
      master_file: "data/raw/Case List(HE).xlsx"
      warehouse_file: "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx"
      output_file: "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
```

### 전체 파이프라인 실행

```powershell
python run/run_pipeline.py --all
```

### 특정 Stage만 실행

```powershell
# Stage 1만
python run/run_pipeline.py --stage 1

# Stage 1, 2만
python run/run_pipeline.py --stage 1,2

# Stage 1, 2, 3
python run/run_pipeline.py --stage 1,2,3
```

---

## 4️⃣ 실행 방법 B: 명령줄 직접 지정

개별 Stage를 직접 실행할 수도 있습니다:

### Stage 1: 데이터 동기화

```powershell
# HE vendor
python run/run_pipeline.py --stage 1

# 설정 파일에서 master_file과 warehouse_file이 자동탐지되도록 설정되어 있어야 함
```

**현재 설정 파일 확인:**

```powershell
# 설정 파일 내용 확인
Get-Content config/pipeline_config.yaml | Select-String -Pattern "master_file|warehouse_file"
```

---

## 5️⃣ 빠른 검증

### 유닛 테스트

```powershell
pytest -q
```

### 린트 검사

```powershell
ruff check .
```

### 포맷 검사

```powershell
black --check .
```

---

## 6️⃣ 트러블슈팅

### 문제 1: "파일 사용 중" 오류

**증상:**
```
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
```

**해결:**
- 해당 Excel 파일을 열고 있는 프로그램(Excel, 다른 Python 프로세스 등)을 모두 종료
- 파일 탐색기에서 파일을 선택하고 프로세스 확인
- 재실행

### 문제 2: 토큰 미인식

**증상:**
```
[AUTO-DETECT] HE vendor file: None
자동탐지 실패: HE vendor 파일을 data/raw에서 찾을 수 없습니다.
```

**원인:**
- `he`가 단독 토큰이 아닐 수 있음 (예: `the-file.xlsx`에서 `he`가 부분 문자열로 인식되지 않음)

**해결:**
1. 파일명을 토큰 경계가 분리되도록 변경:
   - ✅ `Case List (HE).xlsx`
   - ✅ `Case List_HE.xlsx`
   - ✅ `Case List-HE.xlsx`
   - ❌ `CaseListhe.xlsx` (토큰 경계 없음)

2. 토큰 확인:
   ```powershell
   python -c "from scripts.core.file_finder import _match_vendor_from_stem; print(_match_vendor_from_stem('Case List(HE)'))"
   ```

### 문제 3: SIM/HE 둘 다 다수 파일 발견

**원인:**
- `file_finder`가 **얕은 경로 + 짧은 파일명**을 우선 선택
- 같은 vendor에 여러 파일이 있을 때 대표 파일 선택 기준 충돌

**해결:**
1. 파일명 정리: 한 vendor당 하나의 대표 파일만 유지
2. 확장자 제한으로 후보 축소:
   ```powershell
   $env:HVDC_FILE_FINDER_ALLOWED_SUFFIXES = ".xlsx"
   ```

### 문제 4: 경로 슬래시 문제

PowerShell과 Python 모두 자동 처리하므로 걱정하지 않아도 됩니다:
- PowerShell: `\` (백슬래시)
- Python `Path`: OS별로 자동 변환
- 설정 파일: `/` 또는 `\` 모두 가능

### 문제 5: SIEMENS 혼동

**증상:**
- `SIEMENS`와 `SIMENSE` 파일이 섞여 있어 혼동 발생

**해결:**
SIEMENS 토큰을 비활성화:

```powershell
$env:HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS = "0"
```

이 경우 `siemens` 토큰은 무시되고 `simense`만 인식됩니다.

---

## 7️⃣ 실행 로그 확인

### 로그 파일 위치

```
logs/pipeline.log
```

### 실시간 로그 확인 (PowerShell)

```powershell
Get-Content logs/pipeline.log -Wait -Tail 50
```

---

## 8️⃣ 실행 예시 (전체 흐름)

```powershell
# 1. 프로젝트 루트로 이동
cd C:\PP1030

# 2. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 3. 자동탐지 사전 점검
python - << 'PY'
from pathlib import Path
from scripts.core.file_registry import FileRegistry
reg = FileRegistry(Path('.').resolve())
print("HE :", reg.get_raw_with_canonical("HE"))
print("SIM:", reg.get_raw_with_canonical("SIM"))
PY

# 4. Stage 1, 2 실행
python run/run_pipeline.py --stage 1,2

# 5. 결과 확인
Get-ChildItem data/processed/synced/*.xlsx
Get-ChildItem data/processed/derived/*.xlsx
```

---

## 9️⃣ Bash 버전 (Linux/WSL)

```bash
cd /path/to/project

# 가상환경 설정
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 환경 변수 설정 (선택)
export HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=1

# 자동탐지 확인
python - << 'PY'
from pathlib import Path
from scripts.core.file_registry import FileRegistry
reg = FileRegistry(Path('.').resolve())
print("HE :", reg.get_raw_with_canonical("HE"))
print("SIM:", reg.get_raw_with_canonical("SIM"))
PY

# 파이프라인 실행
python ./run/run_pipeline.py --stage 1,2,3
```

---

## 📚 참고 자료

- **파이프라인 실행 흐름 상세**: `docs/reports/PIPELINE_EXECUTION_FLOW_DETAILED.md`
- **File Finder 기술 문서**: `scripts/core/file_finder.py`
- **File Registry 사용법**: `scripts/core/file_registry.py`

---

## ✅ 체크리스트

파이프라인 실행 전 확인:

- [ ] `data/raw/` 폴더에 필요한 파일 존재
- [ ] 파일명에 vendor 토큰 포함 (`HE`, `HITACHI`, `SIM`, `SIMENSE`, `SIEMENS`)
- [ ] 설정 파일에서 `master_file`과 `warehouse_file` 경로 설정 (또는 `auto`)
- [ ] 가상환경 활성화됨
- [ ] 필요한 패키지 설치됨 (`pip install -r requirements.txt`)
- [ ] Excel 파일이 다른 프로그램에서 열려있지 않음

---

**이 가이드에 따라 실행하면, 파일명 변형이 있어도 `data/raw`에서 자동으로 파일을 찾아 Stage 1→2→3까지 실행됩니다.**

