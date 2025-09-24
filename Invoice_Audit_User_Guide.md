# 📑 Invoice Audit 자동화 시스템 – 설치 및 사용 가이드

## 1. 구성 요소 (ZIP 안에 포함)
- **VBA 모듈**
  - `modNamedRangeMap.bas` : 시트별 데이터 영역을 자동 감지 → Named Range 생성 (`rng_Header_*`, `rng_Data_*`)
  - `Module1.bas` : Export/Run/Refresh 기본 버튼
  - `modAuditControl.bas` : 원클릭 파이프라인(정리→CSV→Python→결과 리로드→리포트)
- **Python 스크립트**
  - `audit_runner.py` : 인보이스 라인아이템 검증 엔진
  - `rules.py` : 고정환율(USD/AED=3.6725), Δ% 허용치, Risk Band 정의
  - `joiners.py` : 목적지/단위 정규화, Port 힌트 로직

---

## 2. 설치 방법

### 2.1 ZIP 압축 풀기
1. `invoice_audit_delivery_final.zip` 압축을 풀어 원하는 작업 폴더에 배치  
   예: `D:\Projects\InvoiceAudit\`

### 2.2 Excel (VBA 모듈 Import)
1. 엑셀에서 `Alt+F11` → VBA 편집기 열기  
2. `File > Import File…` 메뉴에서 다음 `.bas` 파일을 순서대로 가져오기:
   - `modNamedRangeMap.bas`
   - `Module1.bas`
   - `modAuditControl.bas`  
3. 가져온 뒤 저장 (`Invoice_Audit_Template.xlsm` 등 매크로 지원 파일 형식으로)

### 2.3 Python 환경 준비
1. PC에 Python 3.9+ 설치 확인
2. `invoice-audit/py/` 경로에 다음 파일이 있어야 함:
   - `audit_runner.py`
   - `rules.py`
   - `joiners.py`
3. CMD/PowerShell에서 실행 테스트:
   ```bash
   cd D:\Projects\InvoiceAudit\invoice-audit\py
   python audit_runner.py --shipment 0120
   ```

---

## 3. 사용 흐름

### 3.1 Named Range 자동 생성
- 엑셀 매크로 실행:  
  ```vb
  Call modNamedRangeMap.MapAllSheetsToNamedRanges
  ```
- 각 시트별로 `rng_Data_<SheetName>` 생성됨

### 3.2 Export → Audit → Refresh
1. `Module1.Export_To_CSV` : 현재 인보이스 테이블을 `/io/<shipment>_Invoice_Items.csv`로 저장
2. `Module1.Run_Python_Audit` : Python 검증 실행 → `/out/<shipment>_Audit_Result.csv` 생성
3. `Module1.Refresh_All` : Power Query가 결과 CSV 로드 → `REF_Status` 시트 업데이트

### 3.3 원클릭 전체 실행
- `modAuditControl.Run_All_Audit`  
  → 데이터 정리 → CSV Export → Python 실행 → PQ Refresh → 리포트(PDF/CSV) 출력까지 자동

---

## 4. 검증 규칙 (COST-GUARD)

- **환율 고정** : 1 USD = 3.6725 AED  
- **허용치**
  - ≤ ±2% : PASS  
  - 2.01–5% : WARN  
  - 5.01–10% : HIGH  
  - >10% : CRITICAL  
  - >15% : AUTOFAIL  
- **At-Cost 라인** : 증빙(AED) ÷ 3.6725 → Draft USD와 비교  
- **Contract 라인** : Draft USD ↔ Ref 요율 JSON 비교 (±3% 허용)

---

## 5. 보고서 구조

최종 `Audit_Result.csv` 및 `REF_Status` 시트에는 다음 컬럼 포함:
- `SNo, RateSource, Description, DraftRate_USD, Qty, DraftTotal_USD`
- `Ref_Rate_USD, Delta_%, CG_Band, Status, Flag`
- `Evidence` (PDF 페이지/라인, DocRef 등 확장 가능)

---

## 6. 추천 워크플로우
1. 인보이스 Draft 붙여넣기 → Named Range 매핑 실행  
2. `Run_All_Audit` 매크로 실행 (Shipment ID 입력)  
3. 결과 PDF/CSV 리포트 확인 → FAIL/WARN 라인 검토  
4. 최종 승인 후 고객사/회계팀 전달  

---

## 7. 트러블슈팅
- **ZIP 다운로드 안 됨** → PC 브라우저에서 링크 우클릭 → “다른 이름으로 저장”  
- **Python 실행 오류** → 경로 확인 (`py` 폴더 내 실행), Python 버전 3.9 이상 확인  
- **엑셀에서 매크로 실행 안 됨** → 매크로 보안 설정에서 “모든 매크로 허용” 필요  
