좋아. **수요 집중(capacity gap) 시나리오** 반영해서 바로 쓰는 **v4 패치(diff)** 만들었다.
핵심 변경:

* **Auto-Bump 상한 기본 4 → 16** (수요 16건까지 자동 흡수)
* **수요↔용량 요약 CSV 덤프**(옵션) 추가: `dn_supply_demand.csv`
* **PDF raw_text 폴백에 PyMuPDF 추가**(우선 시도) → 다단/복합 레이아웃 안정화

아래를 `patch_v4.diff`로 저장 → 프로젝트 루트에서 `git apply patch_v4.diff`.

---

```diff
*** Begin Patch
*** Update File: src/utils/pdf_text_fallback.py
@@
-"""
-PDF 본문 텍스트 폴백 추출기
-- 우선순위: pypdf → pdfminer.six → pdftotext(외부) → 빈문자열
-"""
+"""
+PDF 본문 텍스트 폴백 추출기
+- 우선순위: PyMuPDF(fitz) → pypdf → pdfminer.six → pdftotext(외부) → 빈문자열
+  (다단/표 혼합 문서의 추출 안정성을 위해 PyMuPDF를 최우선 시도)
+"""
 from __future__ import annotations
 import os
 import subprocess
 from pathlib import Path
 from typing import Optional
@@
+def _try_pymupdf(pdf_path: str) -> str:
+    try:
+        import fitz  # PyMuPDF
+        doc = fitz.open(pdf_path)
+        texts = []
+        for page in doc:
+            try:
+                # 레이아웃 보존력이 높은 모드 조합
+                t = page.get_text("text") or ""
+                if not t.strip():
+                    t = page.get_text() or ""
+                texts.append(t)
+            except Exception:
+                continue
+        doc.close()
+        return "\n".join(texts)
+    except Exception:
+        return ""
+
 def _try_pypdf(pdf_path: str) -> str:
@@
 def extract_text_any(pdf_path: str) -> str:
     """가용 백엔드를 순차 시도하여 텍스트 추출."""
     pdf_path = str(pdf_path)
-    for fn in (_try_pypdf, _try_pdfminer, _try_pdftotext):
+    for fn in (_try_pymupdf, _try_pypdf, _try_pdfminer, _try_pdftotext):
         txt = fn(pdf_path)
         if txt and txt.strip():
             return txt
     return ""
*** End Patch
```

```diff
*** Begin Patch
*** Update File: src/utils/dn_capacity.py
@@
 def auto_capacity_bump(dn_list: List[dict], top_choice_counts: Dict[int, int]) -> None:
     """
     두 단계 매칭을 위해 사전 '수요' 카운트 기반 자동 용량상향.
-    - ENV DN_AUTO_CAPACITY_BUMP=true (기본 false)
-    - ENV DN_MAX_CAPACITY=4 (상한)
+    - ENV DN_AUTO_CAPACITY_BUMP=true (기본 false)
+    - ENV DN_MAX_CAPACITY=16 (상한; 인기 DN 수요 대응)
     - 오버라이드(capacity가 이미 지정된 DN)는 존중(더 이상 올리지 않음)
     """
     if os.getenv("DN_AUTO_CAPACITY_BUMP", "false").lower() != "true":
         return
-    max_cap = _safe_int(os.getenv("DN_MAX_CAPACITY", "4"), 4)
+    max_cap = _safe_int(os.getenv("DN_MAX_CAPACITY", "16"), 16)
     for j, dn in enumerate(dn_list):
         if "capacity" in dn and isinstance(dn["capacity"], int) and dn["capacity"] > 1:
             continue  # 수동 오버라이드 존중
         demand = int(top_choice_counts.get(j, 0))
         if demand > 1:
*** End Patch
```

