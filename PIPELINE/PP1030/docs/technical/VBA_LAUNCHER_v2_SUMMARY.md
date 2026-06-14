# VBA 런처 v2.0 완전 교체 패치 요약

**작성일**: 2025-12-21  
**버전**: v2.0  
**기반**: p2.md 설계 문서  
**상태**: ✅ 완료

---

## 개요

p2.md 설계를 기반으로 기존 `modPipelineLauncher.bas`를 완전 교체한 고급 VBA 런처를 구현했습니다.

## 생성된 파일

### 1. `vba/modPipelineControl.bas` (신규)
- **p2.md 기반 완전 구현**
- 이름 정의(Name) 사용
- 템플릿 자동 생성
- raw 파일 복사/백업
- 출력 경로 자동 업데이트
- 실행 시간 표시
- 9개 버튼 지원

### 2. `vba/MIGRATION_GUIDE.md` (신규)
- 기존 모듈에서 새 모듈로 마이그레이션 가이드
- 단계별 전환 방법
- 호환성 정보

### 3. `vba/README_v2.md` (신규)
- v2.0 사용 가이드
- 빠른 시작 가이드
- 기능 설명

### 4. `docs/technical/VBA_LAUNCHER_v2_SUMMARY.md` (이 문서)
- 완전 교체 패치 요약

## 주요 변경사항

### 실행 방식 통합

**p2.md 원본**:
```vb
Private Const REL_STAGE1_SCRIPT As String = "scripts\stage1_sync_sorted\data_synchronizer_v30.py"
```

**수정안 (실제 파이프라인 구조 반영)**:
```vb
Private Const REL_STAGE1_SCRIPT As String = "run\run_pipeline.py --stage 1"
Private Const REL_STAGE2_SCRIPT As String = "run\run_pipeline.py --stage 2"
Private Const REL_STAGE3_SCRIPT As String = "run\run_pipeline.py --stage 3"
Private Const REL_STAGE4_SCRIPT As String = "run\run_pipeline.py --stage 4"
```

### BuildCmd 함수 수정

**p2.md 원본**: `--config` 옵션 사용 가정

**수정안**: `run_pipeline.py`는 설정 파일을 자동 로드하므로 `--config` 옵션 제거

```vb
' run_pipeline.py는 설정 파일을 자동 로드하므로 --config 옵션 불필요
' scriptRel은 "run\run_pipeline.py --stage X" 형식으로 전체를 Q()로 감싸야 함
inner = "cd /d " & Q(root) & " && " & QuoteExe(pyExe) & " " & Q(scriptRel)
```

### StageConfigPath 함수 단순화

**p2.md 원본**: Config 경로를 `--config` 옵션으로 전달

**수정안**: Config 경로는 참고용으로만 사용, 실제 실행에는 불필요

```vb
Private Function GetStageArgs(ByVal stageId As String) As String
    ' run_pipeline.py는 설정 파일을 자동 로드하므로 --config 옵션 불필요
    ' 추가 옵션만 반환 (예: --stage4-visualize)
    GetStageArgs = vbNullString
End Function
```

## 기능 비교

| 기능 | v1.0 (modPipelineLauncher) | v2.0 (modPipelineControl) |
|------|----------------------------|---------------------------|
| 템플릿 자동 생성 | ❌ | ✅ |
| 이름 정의(Name) | ❌ | ✅ |
| Stage 표 | ❌ | ✅ |
| raw 파일 복사/백업 | ❌ | ✅ |
| 출력 경로 자동 업데이트 | ❌ | ✅ |
| 실행 시간 표시 | ❌ | ✅ |
| 최신 결과 열기 | ❌ | ✅ |
| 로그 폴더 열기 | ❌ | ✅ |
| LOG 시트 클리어 | ❌ | ✅ |
| 버튼 개수 | 5개 | 9개 |
| 실행 방식 | `run_pipeline.py --stage X` | `run_pipeline.py --stage X` |

## CONTROL 시트 레이아웃

### v1.0 (기존)
- 간단한 A열/B열 구조
- 셀 주소 직접 참조 (B2, B3, ...)
- 수동 시트 생성

### v2.0 (신규)
- 상세한 레이아웃 (A4~E22)
- 이름 정의(Name) 사용
- 템플릿 자동 생성
- Stage 표 포함

## 사용 방법

### 초기 설정

1. **Excel 파일 생성**: `.xlsm` 형식
2. **VBA 모듈 임포트**: `modPipelineControl.bas`
3. **템플릿 초기화**: `UI_InitTemplate` 실행
4. **필수 입력**: Project Root, Python EXE, Master Folder, Warehouse File

### 실행

- **전체 실행**: `RUN ALL (1→4)` 버튼
- **개별 실행**: `Run Stage1`, `Run Stage2` 등
- **유틸리티**: `Open Latest Output`, `Open Log Folder`, `Clear LOG`

## 마이그레이션

### 옵션 A: 새 파일 사용 (권장)

1. 새 Excel 파일 생성
2. `modPipelineControl.bas` 임포트
3. `UI_InitTemplate` 실행
4. 설정 입력

### 옵션 B: 기존 파일 업데이트

1. 기존 모듈 백업
2. 새 모듈 추가
3. `UI_InitTemplate` 실행
4. 데이터 수동 복사

자세한 내용은 [MIGRATION_GUIDE.md](../../vba/MIGRATION_GUIDE.md) 참조.

## 호환성

### 기존 모듈과의 관계

- **기존 모듈 유지**: `modPipelineLauncher.bas`는 그대로 유지 (하위 호환성)
- **신규 모듈 추가**: `modPipelineControl.bas`는 독립적으로 사용
- **동시 사용 가능**: 두 모듈을 함께 사용할 수 있음 (다른 Excel 파일에서)

### Excel 버전 호환성

- **Office LTSC 2021**: ✅ 완전 지원
- **Office 365**: ✅ 지원 (LTSC 전용 기능 미사용)
- **Office 2019**: ✅ 지원 (테스트 필요)

## 다음 단계

### 선택적 기능 추가

1. **xlwings 통합**
   - `vba/python_bridge.py`와 연동
   - 실시간 상태 업데이트

2. **Config 자동 반영**
   - CONTROL 시트 입력을 YAML에 자동 반영
   - 백업 포함

3. **고급 모니터링**
   - 진행률 표시
   - 실시간 로그 스트리밍

---

**최종 업데이트**: 2025-12-21  
**작성자**: HVDC 파이프라인 개발팀

