# HVDC Invoice Audit System - Quick Start Guide

**빠른 시작 가이드** | **Last Updated**: 2025-10-12

---

## 🚀 SHPT 시스템 즉시 실행

### 1. 디렉토리 이동
```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\01_DSV_SHPT\Core_Systems"
```

### 2. 시스템 실행
```powershell
python shpt_sept_2025_enhanced_audit.py
```

### 3. 결과 확인
```powershell
cd "..\Results\Sept_2025\Reports"
cat SHPT_SEPT_2025_FINAL_REPORT.md
```

**예상 실행 시간**: 1.5초  
**예상 결과**: 102개 항목, 35개 PASS (34.3%)

---

## 🚛 DOMESTIC 시스템 즉시 실행

### 1. 디렉토리 이동
```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\02_DSV_DOMESTIC\Core_Systems"
```

### 2. 시스템 실행
```powershell
python domestic_sept_2025_audit.py
```

**또는 간단 실행:**
```powershell
python run_domestic_sept2025.py
```

### 3. 결과 확인
```powershell
cd "..\Results\Sept_2025\Reports"
cat DOMESTIC_SEPT_2025_FINAL_REPORT.md
```

**예상 실행 시간**: 1.4초  
**예상 결과**: 8개 항목 (샘플), 5개 PASS (62.5%)

---

## 📁 주요 파일 위치

### SHPT 시스템

**실행 파일**:
```
01_DSV_SHPT/Core_Systems/shpt_sept_2025_enhanced_audit.py
```

**최신 결과**:
```
01_DSV_SHPT/Results/Sept_2025/JSON/shpt_sept_2025_enhanced_result_20251012_121143.json
01_DSV_SHPT/Results/Sept_2025/CSV/shpt_sept_2025_enhanced_result_20251012_121143.csv
01_DSV_SHPT/Results/Sept_2025/Reports/SHPT_SEPT_2025_FINAL_REPORT.md
```

**인보이스 파일**:
```
01_DSV_SHPT/Data/DSV 202509/SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm
```

**증빙문서**:
```
01_DSV_SHPT/Data/DSV 202509/SCNT Import (Sept 2025) - Supporting Documents/  (57 PDFs)
01_DSV_SHPT/Data/DSV 202509/SCNT Domestic (Sept 2025) - Supporting Documents/  (36 PDFs)
```

### DOMESTIC 시스템

**실행 파일**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_sept_2025_audit.py
02_DSV_DOMESTIC/Core_Systems/run_domestic_sept2025.py
```

**최신 결과**:
```
02_DSV_DOMESTIC/Results/Sept_2025/JSON/domestic_sept_2025_result_20251012_133549.json
02_DSV_DOMESTIC/Results/Sept_2025/CSV/domestic_sept_2025_result_20251012_133549.csv
02_DSV_DOMESTIC/Results/Sept_2025/Reports/DOMESTIC_SEPT_2025_FINAL_REPORT.md
```

**참조 데이터**:
```
02_DSV_DOMESTIC/DOMESTIC_with_distances.xlsx
```

---

## 🔍 결과 파일 확인 방법

### JSON 결과 확인
```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\01_DSV_SHPT\Results\Sept_2025\JSON"
Get-Content "shpt_sept_2025_enhanced_result_20251012_121143.json" | ConvertFrom-Json
```

### CSV 결과 확인
```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\01_DSV_SHPT\Results\Sept_2025\CSV"
Import-Csv "shpt_sept_2025_enhanced_result_20251012_121143.csv" | Out-GridView
```

### 최종 보고서 확인
```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\01_DSV_SHPT\Results\Sept_2025\Reports"
cat "SHPT_SEPT_2025_FINAL_REPORT.md"
```

---

## 📊 주요 결과 (9월 2025)

### 전체 통계
- **총 시트**: 28개
- **총 항목**: 102개
- **총 금액**: $21,402.20 USD
- **처리 시간**: 1.5초

### 검증 결과
- ✅ **PASS**: 35개 (34.3%)
- ⚠️ **REVIEW**: 66개 (64.7%)
- ❌ **FAIL**: 1개 (1.0%)

### Charge Group
- **Contract**: 64개 (62.7%)
- **AtCost**: 14개 (13.7%)
- **PortalFee**: 4개 (3.9%)
- **Other**: 20개 (19.6%)

### Gate 검증
- **Gate PASS**: 35개 (34.3%)
- **평균 Score**: 78.8/100
- **증빙문서**: 93개 PDF 매핑

---

## 🛠️ 시스템 요구사항

### Python 환경
```bash
Python 3.8+
pandas
openpyxl
```

### 설치
```powershell
pip install pandas openpyxl
```

---

## ⚠️ 주의사항

1. **Excel 파일 경로**
   - 시스템은 `Data/DSV 202509/` 폴더에서 인보이스 파일을 찾습니다
   - 파일명이 정확히 일치해야 합니다

2. **증빙문서 명명 규칙**
   - PDF 파일명: `HVDC-ADOPT-{ShipmentID}_{DocType}.pdf`
   - 예: `HVDC-ADOPT-SCT-0126_BOE.pdf`

3. **Portal Fee AED 수식**
   - FORMULA 컬럼: `=27/3.6725` 형태로 입력
   - 숫자만 사용 (쉼표 없음)

---

## 📞 문제 해결

### 자주 발생하는 오류

**Q: FileNotFoundError**
```
A: Data/DSV 202509/ 폴더 경로를 확인하세요
```

**Q: 증빙문서 연결 안 됨**
```
A: PDF 파일명 형식을 확인하세요 (HVDC-ADOPT-XXX_YYY.pdf)
```

**Q: Portal Fee FAIL**
```
A: FORMULA 컬럼에 AED 수식이 있는지 확인하세요
```

---

## 📚 추가 문서

- `README.md` - 프로젝트 전체 개요
- `01_DSV_SHPT/README.md` - SHPT 시스템 상세 가이드
- `02_DSV_DOMESTIC/README.md` - DOMESTIC 시스템 가이드
- `MIGRATION_COMPLETE_REPORT.md` - Migration 완료 보고서

---

**시스템 상태**: SHPT ✅ Ready | DOMESTIC ✅ Ready  
**마지막 검증**: 2025-10-12 13:35:51  
**SHPT**: 102개 항목 | **PASS**: 35 (34.3%)  
**DOMESTIC**: 8개 항목 (샘플) | **PASS**: 5 (62.5%)

