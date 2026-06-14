# HVDC 파이프라인 자동탐지 실행 가이드

## 📋 문서 정보
- **작성일**: 2025-11-02
- **버전**: v1.0
- **대상 환경**: Windows PowerShell, Linux/WSL Bash
- **상태**: ✅ 완료

---

## 0) 준비(1회)

### 1. 프로젝트 루트로 이동

```powershell
cd C:\PP1030
```

### 2. 가상환경 & 패키지 (선택)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 원본 배치(파일명은 유연 매칭됨)

```
data/
  raw/
    Case List(HE).xlsx              # HE vendor master file
    Case List(SIM_20251030).xlsm   # SIM vendor master file
    HVDC WAREHOUSE_HITACHI(HE).xlsx # HE vendor warehouse
    HVDC WAREHOUSE_SIMENSE(SIM).xlsm # SIM vendor warehouse
    [선택] HVDC WAREHOUSE_SIEMENS.xlsx  ← SIEMENS 토큰도 허용
```

---

## 1) 자동탐지 옵션(선택)

### 기본값: **SIEMENS 토큰 포함 = ON**

- 끄고 싶으면(예: 혼동 방지):

```powershell
$env:HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS = "0"
```

- 확장자 제한(선택):

```powershell
$env:HVDC_FILE_FINDER_ALLOWED_SUFFIXES = ".xlsx,.xlsm"
```

---

## 2) 사전 점검(10초)

**자동탐지 결과만 출력해서 확인**:

```powershell
# PowerShell 스크립트 사용
.\run\check_autodetect.ps1

# 또는 직접 Python 실행
python -c "from pathlib import Path; from scripts.core.file_registry import FileRegistry; reg = FileRegistry(Path('.').resolve()); print('HE:', reg.get_raw_with_canonical('HE')); print('SIM:', reg.get_raw_with_canonical('SIM'))"
```

- `('...HVDC WAREHOUSE_HITACHI(HE).xlsx', 'hitachi')` 처럼 보이면 OK.
- `None`이면 `data/raw` 파일명에 토큰이 안 잡힌 것. (예: `he`가 단독 토큰이 아니거나 오탈자)

---

## 3) 실행 — 모드 A: **설정파일 + auto**

`config/pipeline_config.yaml`에서 **경로를 `auto`로 설정**하면 자동 대체됩니다.

### 설정 예시:

```yaml
stages:
  stage1:
    io:
      master_file: "auto"              # HE vendor 자동탐지
      warehouse_file: "auto"           # HE vendor 자동탐지
      output_file: data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx
```

### 실행:

```powershell
# 전체 실행 (Stage 1-4)
python .\run\run_pipeline.py --all

# Stage 1, 2, 3만 실행
python .\run\run_pipeline.py --stage 1,2,3

# 또는 PowerShell 스크립트 사용 (권장)
.\run\run_stage1_2_3_autodetect.ps1
```

---

## 4) 실행 — 모드 B: **직접 경로 지정**

설정 파일에서 직접 경로를 지정할 수도 있습니다:

```yaml
stages:
  stage1:
    io:
      master_file: data/raw/Case List(HE).xlsx
      warehouse_file: data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx
      output_file: data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx
```

---

## 5) 빠른 검증(권장)

```powershell
# 유닛테스트
pytest -q

# 린트 체크
ruff check .

# 포맷 체크
black --check .
```

---

## 6) 트러블슈팅

### 엑셀 열림 오류
**증상**: "파일 사용 중" 오류  
**해결**: 해당 Excel 파일을 닫고 재실행

### 토큰 미인식
**증상**: `None` 반환  
**원인**: `he`가 **단독 토큰**이 아닐 수 있음  
**해결**: 파일명을 `... (HE).xlsx`·`..._HE.xlsx`처럼 경계 분리

### SIM/HE 둘 다 다수
**증상**: 예상과 다른 파일이 선택됨  
**원인**: `file_finder`가 **얕은 경로 + 짧은 이름**을 우선  
**해결**: 파일명을 정리하거나 `allowed_suffixes`로 후보 축소

### 경로 슬래시 문제
**원인**: PowerShell과 Python 경로 구분자 차이  
**해결**: Python 내부는 `Path`가 OS별로 처리하므로 경로 문자열 그대로 사용

### SIEMENS 혼동
**증상**: SIM과 SIEMENS가 섞여 들어올 때  
**해결**: `HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=0`으로 끄기

---

## 7) Bash 버전 (Linux/WSL)

```bash
cd /path/to/project

# 가상환경 설정
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 환경 변수 설정
export HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=1

# 사전 점검
python -c "from pathlib import Path; from scripts.core.file_registry import FileRegistry; reg = FileRegistry(Path('.').resolve()); print('HE :', reg.get_raw_with_canonical('HE')); print('SIM:', reg.get_raw_with_canonical('SIM'))"

# 파이프라인 실행
python ./run/run_pipeline.py --stage 1,2,3
```

---

## 8) 실행 예시

### 예시 1: 자동탐지 사용

```powershell
# 1. 사전 점검
.\run\check_autodetect.ps1

# 2. Stage 1, 2, 3 실행
python .\run\run_pipeline.py --stage 1,2,3
```

### 예시 2: PowerShell 스크립트 사용

```powershell
.\run\run_stage1_2_3_autodetect.ps1
```

### 예시 3: SIEMENS 토큰 비활성화

```powershell
$env:HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS = "0"
python .\run\run_pipeline.py --stage 1,2,3
```

---

## 참고사항

- **자동탐지 우선순위**: 얕은 경로 > 짧은 파일명
- **토큰 매칭**: 대소문자 구분 없음, 토큰 경계 분리 필수
- **환경 변수**: PowerShell 세션 내에서만 유지 (영구 설정은 시스템 환경 변수 사용)

---

이 가이드에 따라 파일명 변종(SIM/SIEMENS/simense, HITACHI/HE/(HE))이 섞여 들어와도 `data/raw`에서 자동으로 잡아 Stage1→2→3까지 실행됩니다.

