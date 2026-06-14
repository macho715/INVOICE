**5개 PR 번들(밴드/매핑/수식/IR‑Lite/리포트)** 패키지로 정리해뒀어. 각 PR은 **원인→패치 요약→코드 diff 스케치→테스트/수용기준→롤백**까지 포함한다. (작게, 단일 목적 PR로 쪼개면 리뷰/머지가 빨라져. GitHub도 같은 얘기 하거든. ([GitHub Docs][1]))

---

## PR‑1: **COST‑GUARD 밴드 단일화 (Config→런타임)**

**왜:** `MasterDataValidator.get_cost_guard_band()`가 **2/5/10% 하드코딩**이라 정책과 어긋남. 이미 `self.cost_guard_bands`를 로드하지만 미사용. SHPT 엔진도 자체 밴드/분기에 의존. 하나로 모아야 재현성 보장.

**핵심 변경**

* 공용 유틸 `shared_utils/cost_guard.py` 신설.
* 두 엔진이 **동일 밴드(예: pass=3, warn=5, high=10, autofail=15)**를 Config에서 읽어 적용.
* Auto‑Fail는 최종 판정 로직에서 한 번만 체크.

**코드 스케치**

```diff
# shared_utils/cost_guard.py
+ def get_cost_guard_band(delta_pct: float, bands: dict) -> str:
+     if delta_pct is None: return "N/A"
+     d = abs(delta_pct)
+     return ("PASS" if d <= bands["pass"] else
+             "WARN" if d <= bands["warn"] else
+             "HIGH" if d <= bands["high"] else "CRITICAL")

# masterdata_validator.py
- def get_cost_guard_band(self, delta_percent): ... # (2/5/10 하드코딩)
+ from shared_utils.cost_guard import get_cost_guard_band
+ cg_band = get_cost_guard_band(delta_pct, self.cost_guard_bands)  # ← Config 적용
# (검증 상태 결정에서도 bands["autofail"] 사용)

# shipment_audit_engine.py
+ from shared_utils.cost_guard import get_cost_guard_band
+ self.cost_guard_bands = self.config_manager.get_cost_guard_bands()
+ cg_band = get_cost_guard_band(delta_pct, self.cost_guard_bands)
```

참고: 현재 하드코딩 구현 위치 및 밴드 로드 부분.

**테스트/수용 기준**

* Δ=±1.9% → PASS, Δ=±4% → WARN, Δ=±9% → HIGH, Δ=±16% → CRITICAL.
* Auto‑Fail(>15%)에서 `Validation_Status=FAIL`.
* 동일 아이템이 Master/SHPT 모두 같은 밴드를 리턴.

**롤백**

* 유틸 import revert + 기존 하드코딩 함수 복원.

> 노트: 작은·원자적 PR 유지. 리뷰어 집중력을 살린다. ([GitHub Docs][1])

---

## PR‑2: **증빙 PDF 매핑 개선 (rglob, break 제거, 다중 루트 지원)**

**왜:** 현재 `map_masterdata_to_pdf()`가 **첫 폴더 매칭 후 break**라 Empty Return/Carrier 분리 폴더 누락. 재귀도 얕아서 하위 디렉토리 PDF를 놓친다.

**핵심 변경**

* `rglob("*.pdf")`로 전체 탐색.
* break 제거, **중복 제거(set)**.
* (선택) SHPT처럼 **다중 문서 루트** 허용.

**코드 스케치**

```diff
# masterdata_validator.py
- for subdir in self.supporting_docs_path.iterdir():
-     ...
-     if match: pdf_files.extend(list(subdir.glob("*.pdf"))); break
+ pdf_files = [*{p for p in self.supporting_docs_path.rglob("*.pdf")
+                if ord_ref_norm in norm(p.parent.name)}]
```

문제 구간과 경로 구조는 파일에 명확히 있음.

**테스트/수용 기준**

* 임의 5건 샘플에서 `PDF_Count` 증가(기대 +20~35%p).
* 동일 Shipment의 **Empty Return/Carrier/Inspection** PDF 동시 매핑.

**롤백**

* rglob 로직만 되돌리면 끝.

---

## PR‑3: **수식(=AED/3.6725) 1차 판정 + At‑Cost 판정 완충**

