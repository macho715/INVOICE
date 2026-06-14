# Excel 색상 검증 스크립트 마이그레이션 가이드

## 📌 개요

이 문서는 기존 7개 스크립트에서 통합 스크립트로 전환하는 방법을 안내합니다.

---

## 🔄 빠른 전환 표

### 기본 명령어 변환

| 기존 명령어 | 통합 명령어 |
|------------|------------|
| `python verify_excel_colors_optimized.py` | `python verify_excel_colors_unified.py --mode=basic` |
| `python verify_excel_colors_ultra_fast.py` | `python verify_excel_colors_unified.py --mode=ultra_fast` |
| `python verify_excel_colors_fast_batch.py` | `python verify_excel_colors_unified.py --mode=batch` |
| `python verify_excel_colors.py` | `python verify_excel_colors_unified.py --mode=full` |
| `python verify_excel_colors_enhanced.py --prefer-change-log` | `python verify_excel_colors_unified.py --mode=change_log --change-log=<path>` |

---

## 📝 상세 마이그레이션

### 1. verify_excel_colors_optimized.py → unified (basic)

**기존:**
```bash
python verify_excel_colors_optimized.py \
  --rows=200 \
  --cols=12 \
  --sheets=2 \
  --samples=5 \
  --processes=4
```

**통합:**
```bash
python verify_excel_colors_unified.py \
  --mode=basic \
  --rows=200 \
  --cols=12 \
  --sheets=2 \
  --samples=5 \
  --processes=4
```

**변경사항:**
- ✅ 모든 옵션 동일하게 작동
- ✅ `--mode=basic` 추가 (기본값이므로 생략 가능)
- ✅ 성능 동일

---

### 2. verify_excel_colors_ultra_fast.py → unified (ultra_fast)

**기존:**
```bash
python verify_excel_colors_ultra_fast.py
```

**통합:**
```bash
python verify_excel_colors_unified.py --mode=ultra_fast
```

**변경사항:**
- ✅ 동일한 샘플링 로직 (50행, 8컬럼)
- ✅ 속도 동일
- ✅ `--sheets` 옵션 추가 가능

---

### 3. verify_excel_colors_fast_batch.py → unified (batch)

**기존:**
```bash
python verify_excel_colors_fast_batch.py
```

**통합:**
```bash
python verify_excel_colors_unified.py --mode=batch
```

**변경사항:**
- ✅ 동일한 배치 구성 (5개 배치)
- ✅ 직접 실행 (subprocess 대신)
- ⚠️ 배치 설정은 스크립트 내부에 하드코딩 (향후 `--batch-config` 지원 예정)

---

### 4. verify_excel_colors.py → unified (full)

**기존:**
```bash
python verify_excel_colors.py
```

**통합:**
```bash
python verify_excel_colors_unified.py --mode=full
```

**변경사항:**
- ✅ 전체 행 스캔
- ✅ `--full-scan` 자동 활성화
- ✅ 모든 기능 유지

---

### 5. verify_excel_colors_enhanced.py → unified (basic + options)

**기존:**
```bash
python verify_excel_colors_enhanced.py \
  --tail-rows=100 \
  --random-sample=50 \
  --date-cols-only \
  --date-cols="IN Date,OUT Date"
```

**통합:**
```bash
python verify_excel_colors_unified.py \
  --mode=basic \
  --tail-rows=100 \
  --random-sample=50 \
  --date-cols-only \
  --date-cols="IN Date,OUT Date"
```

**변경사항:**
- ✅ 모든 확장 옵션 유지
- ✅ `--mode=basic` 추가

---

### 6. ChangeTracker 로그 사용

**기존:**
```bash
python verify_excel_colors_enhanced.py \
  --change-log=logs/changes.json \
  --prefer-change-log
```

**통합:**
```bash
python verify_excel_colors_unified.py \
  --mode=change_log \
  --change-log=logs/changes.json
```

**변경사항:**
- ✅ 전용 모드로 분리
- ✅ `--prefer-change-log` 불필요 (모드가 이미 우선 처리)
- ✅ JSON/CSV 형식 모두 지원

---

## 🔧 옵션 매핑 표

