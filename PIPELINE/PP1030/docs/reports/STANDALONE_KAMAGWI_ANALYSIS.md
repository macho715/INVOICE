# README_STANDALONE.md, standalone, 까마귀 관계 분석 보고서

**분석 일자**: 2025-01-27
**상태**: 분석 완료

---

## 요약

**핵심 발견**:
- `standalone/`와 `까마귀/` 디렉토리는 모두 코드베이스에 인덱싱되어 있으나, **실제 파일 시스템에 존재하지 않음**
- 두 디렉토리는 **빌드 스크립트 방식에 차이**가 있음
- README_STANDALONE.md는 standalone 디렉토리를 참조하지만, 실제로는 까마귀에도 유사한 파일 구조가 있음

---

## 상세 분석

### 1. 디렉토리 상태

#### standalone 디렉토리
- **인덱싱 상태**: ✅ Cursor에 인덱싱됨
- **실제 파일 시스템**: ❌ 존재하지 않음
- **git 상태**: ❌ HEAD에 없음

#### 까마귀 디렉토리
- **인덱싱 상태**: ✅ Cursor에 인덱싱됨
- **실제 파일 시스템**: ❌ 존재하지 않음
- **git 상태**: ❌ HEAD에 없음

### 2. 파일 구조 비교

#### standalone 디렉토리 파일 목록 (인덱싱 기준)
```
standalone/
├── README_STANDALONE.md
├── IMPLEMENTATION_COMPLETE.md
├── OPTIMIZATION_COMPLETE.md
├── stage1_gui.py (참조만, 실제 파일 없음)
├── stage1_standalone.py (참조만, 실제 파일 없음)
├── build.bat
├── build.ps1
├── build.sh
├── build_exe_optimized_onedir.spec
├── build_gui_onefile.spec
├── build_exe_old.spec
└── scripts/ (하위 구조 언급됨)
```

#### 까마귀 디렉토리 파일 목록 (인덱싱 기준)
```
까마귀/
├── README_STANDALONE.md (간단한 버전)
├── build.bat
├── build.ps1
├── build_exe_optimized_onedir.spec
└── build_gui_onefile.spec
```

### 3. 빌드 스크립트 차이점 분석

#### standalone/build.bat
```bat
# Spec 파일 사용 방식
pyinstaller %EXC% build_exe_optimized_onedir.spec
# EXC = --clean --noconfirm만 포함
# excludes는 spec 파일 내부에 정의
```

#### 까마귀/build.bat
```bat
# CLI 옵션 사용 방식
set EXC= --clean --noconfirm ^
 --exclude-module torch --exclude-module torchvision ...
pyinstaller %EXC% build_exe_optimized_onedir.spec
# excludes를 CLI 옵션으로 직접 지정
```

#### 차이점 요약

| 항목 | standalone | 까마귀 |
|------|-----------|--------|
| Exclude 방식 | Spec 파일 내부 | CLI 옵션 |
| Spec 파일 의존성 | 높음 (excludes는 spec에만) | 낮음 (CLI 옵션 우선) |
| 유지보수성 | Spec 파일 수정 필요 | CLI 옵션으로 빠른 수정 |
| 일관성 | 모든 excludes가 spec에 집중 | 분산되어 있음 |

### 4. Spec 파일 비교

#### 공통점
- 둘 다 `build_exe_optimized_onedir.spec` 사용
- 둘 다 `build_gui_onefile.spec` 사용
- 동일한 `datas` 섹션 구조 (`('scripts/core/__init__.py', 'scripts/core')`)

#### 차이점
- **standalone**: Spec 파일에 excludes 리스트 포함
- **까마귀**: Spec 파일 + CLI 옵션으로 이중 exclude (중복 가능성)

### 5. README_STANDALONE.md 분석

