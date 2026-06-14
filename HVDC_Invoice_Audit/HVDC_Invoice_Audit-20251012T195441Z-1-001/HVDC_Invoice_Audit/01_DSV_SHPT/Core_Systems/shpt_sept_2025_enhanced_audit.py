#!/usr/bin/env python3
"""
SHPT Enhanced 9월 2025 Invoice Audit System

SHPT 시스템 + Portal Fee 검증 + Gate 검증 + 9월 인보이스 지원
- Excel 직접 처리
- Portal Fee ±0.5% 검증
- 핵심 Gate 검증 (3개)
- S/No 순서 보존
- 시트별 통계
"""

import pandas as pd
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

# UnifiedRateLoader import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from rate_loader import UnifiedRateLoader

# PDF Integration import
try:
    from invoice_pdf_integration import InvoicePDFIntegration

    PDF_INTEGRATION_AVAILABLE = True
except ImportError:
    PDF_INTEGRATION_AVAILABLE = False
    logging.warning(
        "PDF Integration not available. Install dependencies: pip install pdfplumber rdflib"
    )


class SHPTSept2025EnhancedAuditSystem:
    """SHPT Enhanced 9월 2025 감사 시스템"""

    def __init__(self):
        self.root = Path(
            __file__
        ).parent.parent  # Core_Systems의 상위 폴더 (01_DSV_SHPT)
        self.out_dir = self.root / "Results" / "Sept_2025"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # 9월 2025 파일 경로 - 여러 위치 시도
        excel_candidates = [
            self.root.parent.parent / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm",
            self.root / "Data" / "DSV 202509" / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm",
            self.root / "Data" / "DSV 202509" / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm",
        ]
        self.excel_file = None
        for candidate in excel_candidates:
            if candidate.exists():
                self.excel_file = candidate
                break
        
        if not self.excel_file:
            raise FileNotFoundError(f"Invoice file not found. Tried: {[str(c) for c in excel_candidates]}")
        self.supporting_docs_paths = [
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT Import (Sept 2025) - Supporting Documents",
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT Domestic (Sept 2025) - Supporting Documents",
        ]

        # SHPT 설정
        self.system_type = "SHPT_ENHANCED"
        self.scope = (
            "Shipment Invoice Processing (Sea + Air) + Portal Fee + Gate Validation"
        )

        # UnifiedRateLoader 초기화
        rate_dir = self.root.parent / "Rate"
        self.rate_loader = UnifiedRateLoader(rate_dir)
        self.rate_loader.load_all_rates()

        # PDF Integration 초기화
        if PDF_INTEGRATION_AVAILABLE:
            try:
                self.pdf_integration = InvoicePDFIntegration(
                    audit_system=self, config_path=None  # 기본 경로 사용
                )
                logging.info("✅ PDF Integration enabled")
            except Exception as e:
                self.pdf_integration = None
                logging.warning(f"⚠️ PDF Integration disabled: {e}")
        else:
            self.pdf_integration = None
            logging.warning("⚠️ PDF Integration not available")

        # Lane Map (해상 + 항공)
        self.lane_map = {
            "KP_DSV_YD": {
                "lane_id": "L01",
                "rate": 252.00,
                "route": "Khalifa Port→Storage Yard",
            },
            "DSV_YD_MIRFA": {
                "lane_id": "L38",
                "rate": 420.00,
                "route": "DSV Yard→MIRFA",
            },
            "DSV_YD_SHUWEIHAT": {
                "lane_id": "L44",
                "rate": 600.00,
                "route": "DSV Yard→SHUWEIHAT",
            },
            "MOSB_DSV_YD": {"lane_id": "L33", "rate": 200.00, "route": "MOSB→DSV Yard"},
            "AUH_DSV_MUSSAFAH": {
                "lane_id": "A01",
                "rate": 100.00,
                "route": "AUH Airport→DSV Mussafah",
            },
        }

        # COST-GUARD 밴드 (2% 기준)
        self.cost_guard_bands = {
            "PASS": {"max_delta": 2.00, "description": "≤2.00%"},
            "WARN": {"max_delta": 5.00, "description": "2.01-5.00%"},
            "HIGH": {"max_delta": 10.00, "description": "5.01-10.00%"},
            "CRITICAL": {"max_delta": float("inf"), "description": ">10.00%"},
        }

        # FX 고정 환율
        self.fx_rate = 3.6725  # 1 USD = 3.6725 AED

        # Portal Fee 설정 (Enhanced 기능)
        self.portal_fee_keywords = [
            "MAQTA",
            "APPOINTMENT",
            "APPT",
            "DPC",
            "DOCUMENT PROCESSING",
            "MANIFEST",
        ]
        self.portal_fee_tolerance = 0.005  # ±0.5%
        self.portal_fee_fixed_rates = {
            "APPOINTMENT": {"AED": 27.00, "USD": 7.35},
            "DPC": {"AED": 35.00, "USD": 9.53},
            "DOCUMENT PROCESSING": {"AED": 35.00, "USD": 9.53},
        }

        # 로깅 설정
        log_file = self.out_dir / "shpt_sept_2025_enhanced_audit.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

        logging.info(f"SHPT Enhanced 시스템 초기화 완료")
        logging.info(f"송장 파일: {self.excel_file}")

    # ==================== Portal Fee 검증 메서드 (Enhanced) ====================

    def is_portal_fee(self, rate_source: str, description: str) -> bool:
        """Portal Fee 여부 판별"""
        rs = (rate_source or "").upper()
        desc = (description or "").upper()
        return any(
            keyword in rs or keyword in desc for keyword in self.portal_fee_keywords
        )

    def parse_aed_from_formula(self, formula: str) -> Optional[float]:
        """수식에서 AED 금액 추출 (=27/3.6725 형식)"""
        if not formula:
            return None

        pattern = r"=\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*3\.6725"
        match = re.search(pattern, formula.replace(",", ""))
        return float(match.group(1)) if match else None

    def get_portal_fee_fixed_rate(self, description: str) -> Optional[Dict[str, float]]:
        """Portal Fee 고정값 조회"""
        desc_upper = (description or "").upper()

        for keyword, rates in self.portal_fee_fixed_rates.items():
            if keyword in desc_upper:
                return rates

        return None

    def portal_fee_band(self, delta_abs: float) -> str:
        """Portal Fee 전용 COST-GUARD 밴드 (±0.5% 기준)"""
        if delta_abs <= 0.005:  # ≤0.5%
            return "PASS"
        elif delta_abs <= 0.05:  # 0.5-5%
            return "WARN"
        elif delta_abs <= 0.10:  # 5-10%
            return "HIGH"
        else:
            return "CRITICAL"

    # ==================== Gate 검증 메서드 (핵심 3개) ====================

    def validate_gate_01_document_set(
        self, supporting_docs: List[Dict]
    ) -> Dict[str, Any]:
        """Gate-01: 문서세트 존재 검증"""
        required_docs = ["BOE", "DO", "DN"]
        found_docs = [doc.get("doc_type", "") for doc in supporting_docs]

        missing_docs = [doc for doc in required_docs if doc not in found_docs]

        return {
            "status": "PASS" if not missing_docs else "FAIL",
            "missing_docs": missing_docs,
            "score": max(0, 100 - len(missing_docs) * 25),
        }

    def validate_gate_07_total_consistency(self, item: Dict) -> Dict[str, Any]:
        """Gate-07: 합계 정합 검증"""
        rate = item.get("unit_rate", 0)
        quantity = item.get("quantity", 0)
        total = item.get("total_usd", 0)

        calculated_total = rate * quantity
        delta = abs(total - calculated_total)

        return {
            "status": "PASS" if delta < 0.01 else "FAIL",
            "calculated": calculated_total,
            "actual": total,
            "delta": delta,
            "score": max(0, 100 - delta * 100),
        }

    def run_key_gates(
        self, item: Dict, supporting_docs: List[Dict], pdf_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """핵심 Gate 검증 실행 (기존 + PDF Gates)"""
        gates = {
            "Gate_01": self.validate_gate_01_document_set(supporting_docs),
            "Gate_07": self.validate_gate_07_total_consistency(item),
        }

        # PDF Integration Gates 추가 (활성화 시)
        if pdf_data and self.pdf_integration:
            pdf_gates = self.pdf_integration.run_pdf_gates(item, pdf_data)

            # PDF Gate 결과를 기존 gates에 통합
            for gate_detail in pdf_gates.get("Gate_Details", []):
                gate_name = gate_detail["gate"]
                gates[gate_name] = {
                    "status": gate_detail["result"],
                    "score": gate_detail["score"],
                    "details": gate_detail["details"],
                }

        failed_gates = [
            name for name, result in gates.items() if result["status"] == "FAIL"
        ]
        total_score = sum(result["score"] for result in gates.values()) / len(gates)

        return {
            "Gate_Status": "PASS" if not failed_gates else "FAIL",
            "Gate_Fails": ",".join(failed_gates) if failed_gates else "",
            "Gate_Score": round(total_score, 1),
            "gates": gates,
        }

    # ==================== Excel 처리 메서드 ====================

    def load_invoice_sheets(self):
        """Excel 파일의 모든 시트 로드"""
        try:
            logging.info(f"📂 송장 파일 로드 중: {self.excel_file.name}")

            if not self.excel_file.exists():
                logging.error(f"[ERROR] File not found: {self.excel_file}")
                return None

            excel_file = pd.ExcelFile(self.excel_file, engine="openpyxl")

            logging.info(f"[OK] File loaded successfully")
            logging.info(f"📊 총 시트 수: {len(excel_file.sheet_names)}")

            return excel_file

        except Exception as e:
            logging.error(f"[ERROR] File load error: {e}")
            return None

    def extract_invoice_items(self, df, sheet_name):
        """시트에서 송장 항목 추출 (run_sept_2025_audit.py 검증된 로직 사용)"""
        items = []

        try:
            # S/No 컬럼 찾기
            header_row = None
            for idx, row in df.iterrows():
                row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
                if "S/No" in row_str or "S/NO" in row_str.upper():
                    header_row = idx
                    break

            if header_row is None:
                return items

            # 헤더 설정
            df.columns = df.iloc[header_row]
            df = df[header_row + 1 :].reset_index(drop=True)

            # 데이터 추출
            for idx, row in df.iterrows():
                try:
                    s_no = str(row.get("S/No", row.get("S/NO", ""))).strip()

                    if not s_no or s_no == "nan":
                        continue

                    if "TOTAL" in s_no.upper():
                        break

                    description = str(
                        row.get("DESCRIPTION", row.get("Description", ""))
                    ).strip()
                    if not description or description == "nan":
                        continue

                    rate_source = str(
                        row.get("RATE SOURCE", row.get("Rate Source", ""))
                    ).strip()

                    rate_col = row.get("RATE", row.get("Rate", row.get("UNIT RATE", 0)))
                    rate = (
                        float(str(rate_col).replace(",", ""))
                        if pd.notna(rate_col)
                        else 0
                    )

                    qty_col = row.get(
                        "Q'TY", row.get("QTY", row.get("Qty", row.get("QUANTITY", 1)))
                    )
                    qty = (
                        float(str(qty_col).replace(",", "")) if pd.notna(qty_col) else 1
                    )

                    total_col = row.get(
                        "TOTAL (USD)", row.get("Total (USD)", row.get("AMOUNT", 0))
                    )
                    total = (
                        float(str(total_col).replace(",", ""))
                        if pd.notna(total_col)
                        else 0
                    )

                    formula_col = row.get("FORMULA", row.get("Formula", ""))
                    formula = str(formula_col).strip() if pd.notna(formula_col) else ""

                    remark = str(row.get("REMARK", row.get("Remark", ""))).strip()

                    item = {
                        "sheet_name": sheet_name,
                        "s_no": s_no,
                        "description": description,
                        "rate_source": rate_source,
                        "unit_rate": rate,
                        "quantity": qty,
                        "total_usd": total,
                        "formula_text": formula,
                        "remark": remark,
                    }

                    items.append(item)

                except Exception as e:
                    logging.debug(f"행 추출 오류 ({sheet_name}, 행 {idx}): {e}")
                    continue

            logging.info(f"  [OK] {sheet_name}: {len(items)} items extracted")

        except Exception as e:
            logging.error(f"  [ERROR] {sheet_name} extraction error: {e}")

        return items

    def validate_enhanced_item(self, item: Dict, supporting_docs: List[Dict]) -> Dict:
        """Enhanced 송장 항목 검증 (Portal Fee + Gate 포함)"""
        validation = {
            "s_no": item["s_no"],
            "sheet_name": item["sheet_name"],
            "description": item["description"],
            "rate_source": item["rate_source"],
            "unit_rate": item["unit_rate"],
            "quantity": item["quantity"],
            "total_usd": item["total_usd"],
            "status": "PASS",
            "flag": "OK",
            "delta_pct": 0.0,
            "cg_band": "PASS",
            "charge_group": "Other",
            "issues": [],
            "tolerance": 0.03,  # 기본 3%
            "ref_rate_usd": None,
            "doc_aed": None,
        }

        try:
            # 1. 금액 계산 검증
            expected_total = round(item["unit_rate"] * item["quantity"], 2)
            if abs(expected_total - item["total_usd"]) > 0.01:
                validation["issues"].append(
                    f"금액 불일치: 예상 {expected_total}, 실제 {item['total_usd']}"
                )
                validation["flag"] = "WARN"

            # 2. Rate Source 분류
            rate_source_upper = item["rate_source"].upper()
            desc_upper = item["description"].upper()

            # Portal Fee 판별 (Enhanced)
            if self.is_portal_fee(item["rate_source"], item["description"]):
                validation["charge_group"] = "PortalFee"
                validation["tolerance"] = self.portal_fee_tolerance  # ±0.5%

                # AED 수식 파싱
                doc_aed = self.parse_aed_from_formula(item["formula_text"])

                # 고정값 테이블 조회
                if doc_aed is None:
                    fixed_rate = self.get_portal_fee_fixed_rate(item["description"])
                    if fixed_rate:
                        doc_aed = fixed_rate["AED"]

                # AED → USD 환산
                if doc_aed is not None:
                    validation["doc_aed"] = doc_aed
                    validation["ref_rate_usd"] = round(doc_aed / self.fx_rate, 2)

                    # Delta % 계산 (Portal Fee)
                    if validation["ref_rate_usd"] > 0:
                        delta_pct = (
                            (item["unit_rate"] - validation["ref_rate_usd"])
                            / validation["ref_rate_usd"]
                        ) * 100
                        validation["delta_pct"] = round(delta_pct, 2)
                        validation["cg_band"] = self.portal_fee_band(
                            abs(delta_pct / 100)
                        )

                        # Status 결정 (±0.5% 기준)
                        if abs(delta_pct) <= 0.5:
                            validation["status"] = "PASS"
                            validation["flag"] = "OK"
                        elif abs(delta_pct) <= 5.0:
                            validation["status"] = "REVIEW"
                            validation["flag"] = "WARN"
                        else:
                            validation["status"] = "FAIL"
                            validation["flag"] = "CRITICAL"

            elif "CONTRACT" in rate_source_upper:
                validation["charge_group"] = "Contract"

                # Contract 항목 ref_rate 조회
                ref_rate = self._find_contract_ref_rate(item)
                if ref_rate is not None:
                    validation["ref_rate_usd"] = ref_rate

                    # Delta % 계산
                    delta_pct = self.rate_loader.calculate_delta_percent(
                        item["unit_rate"], ref_rate
                    )
                    validation["delta_pct"] = delta_pct

                    # COST-GUARD 밴드 결정
                    cg_band = self.rate_loader.get_cost_guard_band(delta_pct)
                    validation["cg_band"] = cg_band

                    # 상태 업데이트 (Delta가 크면 FAIL)
                    if abs(delta_pct) > 5.0:  # WARN 초과
                        validation["status"] = "FAIL"
                        validation["flag"] = (
                            "HIGH" if abs(delta_pct) <= 10.0 else "CRITICAL"
                        )
                        validation["issues"].append(
                            f"Contract 과다/과소 청구: Delta {delta_pct:.2f}% (Ref: ${ref_rate})"
                        )

            elif "AT COST" in rate_source_upper or "AT-COST" in rate_source_upper:
                validation["charge_group"] = "AtCost"
            else:
                validation["charge_group"] = "Other"

            # 3. Gate 검증 실행
            gate_result = self.run_key_gates(item, supporting_docs)
            validation["gate_status"] = gate_result["Gate_Status"]
            validation["gate_score"] = gate_result["Gate_Score"]
            validation["gate_fails"] = gate_result["Gate_Fails"]

            # 4. 최종 상태 결정
            if not validation["issues"] and validation["gate_status"] == "PASS":
                validation["status"] = "PASS"
            elif validation["issues"] or validation["gate_status"] == "FAIL":
                if validation["status"] != "FAIL":
                    validation["status"] = "REVIEW_NEEDED"

        except Exception as e:
            validation["status"] = "ERROR"
            validation["flag"] = "ERROR"
            validation["issues"].append(f"검증 오류: {e}")

        return validation

    def _find_contract_ref_rate(self, item: Dict) -> Optional[float]:
        """
        Contract 항목의 참조 요율 조회

        Args:
            item: Invoice 항목

        Returns:
            참조 요율 (USD) 또는 None
        """
        description = item.get("description", "").strip()
        desc_upper = description.upper()

        # 1. Standard Items 조회 시도
        # MASTER DO FEE, CUSTOMS CLEARANCE, TERMINAL HANDLING 등
        standard_keywords = [
            ("DO FEE", "DO Fee"),
            ("MASTER DO", "DO Fee"),
            ("CUSTOMS CLEARANCE", "Custom Clearance"),
            ("CUSTOM CLEARANCE", "Custom Clearance"),
            ("TERMINAL HANDLING FEE", "Terminal Handling Charge"),
            ("TERMINAL HANDLING CHARGE", "Terminal Handling Charge"),
            ("TERMINAL HANDLING", "Terminal Handling Charge"),
            ("PORT HANDLING", "Port Handling Charge"),
            ("THC", "Terminal Handling Charge"),
        ]

        for keyword_match, keyword_lookup in standard_keywords:
            if keyword_match in desc_upper:
                # Port 추출 시도 (description 또는 기본값)
                port = self._extract_port_from_description(description)
                if not port:
                    port = "Khalifa Port"  # 기본값

                # Terminal Handling의 경우 container type에 따라 다름
                if "TERMINAL HANDLING" in keyword_match or keyword_match == "THC":
                    # Container type 추출 (20DC, 40HC, KG 단위 등)
                    if "20DC" in desc_upper or "20FT" in desc_upper:
                        return 372.00  # Khalifa Port standard
                    elif "40HC" in desc_upper or "40FT" in desc_upper:
                        return 479.00  # Khalifa Port standard
                    elif "KG" in desc_upper or "CW:" in desc_upper:
                        return 0.55  # Abu Dhabi Airport per KG

                # Rate Loader로 조회
                ref_rate = self.rate_loader.get_standard_rate(keyword_lookup, port)
                if ref_rate is not None:
                    return ref_rate

        # 2. Inland Trucking (Transportation) 조회 시도
        if "TRANSPORTATION" in desc_upper or "TRUCKING" in desc_upper:
            # Description에서 Port와 Destination 파싱
            port, destination = self._parse_transportation_route(description)

            if port and destination:
                # Lane rate 조회
                ref_rate = self.rate_loader.get_lane_rate(
                    port, destination, "per truck"
                )
                if ref_rate is not None:
                    return ref_rate

            # 파싱 실패 시 Lane Map 폴백
            if "KHALIFA PORT" in desc_upper and (
                "STORAGE" in desc_upper or "DSV" in desc_upper or "YARD" in desc_upper
            ):
                return 252.00
            elif (
                "DSV" in desc_upper and "KHALIFA" in desc_upper
            ):  # DSV → KHALIFA (EMPTY RETURN)
                return 252.00
            elif "AUH AIRPORT" in desc_upper and "MOSB" in desc_upper:
                if "3 TON PU" in desc_upper or "3T" in desc_upper:
                    return 100.00  # AUH → MOSB (3T PU)
                else:
                    return 200.00  # AUH → MOSB (FB)
            elif "MIRFA" in desc_upper:
                return 420.00
            elif "SHUWEIHAT" in desc_upper or "SHU" in desc_upper:
                return 600.00

        return None

    def _extract_port_from_description(self, description: str) -> Optional[str]:
        """Description에서 Port 이름 추출"""
        desc_upper = description.upper()

        if "KHALIFA" in desc_upper or "KP" in desc_upper:
            return "Khalifa Port"
        elif "JEBEL ALI" in desc_upper or "JAP" in desc_upper:
            return "Jebel Ali Port"
        elif "ABU DHABI AIRPORT" in desc_upper or "AUH" in desc_upper:
            return "Abu Dhabi Airport"
        elif "DUBAI AIRPORT" in desc_upper or "DXB" in desc_upper:
            return "Dubai Airport"

        return None

    def _parse_transportation_route(
        self, description: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Transportation description에서 Port와 Destination 파싱

        예: "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD"

        Returns:
            (port, destination) 튜플
        """
        desc_upper = description.upper()

        # FROM ... TO ... 패턴
        import re

        match = re.search(r"FROM\s+(.+?)\s+TO\s+(.+)", desc_upper)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()

            # 정규화
            port = self._extract_port_from_description(origin)
            dest = self._normalize_destination(destination)

            return (port, dest)

        return (None, None)

    def _normalize_destination(self, destination: str) -> Optional[str]:
        """Destination 정규화"""
        dest_upper = destination.upper()

        if "MIRFA" in dest_upper:
            return "MIRFA SITE"
        elif "SHUWEIHAT" in dest_upper or "SHU" in dest_upper:
            return "SHUWEIHAT Site"
        elif "STORAGE" in dest_upper or "YARD" in dest_upper or "DSV" in dest_upper:
            return "Storage Yard"

        return destination

    def map_supporting_documents(self) -> Dict[str, List[Dict]]:
        """증빙문서 매핑 생성"""
        supporting_docs = {}

        for docs_path in self.supporting_docs_paths:
            if not docs_path.exists():
                logging.warning(f"⚠️ 증빙문서 폴더 없음: {docs_path}")
                continue

            try:
                pdf_files = list(docs_path.rglob("*.pdf"))
                logging.info(f"[DOCS] {docs_path.name}: {len(pdf_files)} PDFs found")

                for pdf_file in pdf_files:
                    # 파일명에서 Shipment ID 추출
                    shipment_id = self.extract_shipment_id(pdf_file.name)

                    if shipment_id:
                        if shipment_id not in supporting_docs:
                            supporting_docs[shipment_id] = []

                        doc_type = self.extract_doc_type(pdf_file.name)

                        supporting_docs[shipment_id].append(
                            {
                                "file_name": pdf_file.name,
                                "file_path": str(pdf_file),
                                "doc_type": doc_type,
                                "file_size": pdf_file.stat().st_size,
                            }
                        )

            except Exception as e:
                logging.error(f"증빙문서 매핑 오류: {e}")

        logging.info(
            f"[OK] Total {len(supporting_docs)} shipment supporting documents mapped"
        )
        return supporting_docs

    def extract_shipment_id(self, filename: str) -> Optional[str]:
        """파일명에서 Shipment ID 추출 (개선)"""
        if "HVDC-ADOPT-" in filename:
            # HVDC-ADOPT-SCT-0126_BOE.pdf 형식
            parts = filename.split("_")
            if parts:
                # 첫 번째 부분이 Shipment ID
                shipment_id = parts[0]
                # 추가 정제: .pdf 제거 등
                shipment_id = shipment_id.replace(".pdf", "")
                return shipment_id
        elif "HVDC-" in filename:
            parts = filename.split("_")
            return parts[0] if parts else None
        return None

    def extract_doc_type(self, filename: str) -> str:
        """파일명에서 문서 타입 추출"""
        fn_upper = filename.upper()
        if "BOE" in fn_upper:
            return "BOE"
        elif "DO" in fn_upper and "DN" not in fn_upper:
            return "DO"
        elif "DN" in fn_upper:
            return "DN"
        elif "CARRIER" in fn_upper or "INVOICE" in fn_upper:
            return "CarrierInvoice"
        else:
            return "Other"

    # ==================== 메인 감사 실행 ====================

    def run_full_enhanced_audit(self):
        """전체 Enhanced 감사 실행"""
        try:
            logging.info("=" * 80)
            logging.info("[START] SHPT Enhanced Sept 2025 full audit")
            logging.info("=" * 80)

            # 1. Excel 파일 로드
            excel_file = self.load_invoice_sheets()
            if excel_file is None:
                return None

            # 2. 증빙문서 매핑
            supporting_docs = self.map_supporting_documents()

            # 3. 모든 시트 처리
            all_items = []
            sheet_summary = []

            logging.info("\n📋 시트별 송장 항목 추출 및 검증 중...\n")

            for sheet_name in excel_file.sheet_names:
                if sheet_name.startswith("_") or sheet_name in [
                    "Summary",
                    "Template",
                    "SEPT",
                ]:
                    continue

                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    items = self.extract_invoice_items(df, sheet_name)

                    if items:
                        # 각 항목 검증 - 시트명에서 Shipment ID 올바르게 추출
                        if sheet_name.startswith("SCT"):
                            shipment_id = f"HVDC-ADOPT-SCT-{sheet_name[3:]}"  # SCT0126 → HVDC-ADOPT-SCT-0126
                        elif sheet_name.startswith("HE"):
                            shipment_id = f"HVDC-ADOPT-HE-{sheet_name[2:]}"  # HE0471 → HVDC-ADOPT-HE-0471
                        elif sheet_name.startswith("SIM"):
                            shipment_id = f"HVDC-ADOPT-SIM-{sheet_name[3:]}"  # SIM0092 → HVDC-ADOPT-SIM-0092
                        else:
                            shipment_id = f"HVDC-ADOPT-{sheet_name}"

                        sheet_docs = supporting_docs.get(shipment_id, [])

                        # PDF 파싱 및 검증 (통합 활성화 시)
                        pdf_validation_data = None
                        if self.pdf_integration and sheet_docs:
                            try:
                                pdf_parse_result = (
                                    self.pdf_integration.parse_supporting_docs(
                                        shipment_id, sheet_docs
                                    )
                                )
                                pdf_validation_data = pdf_parse_result
                                logging.debug(
                                    f"  [PDF] {shipment_id}: Parsed {pdf_parse_result['parsed_count']} docs"
                                )
                            except Exception as e:
                                logging.warning(
                                    f"  [PDF] {shipment_id} parsing failed: {e}"
                                )

                        for item in items:
                            validation = self.validate_enhanced_item(item, sheet_docs)

                            # PDF 검증 통합
                            if pdf_validation_data and self.pdf_integration:
                                try:
                                    enriched = (
                                        self.pdf_integration.validate_invoice_with_docs(
                                            item, shipment_id, sheet_docs
                                        )
                                    )

                                    # PDF 검증 정보 병합
                                    validation["pdf_validation"] = enriched.get(
                                        "pdf_validation", {}
                                    )
                                    validation["demurrage_risk"] = enriched.get(
                                        "demurrage_risk"
                                    )

                                    # PDF Gates 실행 (Gate-11~14)
                                    pdf_gates_result = (
                                        self.pdf_integration.run_pdf_gates(
                                            item, pdf_validation_data
                                        )
                                    )

                                    # Gate 점수 업데이트 (기존 Gate + PDF Gates 통합)
                                    if pdf_gates_result:
                                        existing_gates = validation.get("gates", {})

                                        # PDF Gates 추가
                                        for gate_detail in pdf_gates_result.get(
                                            "Gate_Details", []
                                        ):
                                            gate_name = gate_detail["gate"]
                                            existing_gates[gate_name] = {
                                                "status": gate_detail["result"],
                                                "score": gate_detail["score"],
                                                "details": gate_detail["details"],
                                            }

                                        # 전체 Gate 점수 재계산
                                        all_gates = list(existing_gates.values())
                                        avg_score = (
                                            sum(g["score"] for g in all_gates)
                                            / len(all_gates)
                                            if all_gates
                                            else 0
                                        )
                                        fails = [
                                            name
                                            for name, g in existing_gates.items()
                                            if g["status"] == "FAIL"
                                        ]

                                        validation["gate_score"] = round(avg_score, 1)
                                        validation["gate_status"] = (
                                            "FAIL" if fails else "PASS"
                                        )
                                        validation["gate_fails"] = ",".join(fails)
                                        validation["gates"] = existing_gates

                                except Exception as e:
                                    logging.warning(
                                        f"  [PDF] PDF validation failed for item {item.get('s_no')}: {e}"
                                    )

                            # 증빙문서 정보 추가
                            validation["supporting_docs_list"] = sheet_docs
                            validation["evidence_count"] = len(sheet_docs)
                            validation["evidence_types"] = list(
                                set(doc["doc_type"] for doc in sheet_docs)
                            )
                            all_items.append(validation)

                        sheet_summary.append(
                            {
                                "sheet_name": sheet_name,
                                "item_count": len(items),
                                "supporting_docs": len(sheet_docs),
                                "shipment_id": shipment_id,
                            }
                        )

                except Exception as e:
                    logging.error(f"  [ERROR] {sheet_name} processing error: {e}")

            logging.info(
                f"\n[OK] Total {len(all_items)} items extracted and validated from {len(sheet_summary)} sheets"
            )

            # 4. 통계 계산
            total_items = len(all_items)
            pass_items = len([item for item in all_items if item["status"] == "PASS"])
            review_items = len(
                [
                    item
                    for item in all_items
                    if item["status"] == "REVIEW_NEEDED" or item["status"] == "REVIEW"
                ]
            )
            error_items = len([item for item in all_items if item["status"] == "ERROR"])
            fail_items = len([item for item in all_items if item["status"] == "FAIL"])

            portal_fee_items = len(
                [item for item in all_items if item["charge_group"] == "PortalFee"]
            )
            contract_items = len(
                [item for item in all_items if item["charge_group"] == "Contract"]
            )
            at_cost_items = len(
                [item for item in all_items if item["charge_group"] == "AtCost"]
            )

            total_amount = sum(item["total_usd"] for item in all_items)

            gate_pass_items = len(
                [item for item in all_items if item.get("gate_status") == "PASS"]
            )
            avg_gate_score = (
                sum(item.get("gate_score", 0) for item in all_items) / total_items
                if total_items > 0
                else 0
            )

            # 5. 결과 생성
            audit_result = {
                "audit_info": {
                    "invoice_file": self.excel_file.name,
                    "audit_date": datetime.now().isoformat(),
                    "system_type": self.system_type,
                    "scope": self.scope,
                    "supporting_docs_paths": [
                        str(p) for p in self.supporting_docs_paths
                    ],
                    "total_supporting_docs": sum(
                        len(pdfs) for pdfs in supporting_docs.values()
                    ),
                },
                "statistics": {
                    "total_sheets": len(sheet_summary),
                    "total_items": total_items,
                    "pass_items": pass_items,
                    "review_items": review_items,
                    "fail_items": fail_items,
                    "error_items": error_items,
                    "pass_rate": (
                        f"{(pass_items/total_items*100):.1f}%"
                        if total_items > 0
                        else "0%"
                    ),
                    "total_amount_usd": total_amount,
                    "charge_group_breakdown": {
                        "Contract": contract_items,
                        "AtCost": at_cost_items,
                        "PortalFee": portal_fee_items,
                        "Other": total_items
                        - contract_items
                        - at_cost_items
                        - portal_fee_items,
                    },
                    "gate_validation": {
                        "gate_pass_items": gate_pass_items,
                        "gate_pass_rate": (
                            f"{(gate_pass_items/total_items*100):.1f}%"
                            if total_items > 0
                            else "0%"
                        ),
                        "avg_gate_score": round(avg_gate_score, 1),
                    },
                },
                "supporting_docs": supporting_docs,
                "sheet_summary": sheet_summary,
                "items": all_items,
            }

            # 6. VBA 결과 통합 (Excel 포맷팅 없음)
            try:
                from vba_result_reader import (
                    VBAResultReader,
                    integrate_vba_results,
                    detect_calculation_mismatch,
                )

                vba_reader = VBAResultReader()
                vba_master_data = vba_reader.read_master_data(str(self.excel_file))

                if not vba_master_data.empty:
                    logging.info(
                        f"\n📊 VBA MasterData 로드: {len(vba_master_data)} rows"
                    )

                    # Python 결과를 DataFrame으로 변환
                    python_df = pd.DataFrame(all_items)

                    # VBA 결과 병합
                    merged_df = integrate_vba_results(python_df, vba_master_data)

                    # 불일치 감지
                    mismatches = detect_calculation_mismatch(merged_df)

                    if mismatches:
                        logging.warning(
                            f"⚠️ VBA-Python 계산 불일치 {len(mismatches)}건 발견"
                        )

                    # 병합된 결과를 all_items에 반영
                    all_items = merged_df.to_dict("records")
                    audit_result["items"] = all_items

                    # 통계에 VBA 정보 추가
                    audit_result["vba_integration"] = {
                        "enabled": True,
                        "master_data_rows": len(vba_master_data),
                        "calculation_mismatches": len(mismatches),
                        "mismatch_details": mismatches,
                    }

                    logging.info(f"✅ VBA 결과 통합 완료 (포맷팅 제외)")
                else:
                    logging.warning(
                        "⚠️ VBA MasterData 로드 실패 - VBA 통합 건너뜀"
                    )

            except ImportError:
                logging.warning("VBA 통합 모듈 없음 - VBA 통합 건너뜀")
            except Exception as e:
                logging.error(f"VBA 통합 중 오류: {e}")

            # 7. 결과 저장
            self.save_enhanced_results(audit_result)

            # 8. 결과 출력
            self.print_enhanced_summary(audit_result)

            return audit_result

        except Exception as e:
            logging.error(f"[ERROR] Full audit error: {e}")
            import traceback

            logging.error(traceback.format_exc())
            return None

    def save_enhanced_results(self, audit_result):
        """Enhanced 감사 결과 저장 (Excel 종합 보고서만 생성)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # ✅ Excel 종합 보고서 생성 (6개 시트 포함)
            try:
                from safe_excel_report_generator import SafeExcelReportGenerator

                excel_file = (
                    self.out_dir
                    / "Reports"
                    / f"SHPT_SEPT_2025_FINAL_REPORT_{timestamp}.xlsx"
                )
                excel_file.parent.mkdir(parents=True, exist_ok=True)

                generator = SafeExcelReportGenerator()
                if generator.create_multi_sheet_report(audit_result, str(excel_file)):
                    logging.info(
                        f"\n📊 ✅ Excel 종합 보고서 생성 완료: {excel_file}"
                    )
                    logging.info(f"   - 6개 시트 포함 (요약, 상세, Gate, PDF, VBA, PASS)")
                    logging.info(f"   - VBA 통합 결과 포함")
                    logging.info(f"   - PDF 검증 결과 포함")
                    logging.info(f"   - 포맷팅 없음 (안정적)")
                else:
                    logging.warning("Excel 종합 보고서 생성 실패")

            except ImportError as e:
                logging.error(f"SafeExcelReportGenerator 모듈 없음: {e}")
            except Exception as e:
                logging.error(f"Excel 보고서 생성 중 오류: {e}")

            # ⚠️ MD/CSV/TXT 생성 중단 (사용자 요청: Excel만 필요)
            # Excel 종합 보고서가 유일한 출력물

            # 임시: JSON만 백업용으로 저장 (시스템 호환성 유지)
            json_file = (
                self.out_dir
                / "JSON"
                / f"shpt_sept_2025_enhanced_result_{timestamp}.json"
            )
            json_file.parent.mkdir(parents=True, exist_ok=True)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False)

            logging.info(f"💾 (백업용) JSON 저장: {json_file}")
            logging.info(f"\n✅ 주 출력물: Excel 종합 보고서 (6개 시트)")
            logging.info(f"⚠️ MD/CSV/TXT 파일 생성 중단됨 (Excel만 필요)")

        except Exception as e:
            logging.error(f"[ERROR] Result save error: {e}")

    def print_enhanced_summary(self, audit_result):
        """Enhanced 결과 요약 출력"""
        logging.info("\n" + "=" * 80)
        logging.info("📊 SHPT Enhanced 감사 결과 요약")
        logging.info("=" * 80)

        stats = audit_result["statistics"]
        logging.info(f"\n총 시트 수: {stats['total_sheets']}")
        logging.info(f"총 항목 수: {stats['total_items']}")
        logging.info(f"PASS: {stats['pass_items']} ({stats['pass_rate']})")
        logging.info(f"검토 필요: {stats['review_items']}")
        logging.info(f"FAIL: {stats['fail_items']}")
        logging.info(f"총 금액: ${stats['total_amount_usd']:,.2f} USD")

        logging.info("\n📋 Charge Group 분석:")
        cg = stats["charge_group_breakdown"]
        logging.info(f"  - Contract: {cg['Contract']}개")
        logging.info(f"  - AtCost: {cg['AtCost']}개")
        logging.info(f"  - PortalFee: {cg['PortalFee']}개 ← Enhanced 기능")
        logging.info(f"  - Other: {cg['Other']}개")

        logging.info("\n🚪 Gate 검증 결과:")
        gate = stats["gate_validation"]
        logging.info(
            f"  - Gate PASS: {gate['gate_pass_items']}개 ({gate['gate_pass_rate']})"
        )
        logging.info(f"  - 평균 Gate Score: {gate['avg_gate_score']}")

        logging.info("\n📋 시트별 항목 수:")
        for sheet in audit_result["sheet_summary"]:
            logging.info(f"  - {sheet['sheet_name']}: {sheet['item_count']}개")

        logging.info("\n" + "=" * 80)
        logging.info("[COMPLETE] SHPT Enhanced audit finished!")
        logging.info("=" * 80)


def main():
    """메인 실행 함수"""
    print("[SHPT Enhanced] Sept 2025 Invoice Audit System")
    print("=" * 80)

    auditor = SHPTSept2025EnhancedAuditSystem()
    result = auditor.run_full_enhanced_audit()

    if result:
        logging.info("\n[SUCCESS] Enhanced audit completed successfully.")
        logging.info(f"[SAVED] Results saved to Results/Sept_2025 directory.")

        # Portal Fee 항목 상세 출력
        portal_fee_items = [
            item for item in result["items"] if item["charge_group"] == "PortalFee"
        ]
        if portal_fee_items:
            logging.info(f"\n[PORTAL FEE] {len(portal_fee_items)} items:")
            for pf_item in portal_fee_items[:5]:  # 최대 5개만 출력
                logging.info(f"  - {pf_item['description']}")
                logging.info(f"    Draft: ${pf_item['unit_rate']:.2f}")
                if pf_item["doc_aed"]:
                    logging.info(f"    Doc AED: {pf_item['doc_aed']}")
                    logging.info(f"    Ref USD: ${pf_item['ref_rate_usd']:.2f}")
                logging.info(f"    Delta: {pf_item['delta_pct']:.2f}%")
                logging.info(f"    Tolerance: +/-{pf_item['tolerance']*100}%")
                logging.info(f"    Status: {pf_item['status']}")
    else:
        logging.error("\n[ERROR] Enhanced audit failed")


if __name__ == "__main__":
    main()