### 공통 옵션 (모든 모드)

| 기존 옵션 | 통합 옵션 | 설명 |
|---------|---------|------|
| `--stage1` | `--stage1` | Stage1 파일 경로 |
| `--report` | `--report` | 결과 JSON 경로 |
| `--sheets` | `--sheets` | 스캔할 시트 수 |
| `--samples` | `--samples` | 케이스 샘플 수 |
| `--processes` | `--processes` | 병렬 프로세스 수 |
| `--no-parallel` | `--no-parallel` | 병렬 처리 비활성화 |

### 스캔 옵션

| 기존 옵션 | 통합 옵션 | 지원 모드 |
|---------|---------|----------|
| `--rows` | `--rows` | basic, full |
| `--cols` | `--cols` | basic, full |
| `--header-rows` | `--header-rows` | basic, full |
| `--max-cells` | `--max-cells` | basic, full |

### 확장 옵션

| 기존 옵션 | 통합 옵션 | 지원 모드 |
|---------|---------|----------|
| `--tail-rows` | `--tail-rows` | basic, full |
| `--random-sample` | `--random-sample` | basic, full |
| `--random-seed` | `--random-seed` | basic, full |
| `--date-cols-only` | `--date-cols-only` | basic, full |
| `--date-cols` | `--date-cols` | basic, full |
| `--full-scan` | `--full-scan` | basic, full |

### ChangeTracker 옵션

| 기존 옵션 | 통합 옵션 | 지원 모드 |
|---------|---------|----------|
| `--change-log` | `--change-log` | change_log, basic (선택) |
| `--prefer-change-log` | (제거) | change_log 모드로 대체 |

---

## 📊 성능 비교

### 처리 시간 (2-3 시트 기준)

| 모드 | 기존 스크립트 | 통합 스크립트 | 비고 |
|------|------------|------------|------|
| basic | ~15초 | ~15초 | 동일 |
| ultra_fast | ~3초 | ~3초 | 동일 |
| batch | ~45초 | ~45초 | 동일 |
| full | ~10분 | ~10분 | 동일 |
| change_log | ~0.5초 | ~0.5초 | 동일 |

---

## 🚀 마이그레이션 단계

### Step 1: 백업

```bash
# 기존 스크립트 백업 (자동)
python cleanup_old_scripts.py
```

또는 수동:

```bash
mkdir -p archive/verify_colors_archive
mv verify_excel_colors*.py archive/verify_colors_archive/
# 단, verify_excel_colors_unified.py는 제외
```

---

### Step 2: 테스트

```bash
# 1. 빠른 테스트 (ultra_fast)
python verify_excel_colors_unified.py --mode=ultra_fast

# 2. 기본 테스트 (basic)
python verify_excel_colors_unified.py --mode=basic --sheets=1

# 3. 전체 테스트 (full) - 선택적
python verify_excel_colors_unified.py --mode=full --sheets=1
```

---

### Step 3: 스크립트/자동화 업데이트

**예시: Bash 스크립트**

**기존:**
```bash
#!/bin/bash
python verify_excel_colors_optimized.py --rows=200 --cols=12
```

**업데이트:**
```bash
#!/bin/bash
python verify_excel_colors_unified.py --mode=basic --rows=200 --cols=12
```

**예시: Python 스크립트**

**기존:**
```python
import subprocess

subprocess.run([
    "python", "verify_excel_colors_optimized.py",
    "--rows", "200",
    "--cols", "12"
])
```

**업데이트:**
```python
import subprocess

subprocess.run([
    "python", "verify_excel_colors_unified.py",
    "--mode", "basic",
    "--rows", "200",
    "--cols", "12"
])
```

---

### Step 4: CI/CD 파이프라인 업데이트

**예시: GitHub Actions**

**기존:**
```yaml
- name: Verify Excel Colors
  run: python verify_excel_colors_optimized.py --rows=200
```

**업데이트:**
```yaml
- name: Verify Excel Colors
  run: python verify_excel_colors_unified.py --mode=basic --rows=200
```

---

## ⚠️ 주의사항

### 1. 배치 설정 커스터마이징

**기존:**
`verify_excel_colors_fast_batch.py`에서 배치 설정 직접 수정