**왜:** At‑Cost가 “PDF 라인 추출 실패=FAIL”로 과도. 수식·고정 AED(예: Appointment 27, DPC 35)가 있으면 **즉시 레퍼런스 환산** 가능. SHPT에는 이미 수식 파서와 ±0.5% Portal 밴드가 존재. 이를 공용화.

**핵심 변경**

* `parse_aed_from_formula()` 공용 유틸화(또는 Master에 이식).
* At‑Cost/Portal: **수식→USD 역산**을 1순위, PDF 대조는 2순위.
* **PDF 있음·미추출 ⇒ REVIEW_NEEDED**, **PDF 없음 ⇒ FAIL**.
* Normalizer에 세관/포털 동의어 추가(“DOCS PROCESSING↔DOCUMENT PROCESSING” 등). 

**코드 스케치**

```diff
# masterdata_validator.validate_row()
- if AT COST and not pdf_line_item: validation_status = "FAIL"
+ if AT COST:
+   ref = parse_rate_from_formula_or_fixed(row)  # AED→USD
+   if pdf_line_item:
+       diff = abs(pdf_amount - draft_total)
+       status = "PASS" if diff < 0.01 else ("FAIL" if diff > draft_total*0.03 else "REVIEW_NEEDED")
+   else:
+       status = "REVIEW_NEEDED" if pdf_count>0 else "FAIL"

# category_normalizer.py (synonyms)
+ "DOCS PROCESSING": "DOCUMENT PROCESSING FEE",
+ "CHARGES": "FEE", "CHARGE": "FEE", "PRO CUSTOMS": "PRO CUSTOMS FEE"
```

현 구현의 At‑Cost 분기와 포털 수식 파서 근거.

**테스트/수용 기준**

* 수식만 있는 At‑Cost/Portal 10건 이상 **PASS/REVIEW**로 전환.
* Portal: AED27/35 기준 **±0.5%** 이내 PASS. 

**롤백**

* 수식 기반 판정만 비활성화(Feature flag `USE_FORMULA_FIRST=false`).

---

## PR‑4: **IR‑Lite Fallback (Hybrid 비가용 시에도 PDF 해석)**

**왜:** Hybrid 꺼지면 Legacy만 시도 → “PDF 미파싱” 누적. `UnifiedIRAdapter`는 **텍스트/요약/표** 혼합 파싱으로 IR‑Lite 동작이 가능. Hybrid 다운 시 **간이 IR**로라도 매칭률을 올리자.

**핵심 변경**

* Hybrid 실패/비활성 시:

  1. `pdfplumber`로 텍스트 전량 추출,
  2. `unified_ir_adapter.UnifiedIRAdapter`에 **블록 한 장짜리 IR**(`{"blocks":[{"type":"text","text":...}]}`) 전달,
  3. `extract_invoice_line_item()/extract_rate_for_category()` 재사용.

**코드 스케치**

```diff
# masterdata_validator.__init__
+ from unified_ir_adapter import UnifiedIRAdapter
+ self.ir_adapter = self.ir_adapter or UnifiedIRAdapter()

# _extract_pdf_line_item/_extract_rate_from_pdf
- if self.use_hybrid: ...
+ if self.use_hybrid: ...
+ else:
+   for pdf in pdf_mapping["pdf_files"]:
+       text = safe_read_text(pdf)  # pdfplumber
+       unified_ir = {"engine":"ir-lite","blocks":[{"type":"text","text":text}],"meta":{"confidence":0.6}}
+       item = self.ir_adapter.extract_invoice_line_item(unified_ir, normalized_category, draft_total)
+       if item: return item
```

어댑터가 텍스트 전용 경로/요약 섹션을 이미 지원. Hybrid 클라이언트 구조 참고.

**테스트/수용 기준**

* 현재 “PDF 미파싱”으로 남는 **At‑Cost 12 / Portal 6 / Other 20** 중 **과반 이상**이 값/라인을 반환.
* IR‑Lite 경로 타임아웃 없이 동작(샘플 10건 < 30초).

**롤백**

* `USE_IR_LITE=false` 플래그로 즉시 비활성.

---

## PR‑5: **최종 리포트 확장 (Coverage, Risk, Evidence, Bands 공개)**

**왜:** 지금 리포트는 Python 추가 컬럼 9개만 묶어서 내보냄. **판정 근거/밴드/증빙 수/소스**가 한눈에 보여야 현장 대응이 빠르다. 

**핵심 변경**