#### standalone/README_STANDALONE.md
- ✅ 상세한 빌드 가이드 포함
- ✅ onedir/onefile 모드 설명
- ✅ Features 섹션 포함
- ✅ 빌드 최적화 설명
- ❌ 경로: `cd standalone` (실제 경로는 `scripts/stage1_Standalone/standalone`)

#### 까마귀/README_STANDALONE.md
- ⚠️ 간단한 버전 (13줄만)
- ❌ 상세 가이드 없음

---

## 발견된 문제점

### 문제 1: 파일 존재하지 않음 (치명적)
- 두 디렉토리 모두 실제 파일 시스템에 없음
- 빌드/실행 불가능

### 문제 2: 디렉토리명 불일치
- README는 standalone을 참조하지만 까마귀도 존재
- 사용자 혼란 가능

### 문제 3: 빌드 방식 차이
- standalone: Spec 파일 기반 (일관성 높음)
- 까마귀: CLI 옵션 기반 (유연성 높음)
- 표준화 필요

### 문제 4: 경로 명시 부족
- README: `cd standalone`만 표기
- 실제: `cd scripts/stage1_Standalone/standalone`
- 명확한 경로 표시 필요

---

## 해결 방안

### 옵션 1: Git에서 파일 복구 (권장)
```bash
# 모든 브랜치에서 파일 검색
git log --all --full-history --oneline -- "scripts/stage1_Standalone"

# 특정 커밋에서 복구
git checkout <commit-hash> -- scripts/stage1_Standalone/standalone
# 또는
git checkout <commit-hash> -- scripts/stage1_Standalone/까마귀
```

### 옵션 2: 디렉토리 통합 및 정리
1. **까마귀를 standalone으로 통합**
   - 까마귀의 내용을 standalone으로 이동
   - 까마귀 삭제 또는 아카이브

2. **빌드 방식 표준화**
   - Spec 파일 기반 방식 채택 (standalone 방식)
   - CLI 옵션은 최소화

3. **README 업데이트**
   - 전체 경로 명시: `cd scripts/stage1_Standalone/standalone`
   - 디렉토리 구조 명확화

### 옵션 3: 새로운 독립 디렉토리 생성
- 현재 인덱싱된 파일 내용을 기반으로 새로운 standalone 디렉토리 생성
- 까마귀는 백업으로 보존
- README를 실제 파일 구조에 맞게 업데이트

---

## 권장 해결 순서

1. ✅ **즉시**: Git 히스토리 상세 조사로 파일 최종 위치 확인
2. ⚠️ **빠른 조치**: 파일이 있다면 복구, 없다면 재생성
3. 📝 **표준화**: 까마귀와 standalone 중 하나로 통합
4. 🔧 **문서 개선**: README_STANDALONE.md에 전체 경로 추가
5. ✅ **검증**: 빌드 스크립트 실제 테스트

---

## 다음 단계

### 즉시 실행 가능한 작업
1. Git 모든 브랜치에서 standalone 관련 파일 검색
2. 발견된 파일을 현재 브랜치로 체크아웃
3. README_STANDALONE.md 경로 수정

### 장기 개선 작업
1. 디렉토리명 표준화 (까마귀 → standalone 또는 반대)
2. 빌드 방식 통일 (Spec 파일 기반 권장)
3. 빌드 스크립트 테스트 자동화
4. CI/CD 파이프라인에 빌드 테스트 추가

---

## 결론

**현재 상황**:
- standalone과 까마귀는 **코드베이스 인덱싱에는 있으나 실제 파일은 없음**
- 두 디렉토리는 **빌드 방식에 차이**가 있음
- README는 standalone을 참조하지만 **실제 경로가 불명확**

**권장 조치**:
1. Git에서 파일 복구 또는 재생성
2. 까마귀를 standalone으로 통합 (빌드 방식은 Spec 파일 기반 채택)
3. README에 전체 경로 명시
4. 빌드 테스트 및 검증

**우선순위**: P0 (Critical) - 파일 부재로 인해 현재 빌드 불가능

