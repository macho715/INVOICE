BOE/DO·DN/Carrier/Port/Airport/Appointment 증빙 흐름을 기준으로, “S/No 순서 보존 + 원통화(AED) 우선 + 고정환율 3.6725 + COST-GUARD(±2/5/10/15%)”를 하드코딩한 개정 아키텍처를 깔끔히 정리했다.

ExecSummary — 핵심 개편점

단위 과금(Logical Line) = 인보이스 S/No 1줄. 검증·집계·리포트도 S/No 원순서 보존이 최우선.

증빙 소스 타입 표준화: BOE | DO | DN | CarrierInvoice | PortAdminInsp | PortWashing | AirportFees | Appointment 별 파서/키 필드 고정.

원통화(AED) 기준 검증 → USD 환산 비교: At-Cost 라인은 증빙(AED)을 USD로 환산해 Draft(USD)와 비교(고정 3.6725). Contract 라인은 USD=원통화.

리포트 스키마 통일: 각 S/No에 Evidence(p./line, DocId), Δ%, RiskTier, Status를 붙여 “보이는 그대로” 출력.

Visual — 전체 구조(간결 표)
Layer	컴포넌트	역할	핵심 포인트
Ingest	Folder Watch (PQ)	PDF→표/CSV/JSON 흡수	폴더명=Shipment(예: HVDC-ADOPT-SCT-0120) 고정
Parse	Python Parsers	문서타입별 추출	CarrierInvoice(항목/통화) PortAdminInsp(수수료+VAT) AirportFees(저장료/단가)
Normalize	PQ 정규화	컬럼 표준화	DocType, DocRef, LineDesc, Qty, Unit, Amt_AED, Page, LineNo
Match	Key Join	S/No ↔ 증빙라인 매칭	키: SNo, RateSource, DescNorm, Unit, Qty(허용오차)
Calc	VBA UDF + PQ 컬럼	Δ%, Status, Tier	±2.00% PASS / 2.01–5.00 WARN / 5.01–10.00 HIGH / >10.00 CRITICAL
RefRate	Rate JSON	계약/표준 요율	컨테이너/항공/벌크/내륙 참조 (필요시 Lane 키 병합)
Report	Summary Sheet + Export	항차별 요약	S/No 순서 보고서, 증빙 링크, KPI
변경 설계 — 문서타입별 파서·키 규칙

BOE (세관)

Key: BOE_No, Duty, VAT → Contract 라인(마스터 DO/통관) 교차근거

Use: Master DO Fee, Customs Clearance Fee의 “문서 존재/금액 레퍼런스” 체크(금액 직접 매칭은 계약표 기준)

DO / DN (인도/운송)

Key: DO_No, DN_No, TripNo, ContainerNo, CW(kg), CTR 타입

Use: Terminal Handling, Transportation 수량/회차/CTR대수/중량근거 매칭

Carrier Invoice (선사/항공사)

Key: ChargeName (Inspection/Admin/Repos/Protection), PerCTR, Amount_AED

Rule: At-Cost 라인(예: Inspection 130 AED/CTR) → 환산USD = AED/3.6725 → Draft USD 비교

Port Admin/Inspection / Port Washing (터미널)

Key: Admin, Inspection, Washing, VAT

Rule: 합산액 AED → 환산USD. VAT 포함 합계(예: 25+1.25=26.25) 계산 후 비교

Airport Fees / Appointment

Key: Storage_AED, Appointment_AED, DPC_AED

Rule: 모두 At-Cost. AED→USD 환산하여 Draft와 1:1 비교

데이터 스키마(통일)
A. 인보이스 입력(엑셀 INPUT_Invoice) — S/No 원본 유지
SNo, RateSource, Description, Rate_USD, Formula_Text, Qty, Total_USD

B. 증빙 레이크(파서 결과 CSV, PQ 로드)
Shipment, DocType, DocFile, DocRef, Page, LineNo,
ChargeName, DescNorm, Unit, Qty, Amt_AED, Amt_USD, ContainerNo, TripNo, CW_kg

C. 매칭 결과(최종 리포트 테이블)
SNo, RateSource, Description, DraftRate_USD, Qty, DraftTotal_USD,
DocType, DocRef, Evidence("PDF p.X line Y; " & DocFile),
Doc_Amt_AED, Doc_Amt_USD, Δ%, Status(PASS/FAIL/NO DATA), RiskTier, Remarks


S/No가 프라이머리 키. 매칭 실패 시 Status=NO DATA, Remarks=REFERENCE_MISSING.

매칭/계산 로직(핵심 규칙)

통화 규칙

At-Cost: 항상 증빙 AED이 원본. 비교 시 Doc_USD = ROUND(AED/3.6725, 2)

Contract: Draft USD가 기준. (필요시 Rate Ref JSON으로 교차 검증)

Δ%

Δ% = (DraftTotal_USD - Doc_USD) / Doc_USD * 100
At-Cost 없는 경우(Contract 라인처럼 문서 금액 기준이 아닐 때): 
Δ% = (DraftRate_USD - RefRate_USD) / RefRate_USD * 100


