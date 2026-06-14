#!/usr/bin/env python3
"""
MasterData Validator
VBA 생성 MasterData를 입력으로 받아 Python 검증 결과를 컬럼으로 추가

Version: 2.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import sys
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Configuration Manager import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from config_manager import ConfigurationManager
from category_normalizer import CategoryNormalizer
from cost_guard import get_cost_guard_band, check_auto_fail
from formula_parser import parse_rate_from_formula_or_fixed, KNOWN_AED_RATES

# PDF Integration import
try:
    from pdf_integration import (
        DSVPDFParser,
        CrossDocValidator,
        OntologyMapper,
        WorkflowAutomator,
    )

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MasterDataValidator:
    """MasterData 검증 시스템 (Configuration + PDF 통합)"""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.rate_dir = self.root.parent / "Rate"

        # Configuration Manager 초기화
        self.config_manager = ConfigurationManager(self.rate_dir)
        self.config_manager.load_all_configs()

        # Category Normalizer 초기화
        self.normalizer = CategoryNormalizer()

        logger.info(
            f"Configuration Manager loaded: {self.config_manager.get_config_summary()['lanes_loaded']} lanes"
        )
        logger.info(
            f"Category Normalizer loaded: {len(self.normalizer.get_synonym_map())} synonyms"
        )

        # Excel 파일 경로
        self.excel_file = (
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
        )

        # Supporting Documents 경로
        self.supporting_docs_path = (
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT Import (Sept 2025) - Supporting Documents"
        )

        # Configuration 데이터 로드
        self.lane_map = self.config_manager.get_lane_map()
        self.cost_guard_bands = self.config_manager.get_cost_guard_bands()
        self.fx_rate = self.config_manager.get_fx_rate("USD", "AED")

        # Hybrid System Feature Flag
        self.use_hybrid = os.getenv("USE_HYBRID", "false").lower() == "true"

        # Hybrid System 초기화 (우선)
        if self.use_hybrid:
            try:
                from hybrid_client import HybridDocClient

                sys.path.insert(
                    0, str(Path(__file__).parent.parent.parent / "00_Shared")
                )
                from unified_ir_adapter import UnifiedIRAdapter

                self.hybrid_client = HybridDocClient("http://localhost:8080")
                self.ir_adapter = UnifiedIRAdapter()
                self.pdf_integration = None  # Disable legacy
                logger.info("✅ Hybrid System enabled (Docling + ADE)")

            except Exception as e:
                logger.warning(
                    f"Hybrid System init failed: {e}. Using IR-Lite fallback."
                )
                self.use_hybrid = False
                self.hybrid_client = None
                self.ir_adapter = None
                logger.warning("⚠️ UnifiedIRAdapter not available")

        # Legacy PDF Integration (Fallback)
        if not self.use_hybrid:
            # IR-Lite Fallback을 위해 UnifiedIRAdapter 초기화
            try:
                from unified_ir_adapter import UnifiedIRAdapter
                self.ir_adapter = UnifiedIRAdapter()
                logger.info("✅ UnifiedIRAdapter loaded for IR-Lite fallback")
            except Exception as e:
                self.ir_adapter = None
                logger.warning(f"⚠️ UnifiedIRAdapter not available: {e}")
            
            if PDF_AVAILABLE:
                try:
                    from invoice_pdf_integration import InvoicePDFIntegration

                    self.pdf_integration = InvoicePDFIntegration()
                    logger.info("ℹ️ Using legacy PDF integration")
                except Exception as e:
                    self.pdf_integration = None
                    logger.warning(f"PDF Integration not available: {e}")
            else:
                self.pdf_integration = None

        # PDF 캐시
        self.pdf_cache = {}

        # SEPT 시트에서 Mode 정보 로드 (Transport Mode 식별 개선)
        try:
            sept_df = pd.read_excel(self.excel_file, sheet_name="SEPT")
            self.mode_lookup = dict(zip(sept_df["Shpt Ref"], sept_df["Mode"]))
            self.pol_pod_lookup = dict(
                zip(sept_df["Shpt Ref"], zip(sept_df["POL"], sept_df["POD"]))
            )
            logger.info(
                f"SEPT Mode information loaded: {len(self.mode_lookup)} shipments"
            )
        except Exception as e:
            logger.warning(
                f"Could not load SEPT sheet: {e}. Falling back to pattern-based mode detection."
            )
            self.mode_lookup = {}
            self.pol_pod_lookup = {}

    def load_masterdata(self) -> pd.DataFrame:
        """MasterData 시트 로드"""

        logger.info(f"Loading MasterData from: {self.excel_file.name}")
        df = pd.read_excel(self.excel_file, sheet_name="MasterData")

        logger.info(f"MasterData loaded: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    def classify_charge_group(self, rate_source: str, description: str) -> str:
        """Charge Group 분류"""

        if pd.isna(rate_source):
            return "Other"

        rate_source_upper = str(rate_source).upper()
        desc_upper = str(description).upper()

        # Portal Fee 분류
        portal_keywords = [
            "APPOINTMENT",
            "DPC",
            "DOCUMENT PROCESSING",
            "ADMIN FEE",
            "PROCESSING FEE",
        ]
        if any(kw in desc_upper for kw in portal_keywords):
            return "PortalFee"

        # Contract 분류
        if "CONTRACT" in rate_source_upper:
            return "Contract"

        # AtCost 분류
        if "AT COST" in rate_source_upper or "COST" in rate_source_upper:
            return "AtCost"

        return "Other"

    def _identify_transport_mode(self, row: pd.Series) -> str:
        """Transport Mode 식별 (SEPT Mode 우선)"""

        order_ref = str(row.get("Order Ref. Number", ""))

        # Priority 1: SEPT 시트의 Mode 정보 (가장 정확!)
        if order_ref in self.mode_lookup:
            mode = self.mode_lookup[order_ref]
            if mode == "AIR":
                return "AIR"
            elif mode in ["FCL", "LCL"]:
                return "CONTAINER"

        # Priority 2: Order Ref 패턴 (Fallback)
        order_ref_upper = order_ref.upper()
        if "HE" in order_ref_upper or "-HE-" in order_ref_upper:
            return "AIR"
        elif "SCT" in order_ref_upper or "-SCT-" in order_ref_upper:
            return "CONTAINER"

        # Priority 3: DESCRIPTION 키워드 (Fallback)
        description = str(row.get("DESCRIPTION", "")).upper()
        air_keywords = ["AIR", "AIRPORT", "FLIGHT", "AUH AIRPORT", "DUBAI AIRPORT"]
        container_keywords = [
            "CONTAINER",
            "CNT",
            "20DC",
            "20FT",
            "40HC",
            "40FT",
            "40DC",
        ]

        if any(kw in description for kw in air_keywords):
            return "AIR"
        elif any(kw in description for kw in container_keywords):
            return "CONTAINER"

        # Default: CONTAINER
        return "CONTAINER"

    def find_contract_ref_rate(
        self, description: str, rate_source: str, row: pd.Series = None
    ) -> Optional[float]:
        """참조 요율 결정 (고정 요율 우선)"""

        if pd.isna(description):
            return None

        desc_upper = str(description).upper()

        # Priority 1: 고빈도 고정 요율
        # DO FEE 처리
        if any(kw in desc_upper for kw in ["MASTER DO FEE", "DO FEE"]):
            transport_mode = self._identify_transport_mode(row)
            return self.config_manager.get_do_fee(transport_mode)

        # CUSTOMS CLEARANCE 처리
        if any(
            kw in desc_upper
            for kw in ["CUSTOMS CLEARANCE", "CUSTOM CLEARANCE", "CLEARANCE FEE"]
        ):
            return self.config_manager.get_customs_clearance_fee()

        # Portal Fees 처리 (Config 우선 - PDF보다 먼저)
        if "APPOINTMENT FEE" in desc_upper or "TRUCK APPOINTMENT" in desc_upper:
            return self.config_manager.get_portal_fee_rate("APPOINTMENT_FEE", "USD")

        if "DPC FEE" in desc_upper:
            return self.config_manager.get_portal_fee_rate("DPC_FEE", "USD")

        if "DOCUMENT PROCESSING FEE" in desc_upper or "DOCS PROCESSING" in desc_upper:
            return self.config_manager.get_portal_fee_rate(
                "DOCUMENT_PROCESSING_FEE", "USD"
            )

        # Priority 2: 키워드 기반 고정 요율 조회
        fixed_fee = self.config_manager.get_fixed_fee_by_keywords(description)
        if fixed_fee:
            # Transport mode 필요 시 검증
            if fixed_fee.get("transport_mode"):
                transport_mode = self._identify_transport_mode(row)
                if fixed_fee["transport_mode"].upper() == transport_mode.upper():
                    return fixed_fee["rate"]
            else:
                return fixed_fee["rate"]

        # Priority 3: 기존 로직 (Configuration, Lane Map, PDF)
        desc_upper = str(description).upper()

        # row가 제공되지 않으면 기본값 사용
        if row is None:
            row = pd.Series({"CHARGE GROUP": "Contract"})

        charge_group = str(row.get("CHARGE GROUP", "")).strip().upper()

        # 1. CONTRACT 항목: Configuration 우선
        if "CONTRACT" in charge_group:
            # 1-1. Fixed contract rates (config_contract_rates.json)
            contract_rate = self.config_manager.get_contract_rate(description)
            if contract_rate is not None:
                return contract_rate

            # 1-2. Inland Transportation (config_contract_rates.json - inland_transportation)
            if any(
                kw in desc_upper
                for kw in ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
            ):
                # Description에서 출발지/목적지 파싱
                port, destination = self._parse_transportation_route(description)
                if port and destination:
                    # 새로운 inland_transportation 우선 조회
                    inland_rate = self.config_manager.get_inland_transportation_rate(
                        port, destination
                    )
                    if inland_rate is not None:
                        return inland_rate

                    # Fallback: lane_map 조회
                    ref_rate = self.config_manager.get_lane_rate(
                        port, destination, "per truck"
                    )
                    if ref_rate is not None:
                        return ref_rate

            # 1-3. Fallback: PDF (계약서 스캔본)
            pdf_rate = self._extract_rate_from_pdf(row)
            return pdf_rate

        # 2. 일반 항목: PDF 우선
        else:
            # 2-1. PDF 첨부파일에서 추출
            pdf_rate = self._extract_rate_from_pdf(row)
            if pdf_rate:
                return pdf_rate

            # 2-2. Fallback: Configuration
            contract_rate = self.config_manager.get_contract_rate(description)
            if contract_rate is not None:
                return contract_rate

            # Inland Transportation fallback
            if any(
                kw in desc_upper
                for kw in ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
            ):
                port, destination = self._parse_transportation_route(description)
                if port and destination:
                    # 새로운 inland_transportation 우선 조회
                    inland_rate = self.config_manager.get_inland_transportation_rate(
                        port, destination
                    )
                    if inland_rate is not None:
                        return inland_rate

                    # Fallback: lane_map 조회
                    ref_rate = self.config_manager.get_lane_rate(
                        port, destination, "per truck"
                    )
                    if ref_rate is not None:
                        return ref_rate

        # 3. 기타 표준 요율 (추후 확장 가능)
        return None

    def _extract_pdf_line_item(self, row: pd.Series) -> Optional[Dict]:
        """
        PDF에서 실제 청구 라인 아이템 추출 (금액, 수량, 단가)

        Returns:
            {
                "description": str,
                "qty": float,
                "unit_rate": float,
                "amount": float,
                "matched_by": str
            } or None
        """
        order_ref = str(row.get("Order Ref. Number", "")).strip()
        category = str(row.get("DESCRIPTION", "")).strip()

        # Category 정규화
        normalized_category = self.normalizer.normalize(category)

        # PDF 매핑
        pdf_mapping = self.map_masterdata_to_pdf(row)
        if pdf_mapping["pdf_count"] == 0:
            return None

        # Draft Total 추출 (금액 범위 검증용)
        draft_total = float(row.get("TOTAL (USD)", 0.0) or 0.0)

        # Hybrid System 사용
        if self.use_hybrid and self.hybrid_client and self.ir_adapter:
            for pdf_path in pdf_mapping["pdf_files"]:
                try:
                    # Hybrid API로 파싱 요청
                    unified_ir = self.hybrid_client.parse_pdf(str(pdf_path), "invoice")

                    if unified_ir:
                        # 실제 라인 아이템 추출 (정규화 우선, 원본 Fallback)
                        # draft_total을 전달하여 금액 범위 검증 수행
                        line_item = self.ir_adapter.extract_invoice_line_item(
                            unified_ir, normalized_category, draft_total
                        )

                        if not line_item:
                            line_item = self.ir_adapter.extract_invoice_line_item(
                                unified_ir, category, draft_total
                            )

                        if line_item:
                            return line_item

                except Exception as e:
                    logger.warning(f"[PDF LINE ITEM] Extraction failed: {e}")
                    continue

        return None

    def _extract_rate_from_pdf(self, row: pd.Series) -> Optional[float]:
        """PDF에서 Rate 추출 (Hybrid System 우선, 통화 변환 포함, Category 정규화)"""

        order_ref = str(row.get("Order Ref. Number", "")).strip()
        category = str(row.get("DESCRIPTION", "")).strip()

        # Category 정규화 (Synonym + 수량 제거)
        normalized_category = self.normalizer.normalize(category)
        logger.debug(f"[NORMALIZE] '{category}' → '{normalized_category}'")

        # PDF 매핑
        pdf_mapping = self.map_masterdata_to_pdf(row)
        if pdf_mapping["pdf_count"] == 0:
            return None

        # Hybrid System 사용 (우선)
        if self.use_hybrid and self.hybrid_client and self.ir_adapter:
            for pdf_path in pdf_mapping["pdf_files"]:
                try:
                    logger.info(
                        f"[HYBRID] Parsing {pdf_path.name} for '{normalized_category}'"
                    )

                    # 1. Hybrid API로 파싱 요청
                    unified_ir = self.hybrid_client.parse_pdf(str(pdf_path), "invoice")

                    if unified_ir:
                        # 2. 정규화된 Category로 요율 추출 (먼저 시도)
                        rate = self.ir_adapter.extract_rate_for_category(
                            unified_ir, normalized_category
                        )

                        # 3. Fallback: 원본 Category로 시도
                        if not rate or rate <= 0:
                            rate = self.ir_adapter.extract_rate_for_category(
                                unified_ir, category
                            )

                        if rate and rate > 0:
                            logger.info(
                                f"[HYBRID] Found rate for '{normalized_category}': {rate} USD (engine: {unified_ir.get('engine')})"
                            )
                            return rate

                except Exception as e:
                    logger.warning(
                        f"[HYBRID] Parsing failed for {pdf_path}: {e}. Trying next PDF..."
                    )
                    continue

        # Fallback: Legacy PDF Integration
        if not PDF_AVAILABLE or not self.pdf_integration:
            return None

        logger.info(f"[LEGACY] Using legacy PDF integration for '{category}'")

        # PDF 파싱 및 Rate 추출 (기존 로직)
        for pdf_path in pdf_mapping["pdf_files"]:
            try:
                pdf_data = self.pdf_integration.parse_pdf(str(pdf_path))

                # Category 매칭
                matched_rate = self._match_category_in_pdf(category, pdf_data)
                if matched_rate:
                    # 통화 변환 (AED → USD)
                    return self._convert_currency_if_needed(
                        matched_rate, pdf_data.get("currency")
                    )
            except Exception as e:
                logger.warning(f"PDF parsing failed for {pdf_path}: {e}")
                continue

        return None

    def _match_category_in_pdf(self, category: str, pdf_data: dict) -> Optional[float]:
        """PDF 데이터에서 Category 매칭하여 Rate 추출"""
        # 간단한 키워드 매칭 (실제 구현에서는 더 정교한 로직 필요)
        category_lower = category.lower()

        # PDF에서 추출된 데이터에서 매칭 시도
        if "boe_data" in pdf_data:
            for item in pdf_data["boe_data"]:
                if category_lower in str(item.get("description", "")).lower():
                    return item.get("rate")

        if "do_data" in pdf_data:
            for item in pdf_data["do_data"]:
                if category_lower in str(item.get("description", "")).lower():
                    return item.get("rate")

        return None

    def _convert_currency_if_needed(self, rate: float, currency: str) -> float:
        """통화 변환 (AED → USD)"""
        if currency and "AED" in currency.upper():
            fx_rate = self.config_manager.get_fx_rate()
            return round(rate / fx_rate, 2)
        return rate

    def _parse_transportation_route(self, description: str) -> tuple:
        """Description에서 출발지/목적지 추출"""

        import re

        desc_upper = str(description).upper()

        # "FROM ... TO ..." 패턴
        match = re.search(r"FROM\s+([A-Z\s]+)\s+TO\s+([A-Z\s]+)", desc_upper)
        if match:
            port = match.group(1).strip()
            destination = match.group(2).strip()

            # Normalization
            port = self._normalize_location(port)
            destination = self._normalize_location(destination)

            return (port, destination)

        return (None, None)

    def _normalize_location(self, location: str) -> str:
        """위치명 정규화"""

        normalization = self.config_manager.get_normalization_aliases()
        location_upper = str(location).strip().upper()

        # Check ports
        ports = normalization.get("ports", {})
        for alias, standard in ports.items():
            if str(alias).upper() == location_upper:
                return standard

        # Check destinations
        destinations = normalization.get("destinations", {})
        for alias, standard in destinations.items():
            if str(alias).upper() == location_upper:
                return standard

        # No match found - return original
        return location.strip()

    def calculate_delta_percent(
        self, draft_rate: float, ref_rate: float
    ) -> Optional[float]:
        """Delta % 계산"""

        if pd.isna(draft_rate) or pd.isna(ref_rate) or ref_rate == 0:
            return None

        return round(((draft_rate - ref_rate) / ref_rate) * 100, 2)

    def get_cost_guard_band_legacy(self, delta_percent: Optional[float]) -> str:
        """
        COST-GUARD 밴드 결정 (Config 기반으로 이동됨, 호환성 유지용)
        
        DEPRECATED: Use cost_guard.get_cost_guard_band() instead
        """
        # Config 기반 밴드 판정 사용
        return get_cost_guard_band(delta_percent, self.cost_guard_bands)

    def calculate_gate_score(
        self,
        row: pd.Series,
        ref_rate: Optional[float],
        charge_group: str,
        pdf_count: int = 0,
    ) -> float:
        """Gate 검증 점수 계산 (0-100)"""

        score = 0
        max_score = 100

        # Gate-01: RATE SOURCE 존재
        if not pd.isna(row.get("RATE SOURCE")):
            score += 10

        # Gate-02: DESCRIPTION 존재
        if not pd.isna(row.get("DESCRIPTION")):
            score += 10

        # Gate-03: RATE 유효값
        if not pd.isna(row.get("RATE")) and row.get("RATE", 0) > 0:
            score += 10

        # Gate-04: Q'TY 유효값
        if not pd.isna(row.get("Q'TY")) and row.get("Q'TY", 0) > 0:
            score += 10

        # Gate-05: TOTAL 계산 정확성
        if (
            not pd.isna(row.get("RATE"))
            and not pd.isna(row.get("Q'TY"))
            and not pd.isna(row.get("TOTAL (USD)"))
        ):
            expected_total = row["RATE"] * row["Q'TY"]
            actual_total = row["TOTAL (USD)"]
            if abs(expected_total - actual_total) < 0.01:
                score += 10

        # Gate-06: Contract 요율 검증
        if charge_group == "Contract" and ref_rate is not None:
            score += 15

        # Gate-07: Delta 허용 범위 (Contract만)
        if charge_group == "Contract" and ref_rate is not None:
            delta = self.calculate_delta_percent(row.get("RATE", 0), ref_rate)
            if delta is not None and abs(delta) <= 2:
                score += 15

        # Gate-08: PDF 증빙문서 존재 (추가)
        if pdf_count > 0:
            score += 10

        # Gate-09: PDF 개수 적정성 (BOE/DO/DN 등 3개 이상)
        if pdf_count >= 3:
            score += 10

        return min(score, max_score)

    def map_masterdata_to_pdf(self, row: pd.Series) -> Dict:
        """MasterData 행 → PDF 파일 매핑 (개선된 로직)"""

        order_ref = row.get("Order Ref. Number")  # "HVDC-ADOPT-SCT-0126"

        if pd.isna(order_ref) or not self.supporting_docs_path.exists():
            return {"shipment_id": None, "pdf_count": 0, "pdf_files": []}

        # PDF 파일들은 하위 디렉토리 안에 있음
        # 패턴: "NN. {order_ref}/" 디렉토리 찾기
        pdf_files = []

        # 정규화 함수
        def normalize(text):
            """공백, 쉼표 제거하고 소문자로 변환"""
            return text.replace(" ", "").replace(",", "").lower()

        order_ref_normalized = normalize(str(order_ref))

        # 재귀적으로 PDF 찾기 (하위 디렉토리 포함)
        for subdir in self.supporting_docs_path.iterdir():
            if subdir.is_dir():
                dir_name_normalized = normalize(subdir.name)

                # 정확한 매칭 또는 정규화 매칭
                if (
                    order_ref in subdir.name
                    or order_ref_normalized in dir_name_normalized
                ):
                    # 해당 디렉토리 안의 모든 PDF 찾기
                    pdf_files.extend(list(subdir.glob("*.pdf")))
                    break  # 첫 번째 매칭 디렉토리만 사용

        return {
            "shipment_id": order_ref,
            "pdf_count": len(pdf_files),
            "pdf_files": pdf_files,
        }

    def validate_row(self, row: pd.Series) -> Dict:
        """MasterData 행 검증"""

        # Charge Group 분류
        charge_group = self.classify_charge_group(
            row.get("RATE SOURCE"), row.get("DESCRIPTION")
        )

        # 기준 요율 조회
        ref_rate = None
        if charge_group == "Contract":
            ref_rate = self.find_contract_ref_rate(
                row.get("DESCRIPTION"), row.get("RATE SOURCE"), row
            )
        elif charge_group == "PortalFee":
            # Portal Fee는 Configuration에서 USD로 직접 조회
            ref_rate = self.config_manager.get_portal_fee_rate(
                row.get("DESCRIPTION"), "USD"
            )

        # Delta 계산
        delta_pct = self.calculate_delta_percent(row.get("RATE"), ref_rate)

        # COST-GUARD 밴드 (Config 기반)
        cg_band = get_cost_guard_band(delta_pct, self.cost_guard_bands)

        # PDF 매핑
        pdf_info = self.map_masterdata_to_pdf(row)
        pdf_count = pdf_info["pdf_count"]

        # PDF 실제 청구 금액/수량 검증 (NEW)
        pdf_line_item = self._extract_pdf_line_item(row)

        # Gate 점수 (PDF 고려)
        gate_score = self.calculate_gate_score(row, ref_rate, charge_group, pdf_count)
        gate_status = "PASS" if gate_score >= 80 else "FAIL"

        # Validation Status 결정
        validation_status = "REVIEW_NEEDED"
        rate_source = str(row.get("RATE SOURCE", "")).upper()

        # At Cost 항목: 수식 우선, PDF 2차 검증
        if "AT COST" in rate_source or "ATCOST" in rate_source:
            # 1차: 수식 또는 고정 요율에서 Ref Rate 추출
            formula_str = str(row.get("Formula", "")).strip()
            description = str(row.get("DESCRIPTION", "")).strip()
            draft_total = float(row.get("TOTAL (USD)", 0.0) or 0.0)
            
            ref_from_formula = parse_rate_from_formula_or_fixed(
                formula_str, description, KNOWN_AED_RATES, self.fx_rate
            )
            
            if ref_from_formula:
                # 수식 기반 Ref Rate 사용
                ref_rate = ref_from_formula
                delta_pct = self.calculate_delta_percent(row.get("RATE"), ref_rate)
                
                if delta_pct is not None and abs(delta_pct) <= 0.5:
                    validation_status = "PASS"  # 수식과 일치
                elif delta_pct is not None and abs(delta_pct) > 3.0:
                    validation_status = "FAIL"  # 3% 이상 차이
                else:
                    validation_status = "REVIEW_NEEDED"
            
            # 2차: PDF 실제 데이터 검증 (수식 없거나 검증용)
            elif pdf_line_item:
                pdf_amount = pdf_line_item.get("amount", 0.0)
                amount_diff = abs(pdf_amount - draft_total) if pdf_amount else None

                if amount_diff is not None and amount_diff < 0.01:
                    validation_status = "PASS"  # PDF 금액 일치
                elif amount_diff is not None and amount_diff > draft_total * 0.03:
                    validation_status = "FAIL"  # 3% 이상 차이
                else:
                    validation_status = "REVIEW_NEEDED"
            
            # 3차: PDF 있지만 추출 실패
            elif pdf_count > 0:
                validation_status = "REVIEW_NEEDED"  # PDF 있지만 미추출
            
            # 4차: PDF 완전 없음
            else:
                validation_status = "FAIL"  # At Cost인데 증빙 없음

        # Contract 항목 (Auto-Fail 조건: >15% Config 기반)
        elif charge_group == "Contract" and ref_rate is not None:
            if delta_pct is not None:
                # Config 기반 밴드로 PASS 판정
                if cg_band == "PASS":
                validation_status = "PASS"
                # Auto-Fail 체크 (15% threshold from Config)
                elif check_auto_fail(delta_pct, auto_fail_threshold=15.0):
                validation_status = "FAIL"

        # Portal Fee 항목 (특수 허용 오차 ±0.5%)
        elif charge_group == "PortalFee" and delta_pct is not None:
            portal_tolerance = self.cost_guard_bands.get("special_tolerances", {}).get(
                "portal_fee", {}
            ).get("max_delta", 0.5)
            
            if abs(delta_pct) <= portal_tolerance:
                validation_status = "PASS"
            elif check_auto_fail(delta_pct, auto_fail_threshold=5.0):
                validation_status = "FAIL"

        # PDF 소스 파일 추출
        pdf_source_file = None
        if pdf_info["pdf_files"]:
            # 실제 매칭된 첫 번째 파일 사용 (향후 개선 가능)
            pdf_source_file = pdf_info["pdf_files"][0].name if pdf_info["pdf_files"] else None
        
        # PDF 증빙 정보 추출
        pdf_matched_desc = pdf_line_item.get("description") if pdf_line_item else None
        pdf_formula = self._extract_formula_from_pdf(row, pdf_info)
        pdf_amount_aed = self._get_aed_amount(pdf_line_item)
        pdf_amount_usd = pdf_line_item.get("amount") if pdf_line_item else None
        pdf_matched_by = pdf_line_item.get("matched_by") if pdf_line_item else None
        pdf_confidence = self._calculate_match_confidence(pdf_line_item)
        pdf_extraction_status = "Success" if pdf_line_item else ("No PDF" if pdf_count == 0 else "Failed")
        evidence_summary = self._generate_evidence_summary(pdf_info, pdf_line_item)

        return {
            "Validation_Status": validation_status,
            "Ref_Rate_USD": ref_rate,
            "Python_Delta": delta_pct,
            "CG_Band": cg_band,
            "Charge_Group": charge_group,
            "Gate_Score": gate_score,
            "Gate_Status": gate_status,
            "PDF_Count": pdf_count,
            "PDF_Matched_Description": pdf_matched_desc,
            "PDF_Formula": pdf_formula,
            "PDF_Amount_AED": pdf_amount_aed,
            "PDF_Amount_USD": pdf_amount_usd,
            "PDF_Qty": pdf_line_item.get("qty") if pdf_line_item else None,
            "PDF_Unit_Rate": pdf_line_item.get("unit_rate") if pdf_line_item else None,
            "PDF_Source_File": pdf_source_file,
            "PDF_Matched_By": pdf_matched_by,
            "PDF_Confidence": pdf_confidence,
            "PDF_Extraction_Status": pdf_extraction_status,
            "Evidence_Summary": evidence_summary,
            "Validation_Notes": self._generate_notes(
                row, ref_rate, delta_pct, charge_group, pdf_count, pdf_line_item, pdf_info
            ),
        }

    def _extract_formula_from_pdf(self, row: pd.Series, pdf_mapping: Dict) -> Optional[str]:
        """PDF에서 계산식 추출 (=AED/FX 형태)"""
        
        # 엑셀 Formula 컬럼이 있으면 우선 사용
        formula = str(row.get("Formula", "")).strip()
        if formula and formula != "nan":
            return formula
        
        # PDF에서 추출 시도 (향후 구현 가능)
        # TODO: PDF 내 formula 패턴 인식 (예: "=150/3.6725")
        
        return None
    
    def _get_aed_amount(self, pdf_line_item: Optional[Dict]) -> Optional[float]:
        """USD 금액에서 AED 역산"""
        
        if not pdf_line_item:
            return None
        
        amount_usd = pdf_line_item.get("amount", 0.0)
        if amount_usd <= 0:
            return None
        
        # FX rate로 AED 역산
        aed_amount = amount_usd * self.fx_rate
        return round(aed_amount, 2)
    
    def _calculate_match_confidence(self, pdf_line_item: Optional[Dict]) -> float:
        """매칭 신뢰도 계산 (exact:1.0, contains:0.9, keyword:0.7, fuzzy:similarity)"""
        
        if not pdf_line_item:
            return 0.0
        
        matched_by = pdf_line_item.get("matched_by", "").lower()
        
        confidence_map = {
            "exact": 1.0,
            "contains": 0.9,
            "keyword": 0.7,
            "fuzzy": 0.6,  # 기본 fuzzy confidence
        }
        
        return confidence_map.get(matched_by, 0.0)
    
    def _generate_evidence_summary(self, pdf_mapping: Dict, pdf_line_item: Optional[Dict]) -> str:
        """증빙 문서 요약 생성"""
        
        pdf_count = pdf_mapping.get("pdf_count", 0)
        
        if pdf_count == 0:
            return "No PDF evidence"
        
        # PDF 파일 목록 (파일명만)
        pdf_files = pdf_mapping.get("pdf_files", [])
        file_names = [f.name for f in pdf_files] if pdf_files else []
        
        summary_parts = []
        
        # 1. PDF 개수 및 파일 목록 (최대 3개만 표시)
        if len(file_names) <= 3:
            summary_parts.append(f"{pdf_count} PDFs: {', '.join(file_names)}")
        else:
            summary_parts.append(f"{pdf_count} PDFs: {', '.join(file_names[:3])}, ...")
        
        # 2. 매칭된 내용 (있는 경우)
        if pdf_line_item:
            desc = pdf_line_item.get("description", "")
            amount = pdf_line_item.get("amount", 0.0)
            matched_by = pdf_line_item.get("matched_by", "")
            
            if desc:
                summary_parts.append(f"Matched: '{desc}' = ${amount:.2f} ({matched_by})")
        
        return " | ".join(summary_parts) if summary_parts else f"{pdf_count} PDFs available"

    def _generate_notes(
        self,
        row: pd.Series,
        ref_rate: Optional[float],
        delta_pct: Optional[float],
        charge_group: str,
        pdf_count: int = 0,
        pdf_line_item: Optional[Dict] = None,
        pdf_info: Optional[Dict] = None,
    ) -> str:
        """검증 노트 생성 (개선된 버전 - PDF 증빙 경로 및 매칭 정보 상세화)"""

        notes = []

        charge_group_upper = charge_group.upper()
        rate_source = str(row.get("RATE SOURCE", "")).upper()
        description = str(row.get("DESCRIPTION", "")).strip()

        # 1. Ref Rate 소스 상세 정보
        if ref_rate:
            if "CONTRACT" in charge_group_upper:
                notes.append(f"✅ Contract: Ref ${ref_rate:.2f} from Config")
            elif "PORTAL" in charge_group_upper.upper():
                notes.append(f"✅ Portal Fee: ${ref_rate:.2f} from Config")
            else:
                notes.append(f"✅ Ref Rate: ${ref_rate:.2f}")
        
        # 2. PDF 증빙 상세 정보
        if pdf_count > 0 and pdf_info:
            pdf_files = pdf_info.get("pdf_files", [])
            pdf_file_names = [f.name for f in pdf_files[:3]] if pdf_files else []
            
            if pdf_file_names:
                notes.append(f"✅ PDF Verified: {pdf_count} files ({', '.join(pdf_file_names)})")
            else:
                notes.append(f"✅ PDF Verified: {pdf_count} files")
            
            # PDF 매칭 결과
            if pdf_line_item:
                matched_desc = pdf_line_item.get("description", "")
                matched_by = pdf_line_item.get("matched_by", "").upper()
                pdf_amount = pdf_line_item.get("amount", 0.0)
                
                notes.append(f"  └─ Matched: '{matched_desc}' = ${pdf_amount:.2f} ({matched_by})")
        elif pdf_count == 0:
            notes.append("⚠ No PDF evidence available")

        # 3. At Cost 항목 필수 검증
        if "AT COST" in rate_source or "ATCOST" in rate_source:
            if pdf_line_item:
                pdf_amount = pdf_line_item.get("amount", 0.0)
                pdf_qty = pdf_line_item.get("qty", 1.0)
                pdf_unit_rate = pdf_line_item.get("unit_rate", 0.0)
                draft_total = row.get("TOTAL (USD)", 0.0)

                # PDF 금액 vs Draft 금액 비교
                amount_diff = abs(pdf_amount - draft_total) if pdf_amount else None

                if amount_diff is not None and amount_diff < 0.01:
                    notes.append(
                        f"✅ At Cost verified: PDF ${pdf_amount:.2f} = Draft ${draft_total:.2f}"
                    )
                elif amount_diff is not None:
                    notes.append(
                        f"⚠ At Cost mismatch: PDF ${pdf_amount:.2f} ≠ Draft ${draft_total:.2f} (Δ${amount_diff:.2f})"
                    )

                # PDF 세부 정보 (Qty, Unit Rate)
                if pdf_qty and pdf_qty > 0:
                    notes.append(f"  └─ PDF Qty: {pdf_qty}, Unit Rate: ${pdf_unit_rate:.2f}")
            else:
                notes.append(
                    "❌ CRITICAL: At Cost requires PDF verification - No PDF data found!"
                )

        # 4. Formula 정보 (있는 경우)
        formula_str = str(row.get("Formula", "")).strip()
        if formula_str and formula_str != "nan":
            notes.append(f"✅ Formula: {formula_str}")

        # 5. Delta 판정
        if delta_pct is not None:
            if abs(delta_pct) <= 0.5:
                notes.append(f"✅ Delta: {delta_pct:.1f}% (EXACT MATCH)")
            elif abs(delta_pct) <= 2:
                notes.append(f"✅ Delta: {delta_pct:.1f}% (Within tolerance)")
            elif abs(delta_pct) <= 10:
                notes.append(f"⚠ Delta: {delta_pct:.1f}% (Review needed)")
            else:
                notes.append(f"❌ Delta: {delta_pct:.1f}% (HIGH VARIANCE)")

        # 6. VBA DIFF 경고
        vba_diff = abs(float(row.get("DIFFERENCE", 0)))
        if vba_diff > 0.01:
            notes.append(f"⚠ VBA DIFF: ${vba_diff:.2f}")

        return "\n".join(notes) if notes else "No validation notes"

    def validate_all(self) -> pd.DataFrame:
        """MasterData 전체 검증"""

        logger.info("=" * 80)
        logger.info("MasterData Validation Start")
        logger.info("=" * 80)

        # MasterData 로드
        df_master = self.load_masterdata()

        # 검증 결과 저장용 리스트
        validation_results = []

        logger.info(f"\nValidating {len(df_master)} items...")

        for idx, row in df_master.iterrows():
            validation = self.validate_row(row)
            validation_results.append(validation)

            if (idx + 1) % 20 == 0:
                logger.info(f"  Processed: {idx + 1}/{len(df_master)}")

        # 검증 결과를 DataFrame으로 변환
        df_validation = pd.DataFrame(validation_results)

        # 원본 + 검증 결과 결합
        df_result = pd.concat([df_master, df_validation], axis=1)

        logger.info(
            f"\n[OK] Validation complete: {len(df_result)} rows × {len(df_result.columns)} columns"
        )

        # 통계 출력
        self._print_statistics(df_result)

        return df_result

    def _print_statistics(self, df: pd.DataFrame):
        """검증 통계 출력"""

        print("\n" + "=" * 80)
        print("Validation Statistics")
        print("=" * 80)

        # Validation Status
        print(f"\n[Validation Status]")
        status_counts = df["Validation_Status"].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count} ({count/len(df)*100:.1f}%)")

        # Charge Group
        print(f"\n[Charge Group Distribution]")
        cg_counts = df["Charge_Group"].value_counts()
        for group, count in cg_counts.items():
            print(f"  {group}: {count} ({count/len(df)*100:.1f}%)")

        # Contract 항목 분석
        contract_items = df[df["Charge_Group"] == "Contract"]
        if len(contract_items) > 0:
            print(f"\n[Contract Validation]")
            print(f"Total Contract items: {len(contract_items)}")
            with_ref = len(contract_items[contract_items["Ref_Rate_USD"].notna()])
            print(
                f"Items with ref_rate: {with_ref} ({with_ref/len(contract_items)*100:.1f}%)"
            )

            # Delta 분석
            validated = contract_items[contract_items["Python_Delta"].notna()]
            if len(validated) > 0:
                print(f"\nDelta Analysis:")
                print(f"  Average: {validated['Python_Delta'].mean():.2f}%")
                print(f"  Max: {validated['Python_Delta'].max():.2f}%")
                print(f"  Min: {validated['Python_Delta'].min():.2f}%")

            # COST-GUARD
            print(f"\nCOST-GUARD Distribution:")
            cg_band_counts = validated["CG_Band"].value_counts()
            for band, count in cg_band_counts.items():
                print(f"  {band}: {count} ({count/len(validated)*100:.1f}%)")

        # Gate 검증
        print(f"\n[Gate Validation]")
        gate_pass = len(df[df["Gate_Status"] == "PASS"])
        print(f"Gate PASS: {gate_pass}/{len(df)} ({gate_pass/len(df)*100:.1f}%)")
        print(f"Average Gate Score: {df['Gate_Score'].mean():.1f}/100")

        # VBA vs Python 비교
        print(f"\n[VBA vs Python Comparison]")
        vba_vs_python = df[
            (df["REV RATE"].notna())
            & (df["Ref_Rate_USD"].notna())
            & (df["DIFFERENCE"] != 0)
        ]
        if len(vba_vs_python) > 0:
            print(f"Items with both VBA and Python results: {len(vba_vs_python)}")
            print(
                f"VBA DIFFERENCE range: ${vba_vs_python['DIFFERENCE'].min():.2f} to ${vba_vs_python['DIFFERENCE'].max():.2f}"
            )
            print(
                f"Python Delta range: {vba_vs_python['Python_Delta'].min():.2f}% to {vba_vs_python['Python_Delta'].max():.2f}%"
            )


def main():
    """메인 실행 함수"""

    validator = MasterDataValidator()
    df_validated = validator.validate_all()

    # 결과 저장
    output_dir = Path(__file__).parent / "out"
    output_dir.mkdir(exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV 저장
    csv_path = output_dir / f"masterdata_validated_{timestamp}.csv"
    df_validated.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"\n[SAVED] CSV: {csv_path}")

    # Excel 저장 (기본)
    excel_path = output_dir / f"masterdata_validated_{timestamp}.xlsx"
    df_validated.to_excel(excel_path, index=False, engine="openpyxl")
    logger.info(f"[SAVED] Excel: {excel_path}")

    print(f"\n[SUCCESS] MasterData validation complete!")
    print(f"Total rows: {len(df_validated)}")
    print(f"Total columns: {len(df_validated.columns)}")
    print(f"  - VBA original: 13")
    print(f"  - Python validation: 9")

    return df_validated


if __name__ == "__main__":
    main()
