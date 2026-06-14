# Stage 1 Standalone 빌드 문제점 보고서

**작성 일자**: 2025-10-29  
**빌드 시도**: PyInstaller 6.16.0  
**상태**: ⚠️ 빌드 중단됨

---

## 🔴 발견된 주요 문제점

### 1. 빌드 중단
- **증상**: 사용자가 빌드 과정 중 중단 ("Aborted by user request")
- **원인**: 빌드 시간이 너무 오래 걸림 (약 15분 이상 소요)
- **영향**: 최종 .exe 파일이 생성되지 않음

### 2. 불필요한 의존성 포함
**문제**: PyInstaller가 Stage 1에서 필요하지 않은 대형 패키지들을 자동으로 포함하고 있음

**포함된 불필요한 패키지**:
- `torch` (PyTorch) - 약 1GB+, Stage 1에서 불필요
- `matplotlib` - 시각화 라이브러리, Stage 1에서 불필요
- `scipy` - 과학 계산 라이브러리, Stage 1에서 불필요
- `pytest` - 테스트 프레임워크, 빌드에 불필요

**로그 증거**:
```
635206 INFO: Processing standard module hook 'hook-torch.py'
830377 INFO: Processing standard module hook 'hook-matplotlib.py'
300764 INFO: Processing standard module hook 'hook-scipy.py'
301782 INFO: Processing standard module hook 'hook-pytest.py'
```

### 3. 타임아웃 경고 다수 발생
**증상**: 
```
WARNING: Timed out while waiting for the child process to exit!
```

**발생 빈도**: 최소 6회 이상  
**원인**: 불필요한 대형 패키지 분석 중 시간 초과  
**영향**: 빌드 시간 증가 및 불안정성

### 4. 가상환경 활성화 실패
**증상**:
```
'.venv\Scripts\activate'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는
배치 파일이 아닙니다.
```

**원인**: 
- PowerShell에서 `.bat` 파일 실행 시 가상환경 활성화 스크립트 경로 문제
- `.venv` 폴더가 생성되지 않았거나 경로 불일치

**조치 완료**: pathlib 패키지 제거 완료

### 5. 경고 메시지
**경고 목록**:
- `pandas.core._numba.kernels`: numba 모듈 없음 (정상, 선택적 의존성)
- `rapidfuzz.__pyinstaller`: hook-dirs 속성 없음
- `torch.utils.tensorboard`: tensorboard 모듈 없음

**심각도**: 낮음 (기능에 영향 없음)

---

## 📊 빌드 진행 상황 분석

### 완료된 단계
- ✅ PyInstaller 초기화
- ✅ Python 환경 확인
- ✅ 모듈 의존성 그래프 분석 시작
- ✅ 기본 라이브러리 처리
- ✅ pandas, numpy, openpyxl hook 처리
- ⚠️ 대형 패키지 분석 중 (torch, matplotlib 등)

### 미완료 단계
- ❌ 최종 바이너리 생성
- ❌ .exe 파일 패키징
- ❌ dist 폴더 생성

---

## 🔧 해결 방안

### 즉시 조치 사항

#### 1. 불필요한 패키지 제외 (build_exe.spec)
**수정 내용**:
```python
excludes = [
    'torch',
    'matplotlib', 
    'scipy',
    'pytest',
    'IPython',
    'jupyter',
    'notebook',
    'tensorboard',
    'numba',
]
```

#### 2. 가상환경 스크립트 개선 (build.bat)
**문제**: PowerShell에서 `.venv\Scripts\activate` 실행 실패

**해결책 1**: 가상환경 사용하지 않고 시스템 Python 사용
```bat
REM 가상환경 생략, 시스템 Python 직접 사용
python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller
```

**해결책 2**: PowerShell 호환 스크립트 생성 (build.ps1)

#### 3. 빌드 최적화
- `collect_submodules` 제한: 필요한 pandas/numpy/openpyxl만
- `--exclude-module` 옵션 추가
- `--onefile` vs `--onedir` 선택 (현재: COLLECT 사용)

---

## 🎯 권장 수정 사항

### Priority 1: 필수 수정 (빌드 성공을 위해)

1. **build_exe.spec - excludes 추가**
   ```python
   excludes = [
       'torch', 'torchvision', 'torchaudio',
       'matplotlib', 'scipy', 'pytest',
       'IPython', 'jupyter', 'notebook',
       'tensorboard', 'numba',
   ]
   ```

2. **build.bat - 가상환경 문제 해결**
   - 방법 A: 가상환경 사용 안 함 (시스템 Python 직접 사용)
   - 방법 B: PowerShell 스크립트로 변경 (`build.ps1`)

### Priority 2: 최적화 (빌드 시간 단축)

3. **collect_submodules 제한**
   ```python
   # pandas의 모든 submodule이 아닌 필요한 것만
   hiddenimports = [
       'pandas.io.excel._openpyxl',
       'pandas.io.parsers.readers',
       # ... 필요한 것만 명시
   ]
   ```

4. **빌드 옵션 최적화**
   - `upx=True` → `upx=False` (UPX 압축 시간 소요)
   - `strip=False` → `strip=True` (디버그 정보 제거)

---

## 📝 현재 빌드 설정 분석

### build_exe.spec 현재 설정
- ✅ GUI exe 생성 (`console=False`)
- ✅ CLI exe 생성 (`console=True`)
- ✅ datas에 scripts/core/* 포함
- ✅ hiddenimports에 pandas/numpy/openpyxl submodules
- ⚠️ excludes 없음 (불필요한 패키지 제외 안 함)

### 예상 빌드 시간
- **현재**: 15분+ (torch 등 포함 시)
- **최적화 후**: 2-5분 (필수 패키지만 포함 시)

---

## 🧪 테스트 권장 사항

빌드 완료 후:
1. **GUI exe 실행 테스트**: 더블클릭으로 GUI 정상 작동 확인
2. **CLI exe 실행 테스트**: 실제 Master/Warehouse 파일로 동기화 테스트
3. **의존성 확인**: 다른 PC에서 Python 없이 실행 가능한지 확인

---

## 📋 다음 단계

1. ⚠️ **build_exe.spec 수정** (excludes 추가) - 필수
2. ⚠️ **build.bat 개선** (가상환경 문제 해결) - 필수
3. ⚡ **빌드 재시도** (최적화된 설정으로)
4. ✅ **생성된 .exe 파일 테스트**

---

**다음 조치**: build_exe.spec에 excludes 추가 및 build.bat 개선 후 재빌드 권장