```diff
*** Begin Patch
*** Update File: validate_sept_2025_with_pdf.py
@@
-# TopN 후보 덤프
+# TopN 후보 덤프
 DN_DUMP_TOPN = int(os.getenv("DN_DUMP_TOPN", "0"))  # 0이면 비활성; 3이면 상위 3개 덤프
 DN_DUMP_PATH = os.getenv("DN_DUMP_PATH", "dn_candidate_dump.csv")
+# 수요↔용량 요약 덤프
+DN_DUMP_SUPPLY = os.getenv("DN_DUMP_SUPPLY", "true").lower() == "true"
+DN_DUMP_SUPPLY_PATH = os.getenv("DN_DUMP_SUPPLY_PATH", "dn_supply_demand.csv")
@@
     top_choice_counts = {}  # dn index -> 해당 DN을 최고로 선택한 row 수
+    # dn 인덱스별 참조 메타(출력용)
+    dn_meta = {j: {
+        "shipment_ref": str(dn.get("shipment_ref","") or ""),
+        "name": str(dn.get("filename","") or dn.get("pdf_path","") or "")
+    } for j, dn in enumerate(dn_list)}
@@
-    auto_capacity_bump(dn_list, top_choice_counts)
+    auto_capacity_bump(dn_list, top_choice_counts)
@@
     pairs.sort(key=lambda x: x[0], reverse=True)
@@
     assigned_row = set()
     pick_for_row = {}
     for sc, idx, j in pairs:
         if idx in assigned_row:
             continue
         if dn_capacity.get(j, 0) <= 0:
             continue
         # 할당
         pick_for_row[idx] = j
         assigned_row.add(idx)
         dn_capacity[j] -= 1
@@
     if DN_DUMP_TOPN > 0:
         try:
             import csv
             with open(DN_DUMP_PATH, "w", newline="", encoding="utf-8") as f:
                 wr = csv.writer(f)
                 wr.writerow(["row_idx","best_n","score","dn_index","shipment_ref","filename/pdf_path"])
                 # 행별 상위 N 추출
                 from collections import defaultdict
                 per_row = defaultdict(list)
                 for sc, idx, j in pairs:
                     per_row[idx].append((sc, j))
                 for idx in range(len(items_df)):
                     cands = sorted(per_row.get(idx, []), key=lambda x:x[0], reverse=True)[:DN_DUMP_TOPN]
                     for rank, (sc, j) in enumerate(cands, start=1):
                         dn = dn_list[j]
                         wr.writerow([idx, rank, sc, j, dn.get("shipment_ref",""), dn.get("filename","") or dn.get("pdf_path","")])
         except Exception:
             pass
+
+    # 수요↔용량 요약 덤프 (인기 DN 병목 파악)
+    if DN_DUMP_SUPPLY:
+        try:
+            import csv
+            with open(DN_DUMP_SUPPLY_PATH, "w", newline="", encoding="utf-8") as f:
+                wr = csv.writer(f)
+                wr.writerow(["dn_index","shipment_ref","filename/pdf_path","demand_top1","capacity_final","gap"])
+                for j in range(len(dn_list)):
+                    demand = int(top_choice_counts.get(j, 0))
+                    cap = int(dn_list[j].get("capacity", 1))
+                    gap = max(0, demand - cap)
+                    wr.writerow([j, dn_meta[j]["shipment_ref"], dn_meta[j]["name"], demand, cap, gap])
+        except Exception:
+            pass
*** End Patch
```

```diff
*** Begin Patch
*** Update File: debug_detailed.py
@@
 def print_dn_reuse_stats(items_df):
@@
         for k, v in list(multi.items())[:20]:
             print(f"   - {k}: {v} items")

 def print_unmatched_reasons(items_df):
@@
         print(f"  {k}: {v}")
+
+def print_supply_demand_hint():
+    path = "dn_supply_demand.csv"
+    if os.path.exists(path):
+        try:
+            import pandas as pd
+            df = pd.read_csv(path)
+            hot = df.sort_values(["gap","demand_top1"], ascending=[False, False]).head(8)
+            print("\n[Hot DN (gap-ranked)]")
+            for _, r in hot.iterrows():
+                print(f"  {r['shipment_ref']}  demand={int(r['demand_top1'])} cap={int(r['capacity_final'])} gap={int(r['gap'])}")
+            print("  ↑ DN_MAX_CAPACITY 또는 DN_CAPACITY_MAP으로 상향 필요 후보")
+        except Exception:
+            print(f"\n[Hint] supply/demand summary at {path}")
*** End Patch
```

---

## 적용·실행

```bash
git apply patch_v4.diff

# (권장) 자동 용량 상향 사용 + 상한 16
export DN_AUTO_CAPACITY_BUMP=true
export DN_MAX_CAPACITY=16

# (선택) 수동 오버라이드(보고서 근거치)
export DN_CAPACITY_MAP='{
  "HVDC-ADOPT-SCT-0126": 16,
  "HVDC-DSV-PRE-MIR-SHU-230": 7,
  "HVDC-DSV-SAS-MOSB-217": 4,
  "HVDC-DSV-MOSB-SHU-216": 3
}'

python validate_sept_2025_with_pdf.py
python check_results.py
```

## 기대 변화

* **DN_CAPACITY_EXHAUSTED** 12건 중 다수를 **자동 상향(16)**으로 흡수 → **매칭률 ~90%대** 목표.
* `dn_supply_demand.csv`로 **병목 DN** 바로 식별 가능(예: `SCT-0126`, `PRE-MIR-SHU-230`).
* PDF `raw_text` 추출 안정성 ↑ (PyMuPDF 선시도; 다단·표 혼합 문서 호환)

필요하면 **DN별 상한 캡 룰**(예: `HAZMAT` 경로 cap≤2 같은 정책)도 추가해줄 수 있어. 지금은 “수요만큼 유연하게”가 목표라 상향 중심으로 잡았어.
