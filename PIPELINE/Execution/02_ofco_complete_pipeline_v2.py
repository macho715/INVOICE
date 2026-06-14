#!/usr/bin/env python3
"""
OFCO Invoice Complete Pipeline Algorithm v3.0
==============================================

Phase 1: Port Invoice → Standard Lines Schema (v3.0: Manpower Unit 분해 개선)
Phase 2: Lines → Cost Center + Price Center (v3.0: JSON 규칙 + V3 엔진 통합)
Phase 3: Lines → EA Slots (v3.0: 라인 분할 지원)

v3.0 개선사항:
- Manpower Unit 분해: SUBJECT/NOTES에서 실제 명(man)과 시간(hours) 추출
- Cost Center 매핑 강화: 614개 JSON 규칙 적용, V3 매핑 엔진 통합
- 라인 분할: 5개 이상 항목 시 자동 라인 분할 (-A/-B suffix)

Author: MACHO-GPT v3.4-mini
Date: 2025-11-03
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import re
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
import json
from pathlib import Path
# HeaderCore 통합 (표준 경로)
import sys
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "shared" / "scripts"))
    from ofco_header_core import get_header_core
    HEADER_CORE_AVAILABLE = True
except ImportError:
    try:
        # fallback: 현재 디렉토리
        from ofco_header_core import get_header_core
        HEADER_CORE_AVAILABLE = True
    except ImportError:
        HEADER_CORE_AVAILABLE = False
        print("[WARNING] HeaderCore를 사용할 수 없습니다. 기본 컬럼 순서를 사용합니다.")
        get_header_core = None

# ============================================================
# CONSTANTS
# ============================================================

TOLERANCE = Decimal("0.01")
MAX_EA_SLOTS = 4
DECIMAL_PLACES = 2
AED_CURRENCY = "AED"

# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class StandardLine:
    """표준 Lines 스키마"""

    invoice_no: str
    line_no: int
    tariff_id: str
    description: str
    unit1: Decimal
    unit2: Decimal
    unit3: Decimal
    rate: Decimal
    amount_excl_tax: Decimal
    tax_rate_pct: Decimal
    tax_amount: Decimal
    total_incl_tax: Decimal
    calc_check: bool
    evidence: str

    # Phase 2 추가 필드
    cost_center: Optional[str] = None
    price_center_a: Optional[Decimal] = None
    price_center_b: Optional[Decimal] = None
    price_center_c: Optional[Decimal] = None

    # v3.0 추가 필드
    cost_main: Optional[str] = None
    cost_center_a: Optional[str] = None
    price_center_name: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        d = asdict(self)
        # Decimal을 float로 변환
        for key, value in d.items():
            if isinstance(value, Decimal):
                d[key] = float(value)
        return d


@dataclass
class EASlot:
    """EA 슬롯"""

    slot_no: int
    name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal

    def to_dict(self) -> Dict:
        return {
            f"EA_{self.slot_no}_Name": self.name,
            f"EA_{self.slot_no}_Qty": float(self.qty),
            f"EA_{self.slot_no}_Rate": float(self.rate),
            f"EA_{self.slot_no}_Amount": float(self.amount),
        }


# ============================================================
# PHASE 1: CSV → STANDARD LINES SCHEMA
# ============================================================


class Phase1Transformer:
    """Phase 1: CSV → 표준 Lines 스키마 변환"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.qty_amount_pairs = self._identify_qty_amount_pairs()

    def _identify_qty_amount_pairs(self) -> List[Tuple[str, str]]:
        """QTY/AMOUNT 컬럼 쌍 식별"""
        pairs = []
        # 컬럼 이름을 문자열로 변환
        qty_cols = [str(col) for col in self.df.columns if str(col).endswith("_QTY")]

        for qty_col in qty_cols:
            base_name = qty_col.replace("_QTY", "")
            amount_col = base_name + "_AMOUNT"
            # 컬럼 이름도 문자열로 변환하여 비교
            df_cols_str = [str(col) for col in self.df.columns]
            if amount_col in df_cols_str:
                # 원본 컬럼 이름 찾기
                amount_col_orig = next(
                    col for col in self.df.columns if str(col) == amount_col
                )
                qty_col_orig = next(
                    col for col in self.df.columns if str(col) == qty_col
                )
                pairs.append((qty_col_orig, amount_col_orig))

        return pairs

    def _clean_decimal(self, value: Any) -> Optional[Decimal]:
        """숫자 값 정제"""
        if pd.isna(value) or value == "" or value is None:
            return None

        if isinstance(value, (int, float)):
            return Decimal(str(value))

        if isinstance(value, str):
            cleaned = value.replace(",", "").strip()
            if cleaned == "" or cleaned == "-":
                return None
            try:
                return Decimal(cleaned)
            except:
                return None

        return None

    def _round_dec(self, value: Optional[Decimal]) -> Decimal:
        """Decimal 반올림"""
        if value is None:
            return Decimal("0.00")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _infer_tariff_id(self, row: pd.Series) -> str:
        """Tariff ID 추론"""
        # SUBJECT나 COST CENTER로부터 Tariff ID 추론
        subject = str(row.get("SUBJECT", "")).upper()

        # 간단한 매핑 규칙
        tariff_map = {
            "PORT DUE": "100.1",
            "CARGO CLEARANCE": "100.2",
            "CHANNEL": "6.6",
            "WASTE": "6.1",
            "BULK": "201.3",
            "HEAVY LIFT": "703.1",
            "LABOUR": "802.3A",
            "FOREMAN": "802.5A",
            "DOCUMENT": "2.20",
            "PERMIT": "15.1",
        }

        for keyword, tariff in tariff_map.items():
            if keyword in subject:
                return tariff

        return "UNKNOWN"

    def _infer_units(self, row: pd.Series) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Unit1/2/3 추론 (v3.0 개선: Manpower Unit 분해)

        규칙:
        - 기본: (1, 1, 1)
        - Labour/Manpower: (0, 명, 시간) - 실제 데이터에서 추출
        - Heavy Lift: (FRT, 1, 1)
        """
        subject = str(row.get("SUBJECT", "")).upper()
        notes = str(row.get("NOTES", "") or row.get("NOTES_TEXT", "") or "").upper()
        combined_text = f"{subject} {notes}"

        # Labour/Manpower 패턴 처리
        manpower_keywords = [
            "LABOUR",
            "FOREMAN",
            "MANPOWER",
            "SUPERVISOR",
            "RIGGER",
            "BANKSMAN",
            "WINCH",  # 추가
            "ADDITIONAL MAN",  # 추가
        ]
        is_manpower = any(keyword in combined_text for keyword in manpower_keywords)

        if is_manpower:
            # Method 1: SUBJECT/NOTES에서 패턴 추출
            # 패턴: "X명", "X man", "Y시간", "Y hours", "X명 × Y시간"
            unit2 = None  # 명(man)
            unit3 = None  # 시간(hours)

            # 인원수 추출 패턴 (개선: 다양한 형식 지원)
            man_patterns = [
                r"(\d+(?:\.\d+)?)\s*(?:명|man|men|MEN|MAN|persons?)\b",
                r"(\d+(?:\.\d+)?)\s*[x×X]\s*(?:명|man|men|MEN|MAN|persons?)",
                r"(?:명|man|men|MEN|MAN|persons?)\s*[:\s]+(\d+(?:\.\d+)?)",
                r"\b(\d+)\s*(?:man|MAN)\b",  # "3man" 형식
            ]

            # 시간 추출 패턴 (개선: 다양한 형식 지원)
            hour_patterns = [
                r"(\d+(?:\.\d+)?)\s*(?:시간|hour|hr|hours|hrs|HOUR|HRS?)\b",
                r"(\d+(?:\.\d+)?)\s*[x×X]\s*(?:시간|hour|hr|hours|hrs|HOUR|HRS?)",
                r"(?:시간|hour|hr|hours|hrs|HOUR|HRS?)\s*[:\s]+(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?)\b",  # "3hrs" 형식
                r"(\d+(?:\.\d+)?)\s*(?:days?|DAYS?)\b",  # "3days" 형식 (8시간 기준)
            ]

            # 인원수 추출
            for pattern in man_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    try:
                        unit2 = Decimal(str(match.group(1)))
                        break
                    except:
                        continue

            # 시간 추출
            for pattern in hour_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    try:
                        val = Decimal(str(match.group(1)))
                        # "days" 패턴인 경우 8시간 곱하기
                        if "day" in pattern.lower():
                            val = val * Decimal("8")
                        unit3 = val
                        break
                    except:
                        continue

            # Method 2: QTY 컬럼에서 추출
            if unit2 is None:
                # MANPOWER_*_QTY, LABOUR_*_QTY 컬럼 검색
                for col in row.index:
                    col_str = str(col).upper()
                    if (
                        "MANPOWER" in col_str
                        or "LABOUR" in col_str
                        or "FOREMAN" in col_str
                    ) and "_QTY" in col_str:
                        qty_val = self._clean_decimal(row.get(col))
                        if qty_val and qty_val > 0:
                            unit2 = qty_val
                            break

            # Method 3: 기본값 (최소 1명 가정)
            if unit2 is None:
                unit2 = Decimal("1.00")

            if unit3 is None:
                # Rate에서 시간 역산 시도
                amount = self._clean_decimal(row.get("Total_Amount_AED"))
                if amount and unit2 and unit2 > 0:
                    # 시간당 요율 가정 (예: 100 AED/hour)
                    # amount / (unit2 * rate_per_hour) = unit3
                    # 일단 기본값 사용
                    pass
                unit3 = Decimal("1.00")  # 기본값

            return Decimal("0"), unit2, unit3

        # Heavy Lift 패턴
        if "HEAVY LIFT" in subject or "LIFT" in subject:
            # unit1=FRT 수량 (실제로는 데이터에서 추출)
            # FRT 컬럼이 있으면 사용, 없으면 1
            for col in row.index:
                col_str = str(col).upper()
                if "FRT" in col_str and "_QTY" in col_str:
                    frt_qty = self._clean_decimal(row.get(col))
                    if frt_qty and frt_qty > 0:
                        return frt_qty, Decimal("1"), Decimal("1")
            return Decimal("1"), Decimal("1"), Decimal("1")

        # 기본
        return Decimal("1"), Decimal("1"), Decimal("1")

    def _calculate_rate_and_amount(self, row: pd.Series) -> Tuple[Decimal, Decimal]:
        """
        Rate와 Amount 계산

        우선순위:
        1. 원본 Total_Amount_AED 사용
        2. QTY/AMOUNT에서 역산
        """
        # 원본 금액
        total_amount = self._clean_decimal(row.get("Total_Amount_AED"))

        if total_amount is not None:
            amount = self._round_dec(total_amount)

            # Rate 역산: amount / (unit1 * unit2 * unit3)
            unit1, unit2, unit3 = self._infer_units(row)
            unit_product = unit1 * unit2 * unit3

            if unit_product > 0:
                rate = self._round_dec(amount / unit_product)
            else:
                rate = amount

            return rate, amount

        # QTY/AMOUNT에서 합산
        total_qty = Decimal("0")
        total_amt = Decimal("0")

        for qty_col, amount_col in self.qty_amount_pairs:
            qty = self._clean_decimal(row.get(qty_col))
            amt = self._clean_decimal(row.get(amount_col))

            if amt:
                total_amt += amt
            if qty:
                total_qty += qty

        if total_amt > 0:
            amount = self._round_dec(total_amt)
            if total_qty > 0:
                rate = self._round_dec(total_amt / total_qty)
            else:
                rate = amount
            return rate, amount

        return Decimal("0.00"), Decimal("0.00")

    def transform_row_to_standard_line(
        self, row: pd.Series, line_no: int
    ) -> StandardLine:
        """행을 표준 Lines 스키마로 변환"""
        # 기본 정보
        invoice_no = str(row.get("INVOICE NUMBER", "UNKNOWN"))
        tariff_id = self._infer_tariff_id(row)
        description = str(row.get("SUBJECT", ""))

        # Units
        unit1, unit2, unit3 = self._infer_units(row)

        # Rate & Amount
        rate, amount_excl_tax = self._calculate_rate_and_amount(row)

        # Tax (현재 데이터는 VAT 0%)
        tax_rate_pct = Decimal("0.00")
        tax_amount = Decimal("0.00")
        total_incl_tax = amount_excl_tax + tax_amount

        # calc_check
        calculated_amount = self._round_dec(unit1 * unit2 * unit3 * rate)
        calc_check = abs(calculated_amount - amount_excl_tax) <= TOLERANCE

        # Evidence: p{n},row{m} 형식 (P.MD 요구사항)
        # 페이지 번호가 없으면 row{m}만 사용
        # Excel의 경우 행 번호를 사용
        page_num = None  # 페이지 정보가 있으면 사용 (예: row.get("page_number"))
        if page_num is not None:
            evidence = f"p{page_num},row{line_no}"
        else:
            evidence = f"row{line_no}"

        return StandardLine(
            invoice_no=invoice_no,
            line_no=line_no,
            tariff_id=tariff_id,
            description=description,
            unit1=unit1,
            unit2=unit2,
            unit3=unit3,
            rate=rate,
            amount_excl_tax=amount_excl_tax,
            tax_rate_pct=tax_rate_pct,
            tax_amount=tax_amount,
            total_incl_tax=total_incl_tax,
            calc_check=calc_check,
            evidence=evidence,
        )

    def transform_all(self) -> List[StandardLine]:
        """모든 행 변환"""
        print("=" * 80)
        print("[Phase 1] CSV → Standard Lines Schema")
        print("=" * 80)

        lines = []

        for idx, row in self.df.iterrows():
            line = self.transform_row_to_standard_line(row, idx + 1)
            lines.append(line)

            if (idx + 1) % 100 == 0:
                print(f"진행: {idx + 1}/{len(self.df)} 행 변환")

        print(f"\n[OK] Phase 1 완료: {len(lines)} 표준 Lines 생성")

        # 통계
        calc_check_pass = sum(1 for line in lines if line.calc_check)
        print(
            f"   calc_check 통과: {calc_check_pass}/{len(lines)} ({calc_check_pass/len(lines)*100:.2f}%)"
        )

        return lines


# ============================================================
# PHASE 2: LINES → COST CENTER + PRICE CENTER + EA SLOTS
# ============================================================


class Phase2Allocator:
    """Phase 2: Cost Center 매핑 + Price Center 분개 + EA 슬롯 패킹 (v3.0 개선)"""

    # Cost Center 매핑 규칙 (간소화 - 백업용)
    COST_CENTER_MAP = {
        "AGENCY.*CARGO.*CLEARANCE": "CONTRACT (AF FOR CC)",
        "AGENCY.*BERTHING": "CONTRACT (AF FOR BA)",
        "AGENCY.*FW.*SUPPLY": "CONTRACT (AF FOR FW)",
        "PORT.*DUE": "PORT DUES & SERVICES",
        "CHANNEL": "CHANNEL TRANSIT CHARGES",
        "WASTE": "WASTE HANDLING",
        "BULK.*MATERIAL": "BULK MATERIAL HANDLING",
        "HEAVY.*LIFT": "PORT HANDLING SERVICES",
        "LABOUR": "LABOUR CHARGE",
        "FOREMAN": "SUPERVISION/WINCH",
        "EQUIPMENT": "EQUIPMENT HIRE",
        "HANDLING.*FEE": "OFCO HANDLING FEE",
        "PERMIT": "PERMITS & CERTIFICATES",
        "DOCUMENT": "DOCUMENT PROCESSING",
    }

    # Price Center 우선순위
    PRICE_CENTER_PRIORITY = {
        "A": ["PORT DUE", "CHANNEL", "WASTE", "BULK", "HEAVY LIFT"],
        "B": ["EQUIPMENT", "LABOUR", "FOREMAN", "MANPOWER"],
        "C": ["AGENCY", "PERMIT", "DOCUMENT", "GATE", "ADMIN"],
    }

    def __init__(
        self, lines: List[StandardLine], json_rules_path: Optional[str] = None
    ):
        self.lines = lines
        self.mapping_engine = None

        # V3 매핑 엔진 로드 (있는 경우)
        if json_rules_path:
            try:
                # V3 매핑 엔진 import (pipeline_docs 구조)
                mapping_scripts_path = Path(__file__).parent.parent / "pipeline_steps" / "step_04_phase2_mapping" / "scripts"
                sys.path.insert(0, str(mapping_scripts_path))
                from ofco_mapping_v3 import OFCOMappingEngineV3

                self.mapping_engine = OFCOMappingEngineV3(json_rules_path)
            except ImportError:
                # 상대 경로로 시도
                # pipeline_docs 구조에서 매핑 엔진 찾기
                mapping_scripts_path = Path(__file__).parent.parent / "pipeline_steps" / "step_04_phase2_mapping" / "scripts"
                if mapping_scripts_path.exists():
                    sys.path.insert(0, str(mapping_scripts_path))
                else:
                    # fallback: MAPPING 폴더 또는 상위 폴더
                    mapping_path = Path(__file__).parent / "MAPPING"
                    if mapping_path.exists():
                        sys.path.insert(0, str(mapping_path))
                    else:
                        sys.path.insert(0, str(Path(__file__).parent.parent))
                try:
                    from ofco_mapping_v3 import OFCOMappingEngineV3

                    # JSON 규칙 경로 자동 탐색 (pipeline_docs 구조 우선)
                    json_path = (
                        Path(__file__).parent.parent / "pipeline_steps" / "step_04_phase2_mapping" / "config"
                        / "subject_cost_center_mapping.json"
                    )
                    if not json_path.exists():
                        json_path = (
                            Path(__file__).parent / "ofco_pipeline" / "config"
                            / "subject_cost_center_mapping.json"
                        )
                    if not json_path.exists():
                        json_path = (
                            Path(__file__).parent / "MAPPING"
                            / "subject_cost_center_mapping.json"
                        )
                    if json_path.exists():
                        self.mapping_engine = OFCOMappingEngineV3(str(json_path))
                except:
                    pass

    def map_cost_center(self, line: StandardLine) -> Tuple[str, str, str, str]:
        """
        Cost Center 매핑 (v3.0 개선: 다층 매칭 전략)

        Returns:
            (COST_MAIN, COST_CENTER_A, COST_CENTER_B, PRICE_CENTER)
        """
        subject = line.description

        # Priority 1: JSON 규칙 (V3 매핑 엔진)
        if self.mapping_engine:
            result = self.mapping_engine.predict(subject)
            if result.get("method") != "default_fallback":
                return (
                    result.get("cost_main", "PORT HANDLING"),
                    result.get("cost_center_a", "PORT HANDLING CHARGE"),
                    result.get("cost_center_b", "OTHERS"),
                    result.get("price_center", "OTHERS"),
                )

        # Priority 2: 백업 패턴 매칭
        desc_upper = subject.upper()
        for pattern, cc in self.COST_CENTER_MAP.items():
            if re.search(pattern, desc_upper):
                # 간단한 추론 (패턴 기반)
                if "CONTRACT" in cc:
                    return ("CONTRACT", cc, cc.replace("CONTRACT ", ""), "OTHERS")
                elif "PORT" in cc:
                    return ("PORT HANDLING", "PORT HANDLING CHARGE", cc, "OTHERS")
                else:
                    return ("PORT HANDLING", "PORT HANDLING CHARGE", cc, "OTHERS")

        # Priority 3: 기본값
        return ("PORT HANDLING", "PORT HANDLING CHARGE", "OTHERS", "[EXT] Others")

    def allocate_price_center(
        self, line: StandardLine
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Price Center A/B/C 분개

        규칙:
        - A: 공식 요율 기반 (Port Dues, Channel, Bulk 등)
        - B: 자원/장비/인력
        - C: 수수료/패스스루
        """
        desc_upper = line.description.upper()
        amount = line.amount_excl_tax

        # 기본: 전액 A
        a, b, c = amount, Decimal("0"), Decimal("0")

        # B 카테고리 판정
        for keyword in self.PRICE_CENTER_PRIORITY["B"]:
            if keyword in desc_upper:
                b = amount
                a = Decimal("0")
                break

        # C 카테고리 판정
        if a == amount:  # 아직 A인 경우
            for keyword in self.PRICE_CENTER_PRIORITY["C"]:
                if keyword in desc_upper:
                    c = amount
                    a = Decimal("0")
                    break

        return a, b, c

    def process_line(self, line: StandardLine) -> StandardLine:
        """단일 라인 처리 (v3.0 개선)"""
        # Cost Center 매핑 (전체 계층 반환)
        cost_main, cost_center_a, cost_center_b, price_center = self.map_cost_center(
            line
        )
        line.cost_center = cost_center_b  # 기존 필드 유지 (COST CENTER B)
        # 추가 필드 저장 (나중에 확장 가능)
        line.cost_main = cost_main
        line.cost_center_a = cost_center_a
        line.price_center_name = price_center

        # Price Center 분개
        line.price_center_a, line.price_center_b, line.price_center_c = (
            self.allocate_price_center(line)
        )

        return line

    def process_all(self) -> List[StandardLine]:
        """모든 라인 처리"""
        print("\n" + "=" * 80)
        print("[Phase 2] Cost Center + Price Center 매핑")
        print("=" * 80)

        processed_lines = []

        for line in self.lines:
            processed_line = self.process_line(line)
            processed_lines.append(processed_line)

        print(f"\n[OK] Phase 2 완료: {len(processed_lines)} 라인 처리")

        # 통계
        cc_unmapped = sum(
            1
            for line in processed_lines
            if line.cost_center == "[EXT] Others" or line.cost_center == "OTHERS"
        )
        total_lines = len(processed_lines)
        mapped_count = total_lines - cc_unmapped
        mapping_rate = (mapped_count / total_lines * 100) if total_lines > 0 else 0
        print(
            f"   Cost Center 매핑: {mapped_count}/{total_lines} ({mapping_rate:.2f}%)"
        )
        print(f"   UNMAPPED: {cc_unmapped} ({100 - mapping_rate:.2f}%)")

        # V3 엔진 통계 (있는 경우)
        if self.mapping_engine:
            stats = self.mapping_engine.statistics
            print(f"   V3 엔진 통계: 총 {stats['total_predictions']} 예측")
            print(f"     - High confidence: {stats['high_confidence']}")
            print(f"     - Medium confidence: {stats['medium_confidence']}")
            print(f"     - Low confidence: {stats['low_confidence']}")

        return processed_lines