**통합:**
현재는 스크립트 내부 하드코딩. 향후 `--batch-config` JSON 파일 지원 예정.

**임시 해결책:**
배치 설정 변경 시 `verify_excel_colors_unified.py`의 `run_batch_mode()` 함수 수정

---

### 2. 옵션 이름 변경

일부 옵션 이름이 약간 변경되었습니다:

| 기존 | 통합 |
|------|------|
| `--prefer-change-log` | (제거, `--mode=change_log` 사용) |

---

### 3. 기본값 차이

대부분 동일하지만, 일부 기본값 확인:

| 옵션 | 기본값 |
|------|--------|
| `--mode` | `basic` |
| `--rows` | 200 |
| `--cols` | 12 |
| `--sheets` | 2 |
| `--samples` | 5 |
| `--max-cells` | 2000 |

---

## 🔍 호환성 체크리스트

### 필수 확인 사항

- [ ] Python 3.8+ 설치 확인
- [ ] 필수 패키지 설치 (`openpyxl`, `pandas`)
- [ ] Stage1 파일 경로 확인
- [ ] 출력 디렉토리 쓰기 권한 확인

### 기능 확인

- [ ] 기본 스캔 테스트 (basic)
- [ ] 초고속 스캔 테스트 (ultra_fast)
- [ ] 병렬 처리 테스트
- [ ] 결과 JSON 파싱 확인

---

## 📋 마이그레이션 체크리스트

### 준비 단계
- [ ] 기존 스크립트 백업 완료
- [ ] 통합 스크립트 다운로드/복사
- [ ] 의존성 패키지 확인

### 테스트 단계
- [ ] ultra_fast 모드 테스트
- [ ] basic 모드 테스트
- [ ] 기존 스크립트와 결과 비교

### 업데이트 단계
- [ ] Bash/Python 스크립트 업데이트
- [ ] CI/CD 파이프라인 업데이트
- [ ] 문서 업데이트

### 정리 단계
- [ ] 기존 스크립트 아카이브 이동
- [ ] README 업데이트
- [ ] 팀원 공지

---

## 🐛 문제 해결

### 문제: 명령어가 작동하지 않음

**증상:**
```
python verify_excel_colors_unified.py
NameError: name 'xxx' is not defined
```

**해결:**
```bash
# 파이썬 버전 확인
python --version  # Python 3.8+ 필요

# 패키지 재설치
pip install -r requirements.txt --upgrade
```

---

### 문제: 결과가 기존 스크립트와 다름

**증상:** ORANGE/YELLOW 개수가 다름

**해결:**
1. 모드 확인: `--mode=basic` vs `--mode=full`
2. 샘플링 옵션 확인: `--rows`, `--cols`
3. 전체 스캔으로 재확인: `--mode=full`

---

### 문제: 배치 모드가 다르게 작동

**증상:** 배치 결과가 예전과 다름

**해결:**
배치 설정이 통합 스크립트에 하드코딩되어 있으므로, 필요 시 스크립트 직접 수정:
```python
# verify_excel_colors_unified.py 의 run_batch_mode() 함수
batches = [
    {"name": "상단", "rows": 200, ...},
    # 여기에 배치 추가/수정
]
```

---

## 📚 추가 리소스

- [통합 스크립트 README](README_UNIFIED.md)
- [Excel 색상 검증 원리](docs/COLOR_DETECTION.md)
- [HVDC 프로젝트 문서](docs/HVDC_PROJECT.md)

---

## 💡 팁

1. **테스트는 점진적으로**: ultra_fast → basic → full 순서로 테스트
2. **병렬 처리 주의**: 초기엔 `--no-parallel`로 문제 격리
3. **로그 활용**: `--mode=change_log`가 가장 빠름
4. **자동화 우선**: CI/CD에서 basic 모드 사용

---

## 📞 문의

**이슈 발생 시:**
1. 에러 메시지 캡처
2. 사용한 명령어 공유
3. 기존 스크립트와 결과 차이 비교

**프로젝트:** HVDC WAREHOUSE_HITACHI(HE)  
**담당:** Samsung C&T Logistics - ADNOC·DSV Partnership