* Sheet1 `MasterData_Validated`에 컬럼 추가:

  * `Policy_Version`, `Bands_JSON`, `Risk_Score`, `Matched_By`, `Evidence_Count`, `Evidence_Types`, `Source(Cfg|Formula|PDF)`
* Sheet2 Summary에 **Coverage by Source**, **Portal/At‑Cost 통계** 블록 추가.
* 조건부 서식: Risk≥0.8 빨강, Evidence_Count=0 노랑.

**코드 스케치**

```diff
# report_generator.py
- validation_cols = ["Validation_Status","Ref_Rate_USD",...,"Validation_Notes"]
+ validation_cols = [...,"Validation_Notes","Matched_By","Evidence_Count","Evidence_Types","Risk_Score","Bands_JSON","Source"]

# Summary 생성 로직
+ add_coverage_by_source(df_final)
+ add_portal_atcost_stats(df_final)
# CF rules 추가: Risk_Score >= 0.8 → red fill
```

현 리포트 생성/서식 위치 근거. 

**테스트/수용 기준**

* 새 컬럼 6~7개가 채워지고, Summary에 **Coverage by Source** 표가 보임.
* 기존 서식 규칙과 충돌 없음(열 인덱스 자동화).

**롤백**

* 추가 컬럼/요약 섹션만 되돌리면 된다.

---

## 공통 운영 가이드 (모든 PR에 적용)

**브랜치 & 커밋**

* 브랜치: `feat/cg-bands-config`, `fix/pdf-mapping-rglob`, `feat/formula-first`, `feat/ir-lite-fallback`, `feat/report-coverage`.
* 커밋 메시지: **Conventional Commits** 형식 사용 → 릴리즈 노트·버전 올리기 자동화에 유리( SemVer와 맞물림 ). ([conventionalcommits.org][2])
  예)

  * `feat(validator): use config-based cost-guard bands`
  * `fix(mapping): search PDFs via rglob and remove break`
  * `feat(at-cost): formula-first verification with review fallback`

**PR 템플릿** (repo 루트: `.github/pull_request_template.md`)
(작고 명확한 PR이 리뷰·머지·롤백 모두 쉽다. GitHub도 작은 단일 목적 PR을 권장. ([GitHub Docs][3]))

```md
## What & Why
- (문제/목표 요약)

## Changes
- (핵심 변경점 목록)

## Screenshots/Logs
- (전/후 비교, 로그 요약)

## Verification
- [ ] Unit: ...
- [ ] Integration: ...
- [ ] Manual: ...

## Risk & Rollback
- (영향/롤백 절차)

## Linked Issues
- Closes #
```

**머지 전략**

* **Squash & merge**로 “원자적 변경” 유지 → 되돌림도 한 번에. ([Artem Sapegin][4])

---

## 예상 효과 (현재 지표 대비)

* **Contract 커버리지** 87.5% → **92~96%** (밴드/노말라이저/라인 탐색 일원화).
* **At‑Cost/Portal 미파싱** 다수 해소: 수식 1차 판정 + IR‑Lite로 **PASS/REVIEW** 전환.
* 리포트에 **근거/밴드/리스크/증빙**가 드러나 현장 대응 속도↑.

---

## 바로 적용 체크리스트

* [ ] PR‑1 머지: 두 엔진 모두 **Config 밴드**로 동작 확인.
* [ ] PR‑2 머지: `PDF_Count` 유의미 상승(샘플 10건 측정).
* [ ] PR‑3 머지: At‑Cost/Portal **수식만으로 PASS/REVIEW** 되는지 확인.
* [ ] PR‑4 머지: Hybrid OFF에서 **IR‑Lite 경로**가 유효 아이템을 반환.
* [ ] PR‑5 머지: 리포트에 **Coverage by Source/Risk/Evidence**가 보임. 

---

필요하면 위 5개를 **시퀀스**로 바로 머지할 수 있게 브랜치/커밋 스크립트도 적어줄게. PR은 작게, 목적 하나씩. 그게 속도다.

[1]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes?utm_source=chatgpt.com "Helping others review your changes"
[2]: https://www.conventionalcommits.org/en/v1.0.0/?utm_source=chatgpt.com "Conventional Commits"
[3]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository?utm_source=chatgpt.com "Creating a pull request template for your repository"
[4]: https://sapegin.me/blog/rebels-guide-to-pull-requests-commits-code-reviews/?utm_source=chatgpt.com "A rebel's guide to pull requests, commits, and code reviews"