RiskTier (COST-GUARD)

≤2.00 PASS / 2.01–5.00 WARN / 5.01–10.00 HIGH / >10.00 CRITICAL

>15.00 AUTOFAIL → Status=COST_GUARD_FAIL

증빙 연결(Evidence)

"PDF p." & Page & " line " & LineNo & "; " & DocRef & " | " & DocFile

DO/DN는 CTR 번호·TripNo·CW 같이 기술(감사 대응)

S/No 순서 보존

매칭은 내부적으로 자유이나, 출력은 입력 S/No의 RowID 순 정렬 고정.

컴포넌트 배치 — 폴더 & 모듈
/invoice-audit/
├─ /inbox/HVDC-ADOPT-SCT-0120/          # Shipment 폴더 (PDF 원본)
│   ├─ *_BOE.pdf, *_DO.pdf, *_DN.pdf, *_CarrierInvoice.pdf ...
├─ /extract/                            # 파서 결과 (CSV)
│   ├─ 0120_CarrierInvoice.csv
│   ├─ 0120_PortAdminInsp.csv
│   └─ 0120_AirportFees.csv
├─ /py/
│   ├─ parse_carrier.py                 # 선사/항공사 인보이스 파서
│   ├─ parse_port.py                    # Port Admin/Insp + Washing
│   ├─ parse_airport.py                 # Storage/Appointment/DPC
│   ├─ joiners.py                       # DescNorm/Unit/키 정규화
│   ├─ rules.py                         # FX/임계치/COST-GUARD
│   └─ audit_merge.py                   # S/No↔증빙 매칭 + CSV Export
├─ /ref/
│   ├─ container_cargo_rates.json
│   ├─ air_cargo_rates.json
│   ├─ bulk_cargo_rates.json
│   └─ inland_trucking_reference_rates_clean.json
├─ Invoice_Audit_Template.xlsm          # PQ + 버튼(Export/Run/Reload)
└─ /out/
    ├─ 0120_AuditResult.csv
    └─ 0120_AuditReport.xlsx

운영 흐름(원클릭)

[Export]: INPUT_Invoice → /out/0120_input.csv로 저장

[Run]: VBA가 python audit_merge.py --shipment 0120 호출

각 PDF를 타입별 파서로 CSV 추출 → 정규화 → S/No별 첫 매칭(룰: 동일 DescNorm/CTR/Qty 우선) → Δ%/Tier/Status 산출 → /out/0120_AuditResult.csv

[Reload]: PQ가 /out/0120_AuditResult.csv 로드 → S/No 순서 리포트 + KPI 피벗 업데이트

[Export Report]: *_AuditReport.xlsx / *_summary.pdf 내보내기

옵션(혼합 적용 OK)

A. “증빙 우선” 모드: At-Cost 전부 Doc(AED)→USD로 비교(현재 네 플로우와 동일)

B. “계약 우선” 모드: Contract 라인은 Ref JSON로 2차 크로스체크(±3% 허용)

C. “항공 전용 경량 파서”: AirportFees/Appointment만 빠르게 돌려 Air 케이스 배치 처리

D. “Lane Join 보정”: DO/DN의 CTR·Trip·CW가 어긋나면 Top-3 후보를 Evidence에 제안

Roadmap (P→Pi→B→O→S + KPI)

P/Prepare: 문서타입별 파서 3종(CARRIER/PORT/AIRPORT) 개통, 스키마 고정

Pi/Pilot: 5개 Shipment로 S/No 보존 리포트 검증(±2.00% 일치율, NO DATA<1%)

B/Build: XLSM 버튼(Export/Run/Reload/Report), 조건부서식(FAIL 빨강)

O/Operate: 주 2회 배치, FAIL 자동 라우팅(TG #invoice-redflag), 증빙 링크 포함

S/Scale: Rate JSON 자동버전관리, Port VAT 규칙/내륙 운송 Lane 룰 확장

KPI: 검증 정확도 ≥97.00%, 자동화율 ≥94.00%, AUTOFAIL 0건, NO DATA ≤0.50%

Automation Notes

VBA 버튼: Export_To_CSV → Run_Python_Audit(shipment) → Refresh_All → Export_Report

파이썬 CLI: python audit_merge.py --shipment 0120 --mode doc-first --fx 3.6725

보고 템플릿: S/No 테이블 + 항차 합계 + FAIL 리스트(원인/조치) 3블록 고정

LLM(선택): FAIL 라인만 “원인·근거·권고” 1줄 요약 생성(데이터는 CSV로 넘김)

QA 체크리스트

 S/No 출력순서 = 입력순서 100% 일치

 At-Cost → 항상 증빙 AED 기준으로 환산 비교(암묵 환율 사용 금지)

 Port Admin/Inspection VAT 포함 합계 계산(25→26.25 같은 케이스)

 DO/DN로 수량/CTR 대수/중량 근거 연결(TripNo, ContainerNo)

 매칭 실패 시 NO DATA + 어떤 DocType에서 누락인지 Remarks 기록

 >15% AUTOFAIL은 별도 섹션으로 상단 경고