# ============================================================
# EA SLOT PACKER (v2 - 금액 우선순위)
# ============================================================


class EASlotPacker:
    """EA 슬롯 패킹 (v3.0 - 금액 우선순위 + 라인 분할)"""

    def __init__(self, df: pd.DataFrame, lines: List[StandardLine]):
        self.df = df
        self.lines = lines
        self.qty_amount_pairs = self._identify_qty_amount_pairs()
        self.split_count = 0  # 분할된 라인 수 추적

    def _identify_qty_amount_pairs(self) -> List[Tuple[Any, Any]]:
        """QTY/AMOUNT 컬럼 쌍 식별"""
        pairs = []
        # 컬럼 이름을 문자열로 변환
        qty_cols = [str(col) for col in self.df.columns if str(col).endswith("_QTY")]

        for qty_col_str in qty_cols:
            base_name = qty_col_str.replace("_QTY", "")
            amount_col_str = base_name + "_AMOUNT"
            # 컬럼 이름도 문자열로 변환하여 비교
            df_cols_str = [str(col) for col in self.df.columns]
            if amount_col_str in df_cols_str:
                # 원본 컬럼 이름 찾기
                amount_col_orig = next(
                    col for col in self.df.columns if str(col) == amount_col_str
                )
                qty_col_orig = next(
                    col for col in self.df.columns if str(col) == qty_col_str
                )
                pairs.append((qty_col_orig, amount_col_orig))

        return pairs

    def _clean_decimal(self, value: Any) -> Optional[Decimal]:
        """숫자 정제"""
        if pd.isna(value) or value == "":
            return None
        try:
            return Decimal(str(value).replace(",", ""))
        except:
            return None

    def pack_row_to_ea_slots(
        self, row: pd.Series, return_overflow: bool = False
    ) -> Tuple[List[EASlot], List[Dict]]:
        """
        단일 행을 EA 슬롯으로 패킹 (v3.0 - 금액 우선순위 + 라인 분할 지원)

        Args:
            row: DataFrame 행
            return_overflow: True이면 overflow 항목도 반환

        Returns:
            (ea_slots, overflow_items) - EA 슬롯과 넘치는 항목들
        """
        # 항목 수집
        items = []

        for qty_col, amount_col in self.qty_amount_pairs:
            qty = self._clean_decimal(row.get(qty_col))
            amount = self._clean_decimal(row.get(amount_col))

            if amount and amount > 0:
                name = qty_col.replace("_QTY", "")

                # Rate 역산
                if qty and qty > 0:
                    rate = (amount / qty).quantize(Decimal("0.01"))
                else:
                    qty = Decimal("1.00")
                    rate = amount

                items.append({"name": name, "qty": qty, "rate": rate, "amount": amount})

        # 금액 큰 순서로 정렬 (v2/v3 핵심 개선!)
        items.sort(key=lambda x: x["amount"], reverse=True)

        # EA 슬롯 생성 (최대 4개)
        ea_slots = []
        for i, item in enumerate(items[:MAX_EA_SLOTS]):
            ea_slots.append(
                EASlot(
                    slot_no=i + 1,
                    name=item["name"],
                    qty=item["qty"],
                    rate=item["rate"],
                    amount=item["amount"],
                )
            )

        # 빈 슬롯 채우기
        while len(ea_slots) < MAX_EA_SLOTS:
            ea_slots.append(
                EASlot(
                    slot_no=len(ea_slots) + 1,
                    name=None,
                    qty=Decimal("0"),
                    rate=Decimal("0"),
                    amount=Decimal("0"),
                )
            )

        # Overflow 항목 (5개 이상인 경우)
        overflow_items = items[MAX_EA_SLOTS:] if return_overflow else []

        return ea_slots, overflow_items

    def pack_all(self) -> pd.DataFrame:
        """모든 행 EA 슬롯 패킹 (v3.0 - 라인 분할 지원)"""
        print("\n" + "=" * 80)
        print("[Phase 3] EA 슬롯 패킹 (v3.0 - 금액 우선순위 + 라인 분할)")
        print("=" * 80)

        ea_results = []
        split_rows = []  # 분할된 라인 저장

        for idx, row in self.df.iterrows():
            # EA 슬롯 패킹 (overflow 포함)
            ea_slots, overflow_items = self.pack_row_to_ea_slots(
                row, return_overflow=True
            )

            # 기본 EA 슬롯 딕셔너리 생성
            ea_dict = {}
            for slot in ea_slots:
                ea_dict.update(slot.to_dict())

            # 라인 합계
            ea_dict["EA_Line_Amount"] = float(sum(slot.amount for slot in ea_slots))

            # calc_check
            original_amount = self._clean_decimal(
                row.get("Total_Amount_AED")
            ) or Decimal("0")
            ea_total = sum(slot.amount for slot in ea_slots)
            ea_dict["EA_calc_check"] = abs(ea_total - original_amount) <= TOLERANCE

            # Overflow 플래그
            if len(overflow_items) > 0:
                ea_dict["EA_FLAG_SPLIT"] = True
                ea_dict["EA_Overflow_Count"] = len(overflow_items)
            else:
                ea_dict["EA_FLAG_SPLIT"] = False
                ea_dict["EA_Overflow_Count"] = 0

            ea_results.append(ea_dict)

            # 라인 분할 (v3.0): 5개 이상 항목이 있는 경우
            if len(overflow_items) > 0:
                # split_and_reconcile 함수 사용 (ofco_ea_slot_v13.py에서 import)
                try:
                    import sys
                    from pathlib import Path

                    # ofco_ea_slot_v13 import (pipeline_docs 구조에서 찾기, 없으면 스킵)
                    ea_slot_path = Path(__file__).parent.parent / "pipeline_steps" / "step_06_phase3_ea_slots" / "scripts"
                    split_and_reconcile = None
                    if (ea_slot_path / "ofco_ea_slot_v13.py").exists():
                        sys.path.insert(0, str(ea_slot_path))
                        from ofco_ea_slot_v13 import split_and_reconcile
                    
                    if split_and_reconcile:
                        line_no = row.get("line_no") or row.get("NO") or (idx + 1)
                        split_row_dicts = split_and_reconcile(row, overflow_items, line_no)

                    # 분할된 라인들을 EA 슬롯 형식으로 변환
                    for split_row_dict in split_row_dicts:
                        split_ea_dict = {}
                        # EA 슬롯 정보 추출
                        for i in range(1, MAX_EA_SLOTS + 1):
                            split_ea_dict[f"EA_{i}_Name"] = split_row_dict.get(
                                f"EA_{i}_Name"
                            )
                            split_ea_dict[f"EA_{i}_Qty"] = split_row_dict.get(
                                f"EA_{i}_Qty"
                            )
                            split_ea_dict[f"EA_{i}_Rate"] = split_row_dict.get(
                                f"EA_{i}_Rate"
                            )
                            split_ea_dict[f"EA_{i}_Amount"] = split_row_dict.get(
                                f"EA_{i}_Amount"
                            )

                        split_ea_dict["EA_Line_Amount"] = split_row_dict.get(
                            "EA_Total_Amount", 0.0
                        )
                        split_ea_dict["EA_calc_check"] = split_row_dict.get(
                            "calc_check", False
                        )
                        split_ea_dict["EA_FLAG_SPLIT"] = True
                        split_ea_dict["EA_Overflow_Count"] = 0

                        split_rows.append(split_ea_dict)
                        self.split_count += 1

                except ImportError:
                    # split_and_reconcile 함수를 찾을 수 없으면 스킵
                    pass

        # 원본 + 분할 라인 결합
        all_ea_results = ea_results + split_rows
        ea_df = pd.DataFrame(all_ea_results)

        print(f"\n[OK] EA 슬롯 패킹 완료: {len(ea_results)} 행 (원본)")
        if self.split_count > 0:
            print(f"   라인 분할: {self.split_count}개 새 라인 추가")

        # 통계
        if len(ea_df) > 0:
            calc_check_pass = (
                ea_df["EA_calc_check"].sum() if "EA_calc_check" in ea_df.columns else 0
            )
            calc_check_total = (
                ea_df["EA_calc_check"].notna().sum()
                if "EA_calc_check" in ea_df.columns
                else len(ea_df)
            )
            if calc_check_total > 0:
                print(
                    f"   calc_check 통과: {calc_check_pass}/{calc_check_total} ({calc_check_pass/calc_check_total*100:.2f}%)"
                )

        return ea_df


