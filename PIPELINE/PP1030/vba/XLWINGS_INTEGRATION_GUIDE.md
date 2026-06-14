# xlwings 통합 가이드

## ⚠️ 현재 상태: 미통합

**현재 구현 상태**: `modHVDC_CONTROL.bas` (v3.0)에는 xlwings가 통합되어 있지 않습니다.

현재는 VBA에서 직접 Python 스크립트를 호출하는 방식(`Shell` 함수 사용)을 사용하고 있습니다.

## 개요

xlwings를 사용하여 VBA 런처를 더욱 강화할 수 있습니다. Excel 셀에서 직접 Python 함수를 호출하거나, VBA에서 Python 함수를 호출할 수 있습니다.

**참고**: 이 가이드는 향후 xlwings 통합 시 참고용으로 제공됩니다.

## 설치

### 1. Python 패키지 설치

```bash
pip install xlwings>=0.31.0
```

### 2. Excel 추가 기능 설치

```bash
xlwings addin install
```

또는 Excel에서:
1. Excel → 파일 → 옵션 → 추가 기능
2. "xlwings" 확인

## 사용 방법

### 방법 1: VBA에서 Python 함수 호출

**VBA 코드 예시**:
```vb
Sub Run_Stage1_With_xlwings()
    Dim result As Variant
    
    ' Python 함수 호출
    result = RunPython("run_pipeline_stage", 1)
    
    ' 결과 확인
    If result("status") = "SUCCESS" Then
        MsgBox "Stage 1 완료: " & result("message")
    Else
        MsgBox "오류: " & result("message"), vbCritical
    End If
End Sub
```

### 방법 2: Excel 셀에서 직접 Python 함수 호출

**Excel 셀에 입력**:
```
=run_pipeline_stage(1)
```

**상태 조회**:
```
=get_pipeline_status()
```

## 통합된 함수 목록

### run_pipeline_stage(stage_num)

Stage를 실행하고 결과를 반환합니다.

**매개변수**:
- `stage_num`: Stage 번호 (1-4)

**반환값**:
```json
{
    "status": "SUCCESS" | "ERROR",
    "message": "상세 메시지",
    "stage": 1,
    "output_files": []
}
```

### get_pipeline_status()

파이프라인 상태를 조회합니다.

**반환값**:
```json
{
    "stage1": "completed" | "running" | "pending" | "error",
    "stage2": "...",
    "stage3": "...",
    "stage4": "...",
    "last_update": "2025-12-21 12:00:00"
}
```

### get_pipeline_progress()

파이프라인 진행률을 조회합니다.

**반환값**:
```json
{
    "stage1": 100,
    "stage2": 50,
    "stage3": 0,
    "stage4": 0,
    "overall": 37.5
}
```

### validate_pipeline_config()

파이프라인 설정을 검증합니다.

**반환값**:
```json
{
    "valid": true | false,
    "errors": ["오류 메시지 리스트"],
    "warnings": ["경고 메시지 리스트"]
}
```

## VBA 런처와의 통합 (향후 계획)

현재 `modHVDC_CONTROL.bas`에는 xlwings가 통합되어 있지 않습니다. 향후 통합 시 다음 방식으로 사용할 수 있습니다:

기존 VBA 런처(`modPipelineLauncher.bas` 또는 `modHVDC_CONTROL.bas`)와 함께 사용할 수 있습니다:

```vb
Public Sub Run_Stage1_Enhanced()
    ' xlwings로 상태 확인
    Dim status As Variant
    status = RunPython("get_pipeline_status")
    
    If status("stage1") = "running" Then
        MsgBox "Stage 1이 이미 실행 중입니다.", vbInformation
        Exit Sub
    End If
    
    ' 기존 런처로 실행
    RunStage 1
    
    ' 완료 후 상태 업데이트
    status = RunPython("get_pipeline_status")
    Debug.Print "Stage 1 상태: " & status("stage1")
End Sub
```

## 문제 해결

### "RunPython 함수를 찾을 수 없습니다"

**해결**:
1. Excel 추가 기능 설치 확인
2. `xlwings addin install` 재실행
3. Excel 재시작

### Python 함수 호출 실패

**해결**:
1. Python 경로 확인
2. `vba/python_bridge.py` 모듈 경로 확인
3. Python 환경에서 직접 테스트

## 현재 구현과의 차이점

### 현재 구현 (modHVDC_CONTROL.bas v3.0)
- **방식**: VBA `Shell` 함수로 Python 스크립트 직접 호출
- **장점**: 추가 의존성 없음, 간단한 구조
- **단점**: 실시간 상태 업데이트 제한적, 반환값 처리 복잡

### xlwings 통합 시 (향후)
- **방식**: VBA에서 Python 함수 직접 호출
- **장점**: 실시간 상태 업데이트, 구조화된 반환값, Excel 셀에서 직접 호출 가능
- **단점**: xlwings 설치 및 설정 필요

## 통합 계획 (선택적)

xlwings 통합을 원하시면 다음 단계를 진행할 수 있습니다:

1. **xlwings 설치**: `pip install xlwings>=0.31.0`
2. **Excel 추가 기능 설치**: `xlwings addin install`
3. **Python 브리지 모듈 생성**: `vba/python_bridge.py` 확장
4. **VBA 코드 수정**: `RunPython` 함수 사용으로 변경

---

**참고**: 자세한 내용은 `docs/technical/EXCEL_LIBRARIES_INTEGRATION.md` 참조  
**현재 상태**: 미통합 (선택적 기능)

