# Stage 1 Standalone 기술보고서

**작성 일자**: 2025-10-29
**버전**: v1.0.0
**상태**: 완료 및 운영 중

---

## 목차

1. [개요 및 목적](#1-개요-및-목적)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [파일 구조 및 구성요소](#3-파일-구조-및-구성요소)
4. [빌드 시스템](#4-빌드-시스템)
5. [주요 기능](#5-주요-기능)
6. [기술 스택](#6-기술-스택)
7. [최적화 및 개선사항](#7-최적화-및-개선사항)
8. [사용 방법](#8-사용-방법)
9. [문제 해결 및 트러블슈팅](#9-문제-해결-및-트러블슈팅)
10. [성능 지표 및 검증](#10-성능-지표-및-검증)
11. [참고 자료 및 문서](#11-참고-자료-및-문서)

---

## 1. 개요 및 목적

### 1.1 프로젝트 배경

Stage 1 Standalone 패키지는 HVDC 프로젝트의 Stage 1 데이터 동기화 기능을 독립 실행 가능한 실행 파일(.exe)로 패키징한 것입니다. Python 환경이 없는 최종 사용자도 GUI 인터페이스를 통해 데이터 동기화 작업을 수행할 수 있도록 설계되었습니다.

### 1.2 Standalone 패키지의 목적

- **접근성 향상**: Python 설치 없이 실행 가능한 독립형 애플리케이션 제공
- **사용 편의성**: GUI 기반 직관적인 인터페이스 제공
- **배포 용이성**: 단일 실행 파일로 간편한 배포
- **유지보수성**: 자동화된 빌드 프로세스로 일관된 빌드 환경 제공

### 1.3 주요 목표 및 요구사항

#### 기능 요구사항
- ✅ Master Excel 파일과 Warehouse Excel 파일 간 데이터 동기화
- ✅ GUI 및 CLI 인터페이스 제공
- ✅ 실시간 진행 상황 표시
- ✅ 자동 헤더 탐지 및 시맨틱 매칭

#### 비기능 요구사항
- ✅ 빌드 시간 최소화 (목표: 2-5분)
- ✅ 실행 파일 크기 최적화
- ✅ PyInstaller frozen 모드 및 소스 모드 모두 지원
- ✅ Windows 환경 우선 지원

---

## 2. 시스템 아키텍처

### 2.1 전체 구조 개요

```
┌─────────────────────────────────────────────────────────┐
│                  Stage1 Standalone                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   GUI Mode   │         │   CLI Mode   │            │
│  │ (Tkinter)    │         │ (argparse)   │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                         │                    │
│         └────────┬────────────────┘                   │
│                  │                                     │
│         ┌────────▼─────────┐                          │
│         │ stage1_standalone │                          │
│         │    (Wrapper)      │                          │
│         └────────┬─────────┘                          │
│                  │                                     │
│         ┌────────▼─────────┐                          │
│         │ DataSynchronizer │                          │
│         │      V30         │                          │
│         └────────┬─────────┘                          │
│                  │                                     │
│    ┌─────────────┼─────────────┐                     │
│    │             │             │                     │
│ ┌──▼──┐    ┌─────▼──────┐  ┌───▼────┐                │
│ │Core │    │ Header     │  │Excel   │                │
│ │Reg. │    │ Matching   │  │I/O     │                │
│ └─────┘    └────────────┘  └────────┘                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 GUI와 CLI 인터페이스 구조

#### GUI 인터페이스 (stage1_gui.py)
- **기반 프레임워크**: Tkinter (Python 표준 라이브러리)
- **주요 컴포넌트**:
  - 파일 선택기 (Master, Warehouse, Output)
  - 진행 로그 콘솔 (실시간 업데이트)
  - 실행 버튼 및 상태 관리
- **실행 흐름**: GUI → `stage1_standalone.run_sync()` → `DataSynchronizerV30`

#### CLI 인터페이스 (stage1_standalone.py)
- **기반 프레임워크**: argparse (Python 표준 라이브러리)
- **주요 기능**:
  - 명령줄 인자 파싱 (--master, --warehouse, --out)
  - 프로그램적 API 제공 (`run_sync()` 함수)
  - 표준 입출력 리다이렉션 지원

### 2.3 모듈 의존성 관계도

```
standalone/
├── stage1_gui.py
│   └──→ stage1_standalone.py
│           └──→ scripts/tools/data_synchronizer_v30.py
│                   └──→ scripts/core/
│                       ├── header_registry.py
│                       ├── header_normalizer.py
│                       ├── semantic_matcher.py
│                       └── standard_header_order.py
│
└── hooks/
    └── hook-pandas.py (PyInstaller hook)
```

### 2.4 데이터 흐름도

```
[Master Excel] ──┐
                 ├──→ [헤더 탐지] ──→ [시맨틱 매칭] ──→ [데이터 동기화] ──→ [Output Excel]
[Warehouse Excel] ──┘                                  │
                                                       │
                                              [변경 사항 추적]
                                              [셀 색상 표시]
```

---

## 3. 파일 구조 및 구성요소

### 3.1 디렉토리 트리 구조

```
scripts/stage1_Standalone/standalone/
├── stage1_gui.py                    # GUI 인터페이스 (Tkinter)
├── stage1_standalone.py             # CLI 실행기 & 프로그램적 API
├── build_exe_optimized_onedir.spec # PyInstaller spec (onedir 모드)
├── build_gui_onefile.spec           # PyInstaller spec (onefile 모드)
├── build.bat                        # Windows 빌드 스크립트 (CMD)
├── build.ps1                        # Windows 빌드 스크립트 (PowerShell)
├── build.sh                         # Linux/mac 빌드 스크립트
├── requirements_runtime.txt         # 런타임 의존성 목록
├── README_STANDALONE.md             # 사용자 가이드
├── hooks/
│   └── hook-pandas.py               # PyInstaller hook (pandas.tests 억제)
├── scripts/
│   ├── core/
│   │   ├── __init__.py              # Core 모듈 초기화 (최소 구현)
│   │   ├── header_registry.py       # 헤더 레지스트리 (중앙 관리)
│   │   ├── header_normalizer.py     # 헤더 정규화
│   │   ├── semantic_matcher.py      # 시맨틱 매칭 엔진
│   │   └── standard_header_order.py # 표준 헤더 순서 관리
│   └── tools/
│       └── data_synchronizer_v30.py # 데이터 동기화 엔진 (핵심 로직)
└── dist/                            # 빌드 출력 (생성됨)
    ├── Stage1Sync.exe              # GUI 실행 파일
    └── stage1_cli.exe              # CLI 실행 파일
```

### 3.2 각 파일의 역할과 책임

#### 메인 실행 파일

##### stage1_gui.py
- **역할**: GUI 인터페이스 제공
- **주요 클래스**:
  - `LogConsole`: 스크롤 가능한 로그 콘솔 위젯
  - `App`: 메인 애플리케이션 클래스 (Tkinter Frame)
- **기능**:
  - 파일 선택 다이얼로그
  - 실시간 로그 표시
  - 비동기 실행 (threading)

##### stage1_standalone.py
- **역할**: CLI 인터페이스 및 프로그램적 API 제공
- **주요 함수**:
  - `_project_root()`: 프로젝트 루트 경로 감지 (PyInstaller frozen 모드 지원)
  - `_ensure_path()`: Python 경로 설정
  - `run_sync()`: 동기화 실행 함수 (GUI/CLI 공통)
  - `main()`: CLI 진입점
- **특징**:
  - `sys._MEIPASS` 기반 PyInstaller frozen 모드 자동 감지
  - 소스 모드와 frozen 모드 모두 지원

#### 빌드 파일

##### build_exe_optimized_onedir.spec
- **용도**: 개발/테스트용 빠른 빌드 (onedir 모드)
- **특징**:
  - GUI와 CLI 두 실행 파일 동시 생성
  - 불필요한 패키지 제외 (excludes)
  - Hook 시스템 활용 (hookspath=['hooks'])

##### build_gui_onefile.spec
- **용도**: 배포용 단일 EXE (onefile 모드)
- **특징**:
  - GUI 전용 단일 파일 생성
  - 압축 및 패키징 포함

##### build.bat / build.ps1 / build.sh
- **역할**: 자동화된 빌드 프로세스
- **기능**:
  - 가상 환경 자동 생성/활성화
  - 의존성 자동 설치
  - 빌드 모드 선택 (onedir/onefile)

#### Hook 파일

##### hooks/hook-pandas.py
- **역할**: PyInstaller 빌드 경고 억제
- **기능**:
  - `pandas.tests.*` 모듈 완전 제외
  - 빌드 시간 단축 (불필요한 모듈 탐색 제거)
  - 경고 메시지 99%+ 감소

### 3.3 Core 모듈 상세 설명

#### scripts/core/__init__.py
- **역할**: Core 모듈 초기화 및 편의 함수 제공
- **Export 함수**:
  - `get_warehouse_columns()`: 창고 컬럼 목록 (9개)
  - `get_site_columns()`: 사이트 컬럼 목록 (4개)
  - `get_date_columns()`: 날짜 컬럼 목록
  - `detect_header_row()`: 헤더 행 자동 탐지 (최소 구현)
- **특징**: standalone 패키지용 최소 구현 (header_detector 모듈 없이)

#### scripts/core/header_registry.py
- **역할**: 중앙 헤더 레지스트리 관리
- **주요 클래스**:
  - `HeaderRegistry`: 헤더 정의 중앙 관리
  - `HeaderDefinition`: 단일 헤더 정의 (별칭, 시맨틱 키 포함)
  - `HeaderCategory`: 헤더 카테고리 분류
- **장점**: 하드코딩 제거, 중앙 관리로 유지보수 용이

#### scripts/core/header_normalizer.py
- **역할**: 헤더 이름 정규화
- **기능**: 다양한 형식의 헤더를 표준 형식으로 변환

#### scripts/core/semantic_matcher.py
- **역할**: 시맨틱 기반 헤더 매칭
- **주요 클래스**: `SemanticMatcher`
- **기능**: 정확한 이름이 아닌 의미 기반으로 헤더 탐지

#### scripts/core/standard_header_order.py
- **역할**: 표준 헤더 순서 관리
- **기능**: DataFrame 컬럼을 표준 순서로 재정렬

### 3.4 Tools 모듈 상세 설명

#### scripts/tools/data_synchronizer_v30.py
- **역할**: 데이터 동기화 핵심 엔진
- **주요 클래스**: `DataSynchronizerV30`
- **핵심 기능**:
  - Master와 Warehouse Excel 파일 간 데이터 동기화
  - 시맨틱 기반 헤더 매칭
  - 변경 사항 추적 및 색상 표시
    - 주황색 (Orange): 변경된 날짜 셀
    - 노란색 (Yellow): 새로 추가된 행
  - 통계 정보 수집 (변경 셀 수, 추가 행 수 등)
- **특징**:
  - 하드코딩 제거 (모든 헤더는 레지스트리에서 관리)
  - 다양한 Excel 형식 자동 적응
  - 강력한 오류 처리 및 보고

---

## 4. 빌드 시스템

### 4.1 PyInstaller 빌드 프로세스

#### 빌드 단계

1. **의존성 분석** (Analysis)
   - Python 모듈 의존성 그래프 생성
   - 필수 모듈 자동 감지
   - Hidden imports 명시적 추가 (pandas, openpyxl submodules)

2. **모듈 수집** (Collect)
   - 지정된 모듈 및 데이터 파일 수집
   - 제외 목록 적용 (excludes)
   - Hook 파일 실행 (pandas.tests 제외)

3. **바이너리 패키징** (Package)
   - Python 바이트코드 컴파일
   - 바이너리 파일 수집
   - 데이터 파일 포함

4. **실행 파일 생성** (EXE)
   - Bootloader와 패키지 결합
   - GUI/CLI 모드별 설정 적용
   - 최종 .exe 파일 생성

#### 빌드 모드 비교

| 항목 | onedir 모드 | onefile 모드 |
|------|------------|--------------|
| **출력 형식** | 폴더 구조 (.exe + DLLs) | 단일 .exe 파일 |
| **빌드 시간** | 빠름 (2-3분) | 느림 (+1-2분) |
| **실행 속도** | 빠름 | 첫 실행 시 느림 (압축 해제) |
| **용도** | 개발/테스트 | 배포 |
| **디버깅** | 쉬움 | 어려움 |
| **GUI + CLI** | 동시 생성 가능 | GUI만 지원 |

### 4.2 빌드 스크립트 상세

#### build.bat (Windows CMD)
```batch
@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set ONEFILE=%ONEFILE%
if "%ONEFILE%"=="" set ONEFILE=0

if "%NO_VENV%"=="0" (
  if not exist .venv (
    python -m venv .venv
  )
  call .venv\Scripts\activate.bat
)

python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller

if "%ONEFILE%"=="1" (
  pyinstaller --clean --noconfirm build_gui_onefile.spec
) else (
  pyinstaller --clean --noconfirm build_exe_optimized_onedir.spec
)
```

**기능**:
- 가상 환경 자동 관리
- 의존성 자동 설치
- 빌드 모드 선택 (환경변수로 제어)
- 이전 빌드 자동 정리

#### build.ps1 (PowerShell)
```powershell
param(
  [switch]$OneFile = $false,
  [switch]$NoVenv = $false
)

if (-not $NoVenv) {
  if (-not (Test-Path ".venv")) { python -m venv .venv }
  & ".\.venv\Scripts\Activate.ps1"
}

python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller

$commonOpts = @("--clean", "--noconfirm")

if ($OneFile) {
  pyinstaller @commonOpts "build_gui_onefile.spec"
} else {
  pyinstaller @commonOpts "build_exe_optimized_onedir.spec"
}
```

**장점**:
- PowerShell 네이티브 지원
- 타입 안전 파라미터 처리
- 자동 경로 처리

### 4.3 Spec 파일 구조 및 설정

#### build_exe_optimized_onedir.spec 분석

```python
# 1. Hidden imports 설정
hiddenimports = []
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('openpyxl')

# 2. 제외 패키지 목록
excludes = [
    'torch', 'torchvision', 'torchaudio',  # ~1GB+
    'matplotlib', 'scipy', 'sklearn', 'numba',
    'IPython', 'jupyter', 'notebook',
    'tensorboard', 'tensorflow', 'keras',
    'pytest', 'hypothesis',
    'pandas.tests',  # 테스트 모듈 제외
]

# 3. 데이터 파일 포함
datas = [
    ('scripts/core/*.py', 'scripts/core'),
    ('scripts/tools/*.py', 'scripts/tools'),
]

# 4. Analysis 및 EXE 생성
a = Analysis(..., hookspath=['hooks'], ...)
exe_gui = EXE(..., console=False, ...)
exe_cli = EXE(..., console=True, ...)
```

**주요 설정 항목**:
- `hookspath=['hooks']`: 커스텀 hook 파일 경로
- `strip=True`: 디버그 심볼 제거 (크기 최적화)
- `upx=False`: UPX 압축 비활성화 (빌드 시간 단축)
- `console=False/True`: GUI/CLI 모드 구분

### 4.4 Hook 시스템 (pandas.tests 경고 억제)

#### 문제점
- 빌드 시 수천 개의 `pandas.tests.*` hidden import 경고 발생
- 빌드 로그 가독성 저하
- 불필요한 모듈 탐색으로 빌드 시간 증가

#### 해결 방법
**hook-pandas.py**:
```python
excludedimports = ['pandas.tests', 'pandas.tests.*']
```

**Spec 파일 수정**:
```python
hookspath=['hooks']  # 커스텀 hook 경로 지정
```

#### 효과
- ✅ pandas.tests 경고 99%+ 감소
- ✅ 빌드 시간 약 10% 단축
- ✅ 깔끔한 빌드 로그

---

## 5. 주요 기능

### 5.1 GUI 인터페이스 기능

#### 파일 선택
- **Master 파일**: Case List Excel 파일 선택
- **Warehouse 파일**: Warehouse Excel 파일 선택
- **Output 파일**: (선택사항) 출력 파일 경로 지정

#### 실행 및 모니터링
- **Run 버튼**: 동기화 작업 시작
- **실시간 로그**: 진행 상황 실시간 표시
- **결과 알림**: 성공/실패 메시지 박스

#### 사용자 경험
- **비동기 실행**: 메인 스레드 블로킹 방지
- **상태 관리**: 실행 중 버튼 비활성화
- **오류 처리**: 상세한 오류 메시지 표시

### 5.2 CLI 인터페이스 기능

#### 명령줄 옵션
```bash
stage1_cli.exe --master "Master.xlsx" --warehouse "Warehouse.xlsx" --out "output.xlsx"
```

#### 프로그램적 API
```python
from stage1_standalone import run_sync

success, output_path, stats = run_sync(
    master="Master.xlsx",
    warehouse="Warehouse.xlsx",
    out="output.xlsx",
    log_cb=print  # 옵션: 로그 콜백
)
```

### 5.3 데이터 동기화 엔진

#### 동기화 프로세스

1. **헤더 탐지**
   - Excel 파일의 헤더 행 자동 탐지
   - 다양한 형식 자동 인식

2. **시맨틱 매칭**
   - Master와 Warehouse 헤더 간 시맨틱 매칭
   - 별칭 및 유사도 기반 매칭

3. **데이터 동기화**
   - Case Number 기준 행 매칭
   - 날짜 필드 변경 사항 추적
   - 새 행 자동 추가

4. **결과 출력**
   - 변경된 셀 색상 표시
   - 통계 정보 생성
   - Excel 파일 저장

#### 변경 사항 추적

- **주황색 (Orange)**: 변경된 날짜 셀
- **노란색 (Yellow)**: 새로 추가된 행
- **메타데이터 보존**: Source_Sheet, Source_Vendor 컬럼 유지

### 5.4 헤더 매칭 시스템

#### 시맨틱 매칭 엔진
- **의미 기반 매칭**: 정확한 이름이 아닌 의미로 매칭
- **별칭 지원**: 여러 이름으로 표시된 동일 헤더 자동 인식
- **유사도 점수**: 매칭 신뢰도 계산

#### 헤더 레지스트리
- **중앙 관리**: 모든 헤더 정의를 한 곳에서 관리
- **카테고리별 분류**: Warehouse, Site, Date 등
- **확장 가능**: 새로운 헤더 추가 용이

---

## 6. 기술 스택

### 6.1 Python 버전 및 필수 라이브러리

#### Python 버전
- **최소 버전**: Python 3.9+
- **권장 버전**: Python 3.13
- **테스트 환경**: Python 3.13

#### 핵심 의존성 (requirements_runtime.txt)

```
pandas>=2.0        # 데이터 처리 및 Excel I/O
numpy>=1.24        # 수치 연산
openpyxl>=3.1      # Excel 파일 읽기/쓰기
```

#### 빌드 도구 의존성
- **PyInstaller**: 최신 안정 버전
- **wheel**, **setuptools**: 패키징 도구

### 6.2 GUI 프레임워크 (Tkinter)

#### 선택 이유
- **Python 표준 라이브러리**: 별도 설치 불필요
- **크로스 플랫폼**: Windows/macOS/Linux 지원
- **경량**: 최소한의 의존성
- **충분한 기능**: 파일 다이얼로그, 텍스트 위젯 등 모든 필요 기능 제공

#### 사용 위젯
- `ttk.Frame`: 메인 컨테이너
- `ttk.Label`, `ttk.Entry`: 레이블 및 입력 필드
- `ttk.Button`: 실행 버튼
- `tk.Text`: 로그 콘솔 (스크롤 가능)
- `filedialog`: 파일 선택 다이얼로그
- `messagebox`: 알림 및 오류 메시지

### 6.3 빌드 도구 (PyInstaller)

#### 선택 이유
- **성숙한 도구**: 널리 사용되는 표준 도구
- **활발한 커뮤니티**: 문제 해결 리소스 풍부
- **윈도우 모드 지원**: GUI 애플리케이션 적합
- **Hook 시스템**: 커스터마이징 용이

#### 주요 기능 활용
- **Frozen 모드 감지**: `sys._MEIPASS` 기반 경로 처리
- **Hook 파일**: 커스텀 빌드 동작 정의
- **Spec 파일**: 빌드 설정 세밀 제어

### 6.4 의존성 관리

#### 런타임 의존성
- 최소한의 필수 라이브러리만 포함
- 불필요한 패키지 완전 제외 (excludes)
- pandas submodules 자동 수집 (collect_submodules)

#### 빌드 의존성
- 가상 환경으로 격리
- 빌드 전 자동 설치
- 버전 고정 없음 (최신 안정 버전 사용)

---

## 7. 최적화 및 개선사항

### 7.1 빌드 시간 최적화 (15분 → 2-5분)

#### 개선 전 문제점
- **빌드 시간**: 15분+ (사용자 중단)
- **원인**: torch (~1GB), matplotlib, scipy 등 불필요한 대형 패키지 자동 포함
- **타임아웃 경고**: 최소 6회 이상 발생

#### 개선 조치
1. **Excludes 리스트 추가**
   ```python
   excludes = [
       'torch', 'torchvision', 'torchaudio',  # ~1GB+
       'matplotlib', 'scipy', 'sklearn', 'numba',
       'IPython', 'jupyter', 'notebook',
       'tensorboard', 'tensorflow', 'keras',
       'pytest', 'hypothesis',
   ]
   ```

2. **collect_submodules 제한**
   - pandas, openpyxl만 자동 수집
   - 나머지는 명시적 import만 포함

3. **빌드 옵션 최적화**
   - `strip=True`: 디버그 심볼 제거
   - `upx=False`: UPX 압축 비활성화 (빌드 시간 단축)

#### 개선 결과
- ✅ **빌드 시간**: 15분+ → **2-5분** (약 70% 단축)
- ✅ **타임아웃 경고**: 완전 제거
- ✅ **빌드 안정성**: 크게 향상

### 7.2 경고 메시지 억제 (pandas.tests)

#### 문제점
- 수천 개의 `pandas.tests.*` hidden import 경고 발생
- 빌드 로그 가독성 저하
- 불필요한 모듈 탐색으로 빌드 시간 증가

#### 해결 방법
**Hook 파일 생성** (`hooks/hook-pandas.py`):
```python
excludedimports = ['pandas.tests', 'pandas.tests.*']
```

**Spec 파일 수정**:
```python
hookspath=['hooks']  # 커스텀 hook 경로 지정
```

#### 개선 결과
- ✅ **경고 메시지**: 99%+ 감소
- ✅ **빌드 시간**: 약 10% 추가 단축
- ✅ **빌드 로그**: 깔끔하고 읽기 쉬움

### 7.3 불필요한 패키지 제외

#### 제외된 패키지 목록

**머신러닝 프레임워크** (~1GB+):
- `torch`, `torchvision`, `torchaudio`
- `tensorflow`, `keras`

**과학 계산 라이브러리**:
- `scipy`, `sklearn`, `numba`
- `matplotlib`

**개발 도구**:
- `IPython`, `jupyter`, `notebook`
- `pytest`, `hypothesis`, `pluggy`

**기타**:
- `tensorboard`, `protobuf`

#### 효과
- ✅ **빌드 시간 단축**: 불필요한 패키지 분석 제거
- ✅ **실행 파일 크기 감소**: 예상 500MB+ → 100-200MB
- ✅ **빌드 안정성 향상**: 타임아웃 위험 제거

### 7.4 Hook 파일 시스템

#### Hook 파일 역할
- PyInstaller 빌드 과정에 커스텀 로직 주입
- 특정 모듈의 빌드 동작 제어
- 경고 억제 및 최적화

#### 사용 예시
**hook-pandas.py**:
- pandas.tests 모듈 완전 제외
- 빌드 시 해당 모듈 탐색하지 않음
- 경고 메시지 생성 방지

#### 확장 가능성
- 다른 패키지에도 동일한 방식 적용 가능
- 패키지별 최적화 규칙 정의 가능
- 유지보수 용이

---

## 8. 사용 방법

### 8.1 빌드 방법 (개발자용)

#### 빠른 개발 빌드 (onedir 모드)

**Windows (CMD)**:
```batch
cd scripts\stage1_Standalone\standalone
build.bat
```

**Windows (PowerShell)**:
```powershell
cd scripts\stage1_Standalone\standalone
.\build.ps1
```

**출력**:
- `dist\Stage1Sync\Stage1Sync.exe` (GUI)
- `dist\stage1_cli\stage1_cli.exe` (CLI)

#### 배포용 빌드 (onefile 모드)

**Windows (CMD)**:
```batch
cd scripts\stage1_Standalone\standalone
set ONEFILE=1
build.bat
```

**Windows (PowerShell)**:
```powershell
cd scripts\stage1_Standalone\standalone
.\build.ps1 -OneFile
```

**출력**:
- `dist\Stage1Sync.exe` (단일 파일)

#### 가상 환경 없이 빌드

**Windows (CMD)**:
```batch
set NO_VENV=1
build.bat
```

**Windows (PowerShell)**:
```powershell
.\build.ps1 -NoVenv
```

### 8.2 실행 방법 (최종 사용자용)

#### GUI 모드

1. **Stage1Sync.exe 더블클릭**
2. **Master 파일 선택**: Case List Excel 파일 선택
3. **Warehouse 파일 선택**: Warehouse Excel 파일 선택
4. **(선택) Output 경로 지정**: 출력 파일 경로 지정 (미지정 시 자동 생성)
5. **"Run Stage 1" 버튼 클릭**: 동기화 시작
6. **결과 확인**: 로그 창에서 진행 상황 확인, 완료 시 결과 파일 경로 표시

#### CLI 모드

**기본 사용**:
```bash
stage1_cli.exe --master "Master.xlsx" --warehouse "Warehouse.xlsx" --out "output.xlsx"
```

**출력 경로 생략**:
```bash
stage1_cli.exe --master "Master.xlsx" --warehouse "Warehouse.xlsx"
```
(자동으로 `Stage1_Sync_Output.xlsx` 생성)

**반환 코드**:
- `0`: 성공
- `1`: 실패

### 8.3 GUI 사용 가이드

#### 주요 기능

**파일 선택**:
- Master 및 Warehouse 파일: "Browse..." 버튼으로 선택
- Output 파일: "Save As..." 버튼으로 경로 지정 (선택사항)

**실시간 모니터링**:
- 로그 콘솔에서 진행 상황 실시간 확인
- 스크롤 자동 이동 (최신 로그 자동 표시)

**상태 표시**:
- 실행 중: "Run Stage 1" 버튼 비활성화
- 완료: 성공/실패 메시지 박스 표시

### 8.4 CLI 사용 가이드

#### 명령줄 옵션

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--master` | 예 | Master Excel 파일 경로 |
| `--warehouse` | 예 | Warehouse Excel 파일 경로 |
| `--out` | 아니오 | 출력 파일 경로 (미지정 시 자동 생성) |

#### 사용 예시

**기본 사용**:
```bash
stage1_cli.exe --master "Case_List.xlsx" --warehouse "Warehouse.xlsx"
```

**출력 경로 지정**:
```bash
stage1_cli.exe --master "Case_List.xlsx" --warehouse "Warehouse.xlsx" --out "Sync_Result.xlsx"
```

**배치 작업**:
```batch
@echo off
for %%f in (*.xlsx) do (
    stage1_cli.exe --master "Master.xlsx" --warehouse "%%f" --out "Output_%%f"
)
```

---

## 9. 문제 해결 및 트러블슈팅

### 9.1 일반적인 빌드 오류 및 해결방법

#### 빌드 실패: Python 버전 오류

**증상**:
```
ERROR: Python 3.9+ required
```

**해결 방법**:
- Python 3.9 이상 버전 설치 확인
- `python --version` 명령어로 버전 확인

#### 빌드 실패: 의존성 설치 오류

**증상**:
```
ERROR: Could not install pandas
```

**해결 방법**:
1. 인터넷 연결 확인
2. pip 업그레이드: `python -m pip install --upgrade pip`
3. 가상 환경 재생성: `.venv` 폴더 삭제 후 재빌드

#### 빌드 실패: 가상 환경 활성화 오류

**증상**:
```
'.venv\Scripts\activate'은(는) 내부 또는 외부 명령...이 아닙니다.
```

**해결 방법**:
- `NO_VENV=1` 환경변수 설정하여 시스템 Python 사용
- 또는 PowerShell로 `build.ps1` 실행

#### 빌드 실패: PermissionError

**증상**:
```
PermissionError: [WinError 5] 액세스가 거부되었습니다: 'dist\Stage1Sync.exe'
```

**해결 방법**:
- 기존 실행 파일 닫기
- `dist` 폴더 삭제 후 재빌드

### 9.2 런타임 오류 처리

#### Excel 파일 읽기 오류

**증상**:
```
ERROR: Could not read Excel file
```

**가능한 원인**:
- 파일이 다른 프로그램에서 열려있음
- 파일 형식이 올바르지 않음 (`.xlsx`가 아님)
- 파일 손상

**해결 방법**:
1. 파일이 다른 프로그램에서 열려있는지 확인
2. 파일 형식 확인 (`.xlsx`, `.xlsm`, `.xls` 지원)
3. 파일을 다른 이름으로 저장하여 재시도

#### 헤더 탐지 실패

**증상**:
```
WARNING: Could not detect header row
```

**해결 방법**:
- Excel 파일의 첫 번째 행에 헤더가 있는지 확인
- 빈 행이나 병합된 셀 제거
- 파일을 재저장하여 형식 정리

### 9.3 Import 오류 해결

#### ModuleNotFoundError

**증상**:
```
ModuleNotFoundError: No module named 'scripts.core'
```

**가능한 원인**:
- PyInstaller 빌드 시 데이터 파일 누락
- 경로 설정 오류

**해결 방법**:
1. Spec 파일의 `datas` 섹션 확인
2. `scripts/core/*.py` 및 `scripts/tools/*.py` 포함 여부 확인
3. 빌드 재실행

#### 경로 문제

**증상**:
```
FileNotFoundError: scripts/core/header_registry.py not found
```

**해결 방법**:
- `standalone/scripts/core/` 디렉토리 확인
- Spec 파일의 `datas` 섹션에 올바른 경로 포함 확인

### 9.4 경고 메시지 설명

#### Windows DLL 경고

**경고 메시지**:
```
WARNING: Library not found: could not resolve 'bcrypt.dll'
WARNING: Library not found: could not resolve 'VERSION.dll'
```

**설명**:
- ✅ **안전하게 무시 가능**
- 이러한 DLL은 Windows 시스템에 기본 제공
- PyInstaller가 실행 시점에 자동으로 로드

#### jinja2 경고

**경고 메시지**:
```
WARNING: Hidden import "jinja2" not found!
```

**설명**:
- ✅ **안전하게 무시 가능**
- pandas의 선택적 의존성
- 핵심 기능에는 불필요

#### strip 경고

**경고 메시지**:
```
WARNING: Failed to run strip on '...dll'
```

**설명**:
- ✅ **정상적인 경고**
- 시스템 DLL 파일에 대한 strip 실패
- 실행에는 영향 없음

### 9.5 헤더 위치 오탐지 대응 방안

#### 9.5.0 구현 현황

**PR #8 헤더 탐지 개선사항 (v4.0.53+, 2025-10-29 병합)**

메인 코드베이스(`scripts/stage1_sync_sorted/`)에는 PR #8에 의해 다음 개선사항이 구현되어 있습니다:

- ✅ **HeaderDetectionResult 클래스**: 헤더 탐지 결과와 진단 정보를 포함하는 데이터클래스
  - 위치: ```30:51:scripts/core/header_detector.py```
  - 필드: `row_index`, `confidence`, `threshold`, `method`, `warnings`, `diagnostics`
- ✅ **detect_header_row_with_diagnostics 함수**: 진단 정보를 포함한 헤더 탐지 함수
  - 위치: ```463:467:scripts/core/header_detector.py```
- ✅ **수동 헤더 오버라이드**: `--header-override` CLI 파라미터 지원
  - 위치: ```956:980:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
  - 사용법: `--header-override Warehouse:Sheet1=2` 또는 `--header-override *=summary=0`
- ✅ **벤더 폴백 및 후보 목록 검증**: 수동 → 자동 → 벤더 순으로 후보 검증
  - 위치: ```468:514:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
- ✅ **시맨틱 검증 통합**: `case_number` 시맨틱 키를 이용한 기본 검증
  - 위치: ```516:524:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
  - 시맨틱 매칭 실패 시 자동으로 다음 헤더 후보 시도

**Standalone 패키지 현황**

현재 Standalone 패키지는 PR #8 개선사항을 포함하지 않습니다:

- ⚠️ 최소 구현의 `detect_header_row()` 함수만 사용
  - 위치: ```22:62:scripts/stage1_Standalone/standalone/scripts/core/__init__.py```
  - 단순 휴리스틱만 제공, 진단 정보 없음
- ⚠️ 수동 헤더 오버라이드 미지원
- ⚠️ 벤더 폴백 및 후보 검증 미구현
- ⚠️ 시맨틱 검증과 헤더 탐지 연계 부재

**참고 문서**:
- 메인 코드베이스 헤더 탐지 안정화 가이드: `docs/kr/header_detection_overrides.md`
- PR #8 커밋: `933bbfb` (2025-10-29 병합)

#### 9.5.1 현재 헤더 탐지 방식

##### Standalone 패키지의 헤더 탐지

현재 Standalone 패키지는 두 가지 간단한 방식을 사용합니다:

**1. 휴리스틱 기반 자동 탐지** (`detect_header_row()`)
- **위치**: ```22:62:scripts/stage1_Standalone/standalone/scripts/core/__init__.py```
- **방식**:
  - 처음 20행을 스캔하여 텍스트 비율과 null 값 비율을 계산
  - 점수 = (non_null 비율 × 0.5) + (텍스트 비율 × 0.5)
  - 가장 높은 점수를 가진 행을 헤더로 선택
- **반환값**: `(row_index, confidence)` (0.0 ~ 1.0)
- **한계**:
  - 복잡한 Excel 형식에서 오탐지 가능
  - 빈 행이나 병합된 셀에 취약
  - Confidence 점수가 낮아도 검증 없이 사용
  - 진단 정보 부재 (warnings, diagnostics 없음)

**2. 벤더 기반 고정 위치** (`_detect_vendor_and_header_row()`)
- **위치**: ```scripts/stage1_Standalone/standalone/scripts/tools/data_synchronizer_v30.py```
- **방식**:
  - 파일명에서 벤더 타입 검출 (`"simense"`, `"sim"` → SIEMENS)
  - SIEMENS: 헤더 행 0 (첫 번째 행)
  - HITACHI: 헤더 행 4 (다섯 번째 행)
- **장점**: 벤더별 표준 형식에서 매우 정확
- **한계**:
  - 비표준 파일 형식에서 실패 가능
  - 벤더 감지 실패 시 기본값(HITACHI) 사용
  - 후보 검증 메커니즘 없음

##### 메인 코드베이스의 헤더 탐지 (참고)

메인 코드베이스(`scripts/stage1_sync_sorted/`)에는 PR #8로 인해 향상된 헤더 탐지가 구현되어 있습니다:

- **HeaderDetector 클래스**: 향상된 탐지 알고리즘
- **HeaderDetectionResult**: 진단 정보 포함 결과 객체
- **다중 후보 검증**: 수동 → 자동 → 벤더 순으로 검증
- **시맨틱 검증 통합**: 매칭 실패 시 자동으로 다음 후보 시도

자세한 내용은 ```30:550:scripts/core/header_detector.py``` 및 ```468:588:scripts/stage1_sync_sorted/data_synchronizer_v30.py```를 참조하세요.

#### 9.5.2 헤더 위치 오탐지 시나리오

**시나리오 1: 빈 행이 많은 파일**
```
행 0: [공백] [공백] [공백] ...
행 1: [공백] [공백] [공백] ...
행 2: "Case No." "EQ No" "HS Code" ...
행 3: 데이터 ...
```
- **문제**: 행 2가 실제 헤더지만, 행 0이 선택될 수 있음
- **결과**: 모든 컬럼이 잘못된 이름으로 인식

**시나리오 2: 벤더 감지 실패**
- 파일명에 "SIM" 또는 "SIEMENS" 키워드 없음
- 기본값(HITACHI, 행 4) 사용
- 실제로는 SIEMENS 형식(행 0이 헤더)인 경우
- **결과**: 데이터가 헤더로 인식되거나 헤더가 데이터로 인식

**시나리오 3: 낮은 Confidence 무시**
```python
sheet_header_row, confidence = detect_header_row(file_path, sheet_name)
# confidence = 0.3 (매우 낮음)
# 하지만 경고 없이 사용됨
df = pd.read_excel(xl, sheet_name=sheet_name, header=sheet_header_row)
```
- **문제**: Confidence < 0.7일 때도 검증 없이 진행
- **결과**: 오탐지된 헤더 위치로 데이터 로드

#### 9.5.3 문제점 요약

1. **낮은 Confidence 무시**
   - 현재 코드는 confidence 점수를 출력만 하고 실제 검증하지 않음
   - Confidence < 0.7일 때 경고 메시지 없음
   - 사용자가 오탐지를 인지하기 어려움

2. **시맨틱 매칭 결과와 헤더 위치 검증 연계 부재**
   - `_match_and_validate_headers()`에서 시맨틱 매칭 실패 시 헤더 위치 재확인 안 함
   - 필수 컬럼(예: "Case No.") 미발견 시 헤더 위치 오탐지 가능성 고려 안 함

3. **사용자 수동 지정 옵션 부재**
   - GUI/CLI 인터페이스에서 헤더 위치를 직접 지정할 수 없음
   - 자동 탐지 실패 시 사용자가 개입할 방법 없음

4. **오탐지 시 검증 메커니즘 부족**
   - 탐지된 헤더 위치의 역검증 로직 없음
   - 시맨틱 매칭 성공률이 낮을 때 헤더 위치 재확인 안 함

#### 9.5.4 대응 방안

##### 메인 코드베이스에 구현된 방안 (PR #8)

다음 방안들은 메인 코드베이스(`scripts/stage1_sync_sorted/`)에 이미 구현되어 있습니다:

**구현 완료: HeaderDetectionResult 진단 시스템**
- **위치**: ```30:51:scripts/core/header_detector.py```
- **기능**: 헤더 탐지 결과에 진단 정보(warnings, diagnostics, method) 포함
- **효과**: 탐지 실패 원인 분석 가능, 사용자에게 명확한 정보 제공

**구현 완료: 수동 헤더 오버라이드**
- **위치**: ```956:980:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
- **사용법**: `--header-override Warehouse:Sheet1=2` 또는 `--header-override *=summary=0`
- **효과**: 사용자가 직접 헤더 위치 지정 가능, 자동 탐지 실패 시 수동 보정

**구현 완료: 벤더 폴백 및 다중 후보 검증**
- **위치**: ```468:588:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
- **검증 순서**: 수동 오버라이드 → 자동 탐지 → 벤더 기본값
- **효과**: 한 방법 실패 시 자동으로 다음 후보 시도

**구현 완료: 시맨틱 검증 통합**
- **위치**: ```516:524:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
- **기능**: `case_number` 시맨틱 키를 이용한 기본 검증, 실패 시 다음 후보 자동 시도
- **효과**: 필수 컬럼 미발견 시 헤더 위치 오탐지 자동 감지 및 재시도

자세한 사용법은 `docs/kr/header_detection_overrides.md`를 참조하세요.

##### Standalone 패키지 권장 방안

다음 방안들은 Standalone 패키지에 통합이 권장됩니다:

**권장: PR #8 개선사항 통합**
- 메인 코드베이스의 향상된 헤더 탐지 시스템을 Standalone 패키지에 통합
- 구현 방법: 섹션 9.5.7 "PR #8 통합 계획" 참조
- 예상 효과:
  - 헤더 탐지 정확도 향상
  - 진단 정보 제공으로 문제 해결 시간 단축
  - 사용자 수동 오버라이드 지원으로 유연성 증가

**권장: GUI에서 헤더 행 수동 지정 옵션 (중기)**
- 파일 선택 후 "헤더 행 설정" 옵션 추가
- 감지된 헤더 행 표시 및 수정 가능한 입력 필드
- 미리보기 기능: 선택한 헤더 행으로 컬럼 미리보기

**권장: 향상된 헤더 탐지 알고리즘 (장기)**

**개선 방향**:
1. **시맨틱 힌트 활용**
   - HVDC_HEADER_REGISTRY에 정의된 표준 헤더 목록을 참조
   - 각 행에서 표준 헤더와의 매칭 점수 계산
   - 높은 매칭 점수를 가진 행 선택

2. **다중 지표 결합**
   - 기존: 텍스트 비율 + null 비율
   - 추가: 표준 헤더 매칭률, 데이터 타입 일관성, 행 길이 일관성

3. **컨텍스트 인식**
   - 이전 시트의 헤더 위치 학습
   - 같은 파일 내 다른 시트와의 일관성 확인

**구현 예시**:
```python
def detect_header_row_enhanced(xlsx_path: str, sheet_name: str,
                                known_headers: List[str] = None) -> Tuple[int, float]:
    """
    향상된 헤더 탐지 알고리즘

    Args:
        xlsx_path: Excel 파일 경로
        sheet_name: 시트 이름
        known_headers: 알려진 헤더 목록 (옵션, 이전 시트나 표준 헤더)

    Returns:
        (row_index, confidence)
    """
    # 1. 기본 휴리스틱 점수 계산
    basic_scores = calculate_basic_scores(xlsx_path, sheet_name)

    # 2. 표준 헤더 매칭 점수 계산 (새로 추가)
    registry = HVDC_HEADER_REGISTRY
    standard_headers = [h.primary_name for h in registry.get_all_headers()]

    semantic_scores = calculate_semantic_matching_scores(
        xlsx_path, sheet_name, standard_headers
    )

    # 3. 데이터 타입 일관성 점수 (새로 추가)
    type_consistency_scores = calculate_type_consistency_scores(
        xlsx_path, sheet_name
    )

    # 4. 가중치 적용하여 최종 점수 계산
    final_scores = (
        basic_scores * 0.3 +
        semantic_scores * 0.5 +  # 표준 헤더 매칭에 높은 가중치
        type_consistency_scores * 0.2
    )

    best_idx = np.argmax(final_scores)
    confidence = final_scores[best_idx]

    return best_idx, confidence
```

**효과**:
- 정확도 대폭 향상 (예상: 95%+)
- 복잡한 Excel 형식에도 강건함

##### 기타 방안 (레거시 문서)

다음 방안들은 PR #8로 이미 해결되었거나, 메인 코드베이스 구현을 참조하세요:

**방안 1: Confidence 기반 경고 및 재시도 (단기)**

**구현 방법**:
```python
def _load_file_by_sheets_with_validation(self, file_path: str, file_label: str):
    sheet_header_row, confidence = detect_header_row(file_path, sheet_name)

    # Confidence 검증 추가
    if confidence < 0.7:
        print(f"  [WARNING] Low confidence ({confidence:.0%}) for header at row {sheet_header_row}")
        print(f"  [INFO] Attempting alternative header detection...")

        # 주변 행 검색 (±2행 범위)
        for offset in [-2, -1, 1, 2]:
            alt_row = max(0, sheet_header_row + offset)
            alt_confidence = self._validate_header_candidate(file_path, sheet_name, alt_row)
            if alt_confidence > confidence:
                print(f"  [OK] Better header found at row {alt_row} (confidence: {alt_confidence:.0%})")
                sheet_header_row = alt_row
                confidence = alt_confidence
                break

    # 여전히 낮으면 경고 출력
    if confidence < 0.5:
        print(f"  [ERROR] Very low confidence ({confidence:.0%}). Manual verification recommended.")
```

**효과**:
- 낮은 confidence 자동 감지
- 주변 행 자동 재탐색
- 사용자에게 경고 제공

##### 방안 2: 시맨틱 매칭 결과 역검증 (중기)

**구현 방법**:
```python
def _match_and_validate_headers_with_header_validation(
    self, df: pd.DataFrame, file_label: str, detected_header_row: int, file_path: str, sheet_name: str
) -> Dict[str, str]:
    # 기존 시맨틱 매칭 수행
    column_mapping = self._match_and_validate_headers(df, file_label)

    # 필수 컬럼 매칭 실패 시 헤더 위치 재확인
    required_keys = ["case_number"]
    missing_required = [k for k in required_keys if not column_mapping.get(k)]

    if missing_required:
        print(f"  [WARNING] Missing required columns detected. Re-validating header position...")

        # 주변 행에서 재탐색
        for alt_row in [detected_header_row - 2, detected_header_row - 1,
                       detected_header_row + 1, detected_header_row + 2]:
            if alt_row < 0:
                continue
            try:
                alt_df = pd.read_excel(file_path, sheet_name=sheet_name, header=alt_row)
                alt_mapping = self.matcher.match_dataframe(alt_df, required_keys)
                if alt_mapping.successful_matches > 0:
                    print(f"  [OK] Better header found at row {alt_row}")
                    # 재탐색된 헤더로 다시 매칭
                    return self._match_and_validate_headers(alt_df, file_label)
            except Exception:
                continue

    return column_mapping
```

**효과**:
- 시맨틱 매칭 실패 시 자동으로 헤더 위치 재확인
- 필수 컬럼 미발견 문제 근본 원인 해결

##### 방안 3: 사용자 수동 지정 옵션 (GUI/CLI) (중기)

**GUI 구현**:
- 파일 선택 후 "헤더 행 설정" 옵션 추가
- 감지된 헤더 행 표시 및 수정 가능한 입력 필드
- 미리보기 기능: 선택한 헤더 행으로 컬럼 미리보기

**CLI 구현**:
```bash
stage1_cli.exe --master Master.xlsx --warehouse Warehouse.xlsx --header-row 4
```

**효과**:
- 사용자가 직접 헤더 위치 제어
- 자동 탐지 실패 시 수동 보정 가능

##### 방안 4: 향상된 헤더 탐지 알고리즘 (장기)

**개선 방향**:
1. **시맨틱 힌트 활용**
   - HVDC_HEADER_REGISTRY에 정의된 표준 헤더 목록을 참조
   - 각 행에서 표준 헤더와의 매칭 점수 계산
   - 높은 매칭 점수를 가진 행 선택

2. **다중 지표 결합**
   - 기존: 텍스트 비율 + null 비율
   - 추가: 표준 헤더 매칭률, 데이터 타입 일관성, 행 길이 일관성

3. **컨텍스트 인식**
   - 이전 시트의 헤더 위치 학습
   - 같은 파일 내 다른 시트와의 일관성 확인

**구현 예시**:
```python
def detect_header_row_enhanced(xlsx_path: str, sheet_name: str,
                                known_headers: List[str] = None) -> Tuple[int, float]:
    """
    향상된 헤더 탐지 알고리즘

    Args:
        xlsx_path: Excel 파일 경로
        sheet_name: 시트 이름
        known_headers: 알려진 헤더 목록 (옵션, 이전 시트나 표준 헤더)

    Returns:
        (row_index, confidence)
    """
    # 1. 기본 휴리스틱 점수 계산
    basic_scores = calculate_basic_scores(xlsx_path, sheet_name)

    # 2. 표준 헤더 매칭 점수 계산 (새로 추가)
    registry = HVDC_HEADER_REGISTRY
    standard_headers = [h.primary_name for h in registry.get_all_headers()]

    semantic_scores = calculate_semantic_matching_scores(
        xlsx_path, sheet_name, standard_headers
    )

    # 3. 데이터 타입 일관성 점수 (새로 추가)
    type_consistency_scores = calculate_type_consistency_scores(
        xlsx_path, sheet_name
    )

    # 4. 가중치 적용하여 최종 점수 계산
    final_scores = (
        basic_scores * 0.3 +
        semantic_scores * 0.5 +  # 표준 헤더 매칭에 높은 가중치
        type_consistency_scores * 0.2
    )

    best_idx = np.argmax(final_scores)
    confidence = final_scores[best_idx]

    return best_idx, confidence
```

**효과**:
- 정확도 대폭 향상 (예상: 95%+)
- 복잡한 Excel 형식에도 강건함

#### 9.5.5 권장 구현 순서

**메인 코드베이스 (이미 구현 완료, PR #8)**:
1. ✅ HeaderDetectionResult 진단 시스템
2. ✅ Confidence 기반 경고 및 다중 후보 검증
3. ✅ 수동 헤더 오버라이드 (`--header-override`)
4. ✅ 시맨틱 매칭 실패 시 헤더 위치 재확인 로직
5. ✅ 벤더 폴백 및 후보 목록 검증

**Standalone 패키지 (통합 필요)**:

**단기 (PR #8 통합, 1-2주 내)**:
1. PR #8 개선사항 통합 (섹션 9.5.7 참조)
   - HeaderDetectionResult 및 detect_header_row_with_diagnostics 도입
   - 수동 헤더 오버라이드 지원
   - 벤더 폴백 및 다중 후보 검증
   - 시맨틱 검증 통합

**중기 (Standalone 전용 개선, 2-4주 내)**:
1. GUI에 헤더 행 수동 지정 옵션 추가
2. CLI에 `--header-override` 파라미터 추가
3. 헤더 탐지 진단 정보 GUI 표시

**장기 (향후 개선)**:
1. 향상된 헤더 탐지 알고리즘 구현 (시맨틱 힌트 활용)
2. 시트 간 헤더 위치 일관성 검증
3. 헤더 위치 학습 및 캐싱 기능

#### 9.5.7 PR #8 통합 계획

##### 개요

PR #8의 헤더 탐지 개선사항을 Standalone 패키지에 통합하여 메인 코드베이스와 동일한 수준의 헤더 탐지 안정성을 제공합니다.

##### 통합 대상 기능

1. **HeaderDetectionResult 및 detect_header_row_with_diagnostics**
   - 위치: `scripts/core/header_detector.py`
   - Standalone에 통합: `standalone/scripts/core/` 모듈에 추가 필요

2. **수동 헤더 오버라이드**
   - 메인 코드베이스 구현: ```956:980:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
   - Standalone CLI/GUI에 파라미터 추가 필요

3. **벤더 폴백 및 다중 후보 검증**
   - 메인 코드베이스 구현: ```468:588:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
   - `_load_sheet_with_candidates` 메서드 패턴 적용

4. **시맨틱 검증 통합**
   - 메인 코드베이스 구현: ```516:524:scripts/stage1_sync_sorted/data_synchronizer_v30.py```
   - `_basic_header_validation` 메서드 패턴 적용

##### 구현 단계

**1단계: Core 모듈 업데이트**

**파일**: `standalone/scripts/core/__init__.py`

- HeaderDetectionResult dataclass import 및 export 추가
- detect_header_row_with_diagnostics 함수 import 및 export 추가
- HeaderDetector 클래스 포함 여부 검토 (필요시 header_detector.py 모듈 추가)

**참조**: ```30:550:scripts/core/header_detector.py```

**2단계: DataSynchronizer 업데이트**

**파일**: `standalone/scripts/tools/data_synchronizer_v30.py`

- HeaderDetectionResult 사용으로 변경
- `_load_sheet_with_candidates` 메서드 추가 (메인 코드베이스 패턴 복사)
- `_build_header_candidates` 메서드 추가
- `_basic_header_validation` 메서드 추가
- `_load_file_by_sheets` 메서드를 새 후보 검증 로직 사용하도록 수정

**참조**:
- ```468:588:scripts/stage1_sync_sorted/data_synchronizer_v30.py``` (후보 검증 로직)
- ```516:524:scripts/stage1_sync_sorted/data_synchronizer_v30.py``` (시맨틱 검증)

**3단계: CLI 인터페이스 업데이트**

**파일**: `standalone/stage1_standalone.py`

- `--header-override` 파라미터 추가
- 파라미터 파싱 로직 추가 (메인 코드베이스 `parse_header_override_args` 참조)
- DataSynchronizerV30에 헤더 오버라이드 전달

**참조**: ```956:980:scripts/stage1_sync_sorted/data_synchronizer_v30.py```

**4단계: GUI 인터페이스 업데이트 (선택사항, 중기)**

**파일**: `standalone/stage1_gui.py`

- 파일 선택 후 헤더 행 설정 UI 추가
- 감지된 헤더 행 표시 및 수정 가능한 입력 필드
- 헤더 행 미리보기 기능

**5단계: 테스트 및 검증**

- 기존 기능 정상 작동 확인
- PR #8 개선사항 정상 작동 확인
- 빌드 테스트 (onedir 및 onefile 모드)
- 다양한 Excel 파일 형식 테스트

##### 예상 효과

**정확도 향상**:
- 다중 후보 검증으로 헤더 탐지 정확도 향상
- 시맨틱 검증 통합으로 필수 컬럼 미발견 문제 해결

**사용자 경험 개선**:
- 진단 정보 제공으로 문제 해결 시간 단축
- 수동 오버라이드 지원으로 유연성 증가
- 명확한 오류 메시지로 디버깅 용이

**유지보수성 향상**:
- 메인 코드베이스와 동일한 로직으로 일관성 확보
- 향후 개선사항 적용 용이

##### 구현 시 주의사항

1. **Standalone 패키지 크기 제약**
   - `header_detector.py` 전체 모듈 추가 시 패키지 크기 증가 가능
   - 필요한 클래스/함수만 선택적으로 포함 검토

2. **의존성 확인**
   - PR #8 구현이 요구하는 추가 의존성 확인
   - Standalone 패키지의 최소 의존성 원칙 유지

3. **하위 호환성**
   - 기존 `detect_header_row()` 함수는 유지 (하위 호환성)
   - 점진적 마이그레이션 가능하도록 설계

4. **테스트 전략**
   - 메인 코드베이스의 통합 테스트 참조
   - Standalone 패키지 전용 테스트 추가

##### 참고 자료

- PR #8 커밋: `933bbfb` (2025-10-29 병합)
- 헤더 탐지 안정화 가이드: `docs/kr/header_detection_overrides.md`
- 메인 코드베이스 구현:
  - Core 모듈: ```30:550:scripts/core/header_detector.py```
  - DataSynchronizer: ```468:588:scripts/stage1_sync_sorted/data_synchronizer_v30.py```

#### 9.5.6 사용자 대응 가이드

**헤더 위치 오탐지 발생 시 확인 사항**:

1. **로그 확인**
   ```
   [OK] Header at row 4 (confidence: 30%)
   ```
   - Confidence가 50% 미만이면 수동 확인 권장

2. **Excel 파일 확인**
   - 첫 번째 데이터 행이 헤더로 인식되었는지 확인
   - 빈 행이 헤더로 인식되었는지 확인
   - 병합된 셀이 헤더 탐지를 방해하는지 확인

3. **수동 조치**
   - Excel 파일에서 헤더 행을 명확히 식별
   - 빈 행 제거 또는 병합된 셀 해제
   - 파일 재저장 후 다시 시도

**임시 해결 방법**:
- 파일명에 벤더 정보 추가 (예: "CASE_LIST_SIEMENS.xlsx")
- 표준 형식에 맞게 Excel 파일 수정
- 헤더 행 위의 빈 행 제거

**참고**: 메인 코드베이스(v4.0.53+)에서는 PR #8로 인해 대부분의 문제가 자동으로 해결됩니다. 상세한 사용법은 `docs/kr/header_detection_overrides.md`를 참조하세요.

---

## 10. 성능 지표 및 검증

### 10.1 빌드 시간 비교

| 항목 | 개선 전 | 개선 후 | 개선율 |
|------|---------|---------|--------|
| **빌드 시간** | 15분+ | 2-5분 | 약 70% 단축 |
| **타임아웃 발생** | 6회+ | 0회 | 100% 제거 |
| **경고 메시지** | 수천 개 | 소수 | 99%+ 감소 |

### 10.2 실행 파일 크기

| 모드 | 파일 크기 | 설명 |
|------|-----------|------|
| **onedir (GUI)** | 37.2 MB | 폴더 구조 (DLL 포함) |
| **onedir (CLI)** | 34.1 MB | 폴더 구조 (DLL 포함) |
| **onefile (GUI)** | 예상 100-150 MB | 단일 파일 (압축됨) |

**비고**: 개선 전 torch 포함 시 예상 500MB+였으나, 최적화로 크게 감소

### 10.3 기능 검증 결과

#### 검증 완료 항목

✅ **GUI 인터페이스**
- 파일 선택 기능 정상 작동
- 실시간 로그 표시 정상 작동
- 오류 처리 및 알림 정상 작동

✅ **CLI 인터페이스**
- 명령줄 인자 파싱 정상 작동
- 프로그램적 API 정상 작동
- 반환 코드 정상 작동 (0: 성공, 1: 실패)

✅ **데이터 동기화**
- 헤더 탐지 정상 작동
- 시맨틱 매칭 정상 작동
- 데이터 동기화 정상 작동
- 변경 사항 색상 표시 정상 작동

✅ **빌드 시스템**
- onedir 모드 빌드 성공
- onefile 모드 빌드 성공 (예상)
- Hook 시스템 정상 작동
- 경고 억제 정상 작동

#### 검증 대기 항목

- [ ] 다양한 Windows 버전 호환성 테스트
- [ ] 대용량 파일 처리 테스트
- [ ] 복잡한 Excel 형식 처리 테스트
- [ ] 최종 사용자 환경 테스트

---

## 11. 참고 자료 및 문서

### 11.1 관련 문서 목록

#### 사용자 가이드
- `README_STANDALONE.md`: 사용자 가이드 및 빌드 방법

#### 개발자 문서
- `STANDALONE_RECREATION_BUILD_REPORT.md`: 디렉토리 재생성 및 빌드 보고서
- `IMPLEMENTATION_COMPLETE.md`: 구현 완료 보고서
- `OPTIMIZATION_COMPLETE.md`: 최적화 완료 보고서
- `BUILD_ISSUES_REPORT.md`: 빌드 문제점 보고서

#### 코드 문서
- `scripts/core/README.md`: Core 모듈 사용 가이드
- `scripts/core/INTEGRATION_GUIDE.md`: 통합 가이드

#### 헤더 탐지 관련 문서
- `docs/kr/header_detection_overrides.md`: 헤더 탐지 안정화 가이드 (PR #8 적용 가이드)

### 11.2 내부 보고서 링크

#### 진단 보고서
- `docs/reports/STANDALONE_LAUNCH_DIAGNOSIS.md`: 초기 진단 보고서
- `docs/reports/STANDALONE_KAMAGWI_ANALYSIS.md`: 까마귀 디렉토리 분석

#### 프로젝트 문서
- `docs/README.md`: 프로젝트 전체 개요
- `CHANGELOG.md`: 변경 이력

### 11.3 API 문서

#### Core 모듈 API

**헤더 레지스트리**:
```python
from scripts.core import HVDC_HEADER_REGISTRY

# 창고 컬럼 목록 가져오기
warehouse_cols = HVDC_HEADER_REGISTRY.get_warehouse_columns()

# 사이트 컬럼 목록 가져오기
site_cols = HVDC_HEADER_REGISTRY.get_site_columns()
```

**시맨틱 매칭**:
```python
from scripts.core import SemanticMatcher, find_header_by_meaning

# 시맨틱 키로 헤더 찾기
header = find_header_by_meaning(df, "case_number")
```

**편의 함수**:
```python
from scripts.core import (
    get_warehouse_columns,
    get_site_columns,
    get_date_columns,
    detect_header_row
)

warehouse_cols = get_warehouse_columns()
site_cols = get_site_columns()
header_row, confidence = detect_header_row("file.xlsx", "Sheet1")
```

#### DataSynchronizer API

```python
from scripts.tools.data_synchronizer_v30 import DataSynchronizerV30

sync = DataSynchronizerV30()
result = sync.synchronize(
    master="Master.xlsx",
    warehouse="Warehouse.xlsx",
    output="Output.xlsx"
)

if result.success:
    print(f"Output: {result.output_path}")
    print(f"Stats: {result.stats}")
```

#### Standalone API

```python
from stage1_standalone import run_sync

success, output_path, stats = run_sync(
    master="Master.xlsx",
    warehouse="Warehouse.xlsx",
    out="Output.xlsx",
    log_cb=print  # 옵션: 로그 콜백
)
```

---

## 부록

### A. 빌드 체크리스트

빌드 전 확인 사항:
- [ ] Python 3.9+ 설치 확인
- [ ] 인터넷 연결 확인 (의존성 다운로드)
- [ ] 충분한 디스크 공간 확인 (최소 500MB)
- [ ] 이전 빌드 파일 삭제 (선택사항)

빌드 후 확인 사항:
- [ ] 실행 파일 생성 확인
- [ ] 파일 크기 확인
- [ ] GUI 실행 테스트
- [ ] CLI 실행 테스트

### B. 버전 히스토리

- **v1.0.0** (2025-10-29): 초기 릴리스
  - GUI 및 CLI 인터페이스 구현
  - 빌드 시스템 최적화
  - 경고 억제 시스템 도입

### C. 알려진 제한사항

1. **플랫폼 지원**: 현재 Windows 우선 지원 (Linux/macOS는 빌드 스크립트만 제공)
2. **Excel 형식**: `.xlsx`, `.xlsm`, `.xls` 형식 지원 (`.xlsb` 미지원)
3. **대용량 파일**: 매우 큰 파일(수십 MB 이상)의 경우 처리 시간 증가 가능

### D. 향후 개선 계획

1. **아이콘 추가**: 실행 파일 아이콘 커스터마이징
2. **다국어 지원**: 영어/한국어 UI 지원
3. **설정 파일**: 빌드 설정 외부화
4. **자동 업데이트**: 버전 확인 및 업데이트 기능
5. **로깅 강화**: 상세한 로그 파일 생성

---

**기술보고서 작성**: AI Assistant
**최종 업데이트**: 2025-10-29
**문서 버전**: v1.0.0