# ============================================================
# MAIN PIPELINE
# ============================================================


def main():
    """메인 파이프라인 실행"""
    print("=" * 80)
    print("[PIPELINE] OFCO Complete Pipeline v3.0")
    print("=" * 80)
    print("\nPhase 1: CSV -> Standard Lines")
    print("Phase 2: Lines -> Cost Center + Price Center")
    print("Phase 3: Lines -> EA Slots\n")

    # Excel 파일 로드 (CSV 대신 Excel 사용)
    print("[Step 1/6] Excel 파일 로드...")
    excel_path = Path(__file__).parent / "OFCO INVOICE 20251103.xlsx"
    if not excel_path.exists():
        # 상대 경로로 재시도
        excel_path = Path("OFCO INVOICE 20251103.xlsx")
    if not excel_path.exists():
        # 대체 파일명 시도
        excel_path = Path(__file__).parent / "OFCO INVOICE.xlsx"
    if not excel_path.exists():
        # 상대 경로로 재시도
        excel_path = Path("OFCO INVOICE.xlsx")

    if excel_path.exists():
        # 첫 번째 시트 읽기 (자동 감지)
        try:
            df = pd.read_excel(excel_path, sheet_name=0)  # 첫 번째 시트
            print(f"[OK] {len(df)} 행, {len(df.columns)} 컬럼 로드됨\n")
        except Exception as e:
            # LIST 시트가 없으면 첫 번째 시트 사용
            xl = pd.ExcelFile(excel_path)
            print(f"사용 가능한 시트: {xl.sheet_names}")
            df = pd.read_excel(excel_path, sheet_name=xl.sheet_names[0])
            print(
                f"[OK] {len(df)} 행, {len(df.columns)} 컬럼 로드됨 (시트: {xl.sheet_names[0]})\n"
            )
    else:
        print(f"[ERROR] 파일을 찾을 수 없습니다: {excel_path}")
        print("사용 가능한 파일 목록을 확인하세요.")
        return None, None, None

    # Phase 1: 표준 Lines 스키마 변환
    print("[Step 2/6] Phase 1 실행...")
    phase1 = Phase1Transformer(df)
    standard_lines = phase1.transform_all()

    # Phase 2: Cost Center + Price Center
    print("\n[Step 3/6] Phase 2 실행...")
    # JSON 규칙 경로 자동 탐색 (표준 위치 우선)
    import sys

    # 표준 위치 우선 탐색 (pipeline_docs 구조)
    json_rules_path = (
        Path(__file__).parent.parent / "pipeline_steps" / "step_04_phase2_mapping" / "config"
        / "subject_cost_center_mapping.json"
    )
    if not json_rules_path.exists():
        json_rules_path = (
            Path(__file__).parent / "ofco_pipeline" / "config" / "subject_cost_center_mapping.json"
        )
    if not json_rules_path.exists():
        json_rules_path = Path(__file__).parent / "MAPPING" / "subject_cost_center_mapping.json"
    if not json_rules_path.exists():
        # 상대 경로로 재시도
        json_rules_path = Path("ofco_pipeline/config/subject_cost_center_mapping.json")

    phase2 = Phase2Allocator(
        standard_lines, str(json_rules_path) if json_rules_path.exists() else None
    )
    processed_lines = phase2.process_all()

    # Lines to DataFrame
    print("\n[Step 4/6] Lines DataFrame 생성...")
    lines_df = pd.DataFrame([line.to_dict() for line in processed_lines])
    print(f"[OK] Lines DataFrame: {len(lines_df)} 행")
    
    # Phase 1 헤더 정렬 (HeaderCore 사용)
    print("  [HeaderCore] Phase 1 헤더 정렬 중...")
    header_core = get_header_core()
    
    # StandardLine dataclass 필드명을 기준 헤더와 매핑
    standard_line_fields = [
        "invoice_no", "line_no", "tariff_id", "description",
        "unit1", "unit2", "unit3", "rate",
        "amount_excl_tax", "tax_rate_pct", "tax_amount", "total_incl_tax",
        "calc_check", "evidence",
        "cost_center", "price_center_a", "price_center_b", "price_center_c",
        "cost_main", "cost_center_a", "price_center_name"
    ]
    header_core.add_phase_headers(1, standard_line_fields)
    
    # OFCO INVOICE.xlsx 순서에 맞게 정렬
    lines_df = header_core.reorder_dataframe(lines_df, phase=1, fill_missing=False)
    print(f"  [HeaderCore] Phase 1 헤더 정렬 완료: {len(lines_df.columns)} 컬럼")

    # Phase 3: EA 슬롯 패킹
    print("\n[Step 5/6] EA 슬롯 패킹...")

    # 환경 변수 확인: USE_NEW_EA (기본값: True)
    import os

    USE_NEW_EA = os.getenv("USE_NEW_EA", "True").lower() == "true"

    if USE_NEW_EA:
        # 새로운 EA 할당 로직 (Adapter 방식)
        print("  [NEW] 우선순위 기반 EA 할당 사용 (ofco_ea_allocator_v1p3)")

        try:
            from ofco_pipeline_integration_scaffold import (
                allocate_ea,
                check_pc_sums,
                validate_invoice_totals,
            )

            # 원본 DataFrame과 Lines DataFrame 병합
            # allocate_ea()는 *_QTY/*_AMOUNT 컬럼이 있는 원본 DataFrame이 필요
            # lines_df에 원본 DataFrame의 QTY/AMOUNT 컬럼 정보 추가
            merged_df = df.reset_index(drop=True).join(
                lines_df.reset_index(drop=True), rsuffix="_lines"
            )

            # Price Center A/B/C 합계 검증
            merged_df = check_pc_sums(
                merged_df,
                col_a="price_center_a",
                col_b="price_center_b",
                col_c="price_center_c",
                ref_col="amount_excl_tax",
            )

            # EA 슬롯 할당 (우선순위 정렬, 플래그, 검증, 스플릿)
            # allocate_ea()는 *_QTY/*_AMOUNT 컬럼을 찾아서 처리
            ea_df_new = allocate_ea(merged_df)

            # 컬럼명 일치를 위해 기존 형식으로 변환 (필요 시)
            ea_df = ea_df_new

            print(f"  [OK] EA 할당 완료: {len(ea_df)} 행")

        except Exception as e:
            import traceback

            print(f"  [ERROR] 새로운 EA 할당 로직 실패: {e}")
            print(f"  [ERROR] 상세: {traceback.format_exc()}")
            print("  [FALLBACK] 기존 로직으로 전환...")
            USE_NEW_EA = False

    if not USE_NEW_EA:
        # 기존 로직 (롤백용)
        print("  [LEGACY] 기존 EA 할당 로직 사용")
        packer = EASlotPacker(df, processed_lines)
        ea_df = packer.pack_all()

    # 최종 결합
    print("\n[Step 6/6] 최종 결과 생성...")
    
    # 각 DataFrame을 HeaderCore로 정렬 (Phase별)
    print("  [HeaderCore] 최종 결합 전 헤더 정렬 중...")
    header_core = get_header_core()
    
    # 원본 DataFrame 정렬 (기준 헤더 순서)
    df_reordered = header_core.reorder_dataframe(df, phase=None, fill_missing=False)
    
    # Standard_Lines DataFrame 정렬 (Phase 1)
    lines_df_reordered = header_core.reorder_dataframe(lines_df, phase=1, fill_missing=False)
    
    # EA_Slots DataFrame 정렬 (Phase 3)
    ea_df_reordered = header_core.reorder_dataframe(ea_df, phase=3, fill_missing=False)
    
    # 결합
    final_df = pd.concat(
        [
            df_reordered.reset_index(drop=True),
            lines_df_reordered.reset_index(drop=True),
            ea_df_reordered.reset_index(drop=True),
        ],
        axis=1,
    )
    
    # 최종 결합 후 전체 정렬 (OFCO INVOICE.xlsx 순서)
    final_df = header_core.reorder_dataframe(final_df, phase=None, fill_missing=True)
    
    print(f"[OK] 최종 DataFrame: {len(final_df)} 행, {len(final_df.columns)} 컬럼")

    # Invoice-level 검증 (USE_NEW_EA인 경우)
    invoice_checks = None
    if USE_NEW_EA and "allocate_ea" in locals():
        print("\n[Step 6.5/6] Invoice 합계 검증...")
        try:
            # 인보이스 헤더 합계 추출 (원본 DataFrame에서 또는 메타데이터에서)
            # 일단 ea_df에 invoice_no 컬럼이 있다고 가정
            if "invoice_no" in ea_df.columns:
                invoice_checks = validate_invoice_totals(
                    ea_df,
                    invoice_col="invoice_no",
                    ref_excl_col="invoice_total_excl_tax",  # 헤더에서 추출 필요
                    ref_tax_col="invoice_tax_total",
                    ref_incl_col="invoice_total_incl_tax",
                )
                if invoice_checks is not None and len(invoice_checks) > 0:
                    # check_excl, check_tax, check_incl 통계
                    excl_pass = (
                        invoice_checks.get("check_excl", pd.Series()).sum()
                        if "check_excl" in invoice_checks.columns
                        else 0
                    )
                    tax_pass = (
                        invoice_checks.get("check_tax", pd.Series()).sum()
                        if "check_tax" in invoice_checks.columns
                        else 0
                    )
                    incl_pass = (
                        invoice_checks.get("check_incl", pd.Series()).sum()
                        if "check_incl" in invoice_checks.columns
                        else 0
                    )
                    total_invoices = len(invoice_checks)
                    print(f"  [OK] 인보이스 검증 완료: {total_invoices}개 인보이스")
                    print(f"    - Excl VAT 검증: {excl_pass}/{total_invoices}")
                    print(f"    - Tax 검증: {tax_pass}/{total_invoices}")
                    print(f"    - Incl VAT 검증: {incl_pass}/{total_invoices}")
        except Exception as e:
            print(f"  [WARNING] Invoice 검증 스킵: {e}")

    # 저장
    output_dir = Path(__file__).parent
    output_path = output_dir / "ofco_complete_pipeline_v3.xlsx"
    print(f"\n[SAVE] 저장 중: {output_path}")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="Complete_Pipeline", index=False)
        lines_df.to_excel(writer, sheet_name="Standard_Lines", index=False)
        ea_df.to_excel(writer, sheet_name="EA_Slots", index=False)

    print(f"[OK] 저장 완료!\n")

    # 최종 통계
    print("=" * 80)
    print("[STATS] 최종 통계")
    print("=" * 80)
    print(f"총 처리 행: {len(final_df)}")
    print(
        f"Standard Lines calc_check: {lines_df['calc_check'].sum()}/{len(lines_df)} "
        f"({lines_df['calc_check'].mean()*100:.2f}%)"
    )
    # EA calc_check 통계 (컬럼명이 다를 수 있음)
    if "EA_calc_check" in ea_df.columns:
        calc_check_pass = ea_df["EA_calc_check"].sum()
        calc_check_total = len(ea_df)
        print(
            f"EA calc_check: {calc_check_pass}/{calc_check_total} "
            f"({calc_check_pass/calc_check_total*100:.2f}%)"
        )
    elif "calc_check" in ea_df.columns:
        calc_check_pass = (
            ea_df["calc_check"].sum()
            if ea_df["calc_check"].dtype == "bool"
            else (ea_df["calc_check"] == True).sum()
        )
        calc_check_total = len(ea_df)
        print(
            f"EA calc_check: {calc_check_pass}/{calc_check_total} "
            f"({calc_check_pass/calc_check_total*100:.2f}%)"
        )
    else:
        print(
            f"EA calc_check: 컬럼을 찾을 수 없음 (사용 가능한 컬럼: {list(ea_df.columns)[:10]}...)"
        )

    # calc_status 통계 (USE_NEW_EA인 경우)
    if USE_NEW_EA and "calc_status" in ea_df.columns:
        status_counts = ea_df["calc_status"].value_counts()
        print(f"  calc_status 분포:")
        for status, count in status_counts.items():
            print(f"    - {status}: {count}")

    # 플래그 통계 (USE_NEW_EA인 경우)
    if USE_NEW_EA:
        flag_cols = [col for col in ea_df.columns if col.startswith("FLAG_")]
        if flag_cols:
            print(f"  플래그 통계:")
            for flag_col in flag_cols:
                flag_count = (
                    (ea_df[flag_col] == 1).sum()
                    if ea_df[flag_col].dtype in ["int64", "float64"]
                    else ea_df[flag_col].sum()
                )
                print(f"    - {flag_col}: {flag_count}")

    # VAT 및 total_check 통계 (USE_NEW_EA인 경우)
    if USE_NEW_EA and "vat_check" in ea_df.columns:
        vat_check_pass = (
            (ea_df["vat_check"] == True).sum()
            if ea_df["vat_check"].dtype == "bool"
            else (ea_df["vat_check"] == "True").sum()
        )
        vat_check_total = ea_df["vat_check"].notna().sum()
        if vat_check_total > 0:
            print(
                f"  vat_check: {vat_check_pass}/{vat_check_total} ({vat_check_pass/vat_check_total*100:.2f}%)"
            )

    if USE_NEW_EA and "total_check" in ea_df.columns:
        total_check_pass = (
            (ea_df["total_check"] == True).sum()
            if ea_df["total_check"].dtype == "bool"
            else (ea_df["total_check"] == "True").sum()
        )
        total_check_total = ea_df["total_check"].notna().sum()
        if total_check_total > 0:
            print(
                f"  total_check: {total_check_pass}/{total_check_total} ({total_check_pass/total_check_total*100:.2f}%)"
            )
    print(
        f"Cost Center UNMAPPED: {sum(1 for line in processed_lines if line.cost_center == '[EXT] Others')}"
    )

    print("\n[OK] 파이프라인 완료!")
    print("=" * 80)

    return final_df, lines_df, ea_df


if __name__ == "__main__":
    final_df, lines_df, ea_df = main()
