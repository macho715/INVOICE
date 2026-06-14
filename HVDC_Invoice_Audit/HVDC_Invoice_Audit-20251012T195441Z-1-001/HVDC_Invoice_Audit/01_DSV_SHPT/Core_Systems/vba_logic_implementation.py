#!/usr/bin/env python3
"""
VBA Logic Python Implementation
VBA 시스템의 핵심 기능들을 Python으로 재구현하여 Excel 보고서에 통합
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class VBALogicImplementation:
    """VBA 로직의 Python 구현"""

    def __init__(self):
        self.log_entries = []

    def log_action(self, tag: str, message: str, user: str = "System"):
        """VBA LogAction 함수의 Python 구현"""
        self.log_entries.append(
            {"timestamp": datetime.now(), "tag": tag, "message": message, "user": user}
        )
        logger.info(f"[{tag}] {message}")

    def extract_formulas_from_dataframe(
        self, df: pd.DataFrame, rate_column: str = "RATE"
    ) -> pd.DataFrame:
        """
        VBA ExtractFormulasWithExclusion 함수의 Python 구현
        DataFrame에서 공식을 추출하여 Formula 컬럼에 저장
        """
        self.log_action("ExtractFormulas", "BEGIN")

        result_df = df.copy()

        # Formula 컬럼이 없으면 추가
        if "Formula" not in result_df.columns:
            # RATE 컬럼 다음에 Formula 컬럼 삽입
            if rate_column in result_df.columns:
                rate_idx = result_df.columns.get_loc(rate_column)
                columns = result_df.columns.tolist()
                columns.insert(rate_idx + 1, "Formula")
                result_df = result_df.reindex(columns=columns)
                result_df["Formula"] = ""
            else:
                result_df["Formula"] = ""

        # RATE 컬럼에서 공식 추출 (시뮬레이션)
        if rate_column in result_df.columns:
            for idx, value in result_df[rate_column].items():
                if pd.notna(value):
                    # 실제 VBA에서는 Excel 공식을 추출하지만, 여기서는 시뮬레이션
                    if isinstance(value, (int, float)) and value > 0:
                        # 간단한 공식 시뮬레이션
                        result_df.loc[idx, "Formula"] = (
                            f"'=VLOOKUP({value},RateTable,2,FALSE)"
                        )

        self.log_action("ExtractFormulas", f"Processed {len(result_df)} rows")
        return result_df

    def apply_rev_rate_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        VBA ApplyFormula_ByDynamicRemark_ExactTotal_Safe 함수의 Python 구현
        REV RATE, REV TOTAL, DIFFERENCE 계산
        """
        self.log_action("ApplyFormula", "BEGIN")

        result_df = df.copy()

        # 필요한 컬럼들 확인
        required_cols = ["RATE", "Q'TY", "TOTAL (USD)"]
        missing_cols = [col for col in required_cols if col not in result_df.columns]

        if missing_cols:
            self.log_action("ApplyFormula", f"Missing columns: {missing_cols}")
            return result_df

        # REV RATE 계산 (ROUND(RATE, 2))
        result_df["REV RATE"] = pd.to_numeric(result_df["RATE"], errors="coerce").round(
            2
        )

        # REV TOTAL 계산 (REV RATE × Q'TY)
        qty_numeric = pd.to_numeric(result_df["Q'TY"], errors="coerce")
        result_df["REV TOTAL"] = result_df["REV RATE"] * qty_numeric

        # DIFFERENCE 계산 (REV TOTAL - TOTAL (USD))
        total_numeric = pd.to_numeric(result_df["TOTAL (USD)"], errors="coerce")
        result_df["DIFFERENCE"] = result_df["REV TOTAL"] - total_numeric

        # 숫자 형식 적용 (소수점 2자리)
        for col in ["REV RATE", "REV TOTAL", "DIFFERENCE"]:
            result_df[col] = result_df[col].round(2)

        self.log_action(
            "ApplyFormula", f"Calculated REV columns for {len(result_df)} rows"
        )
        return result_df

    def compile_master_data(
        self,
        sheets_data: Dict[str, pd.DataFrame],
        job_numbers: Dict[str, str] = None,
        order_refs: Dict[str, str] = None,
    ) -> pd.DataFrame:
        """
        VBA CompileAllSheets 함수의 Python 구현
        모든 시트 데이터를 MasterData로 통합
        """
        self.log_action("CompileMaster", "BEGIN")

        master_data = []

        # 표준 헤더 정의
        standard_headers = [
            "CWI Job Number",
            "Order Ref. Number",
            "S/No",
            "RATE SOURCE",
            "DESCRIPTION",
            "RATE",
            "Formula",
            "Q'TY",
            "TOTAL (USD)",
            "REMARK",
            "REV RATE",
            "REV TOTAL",
            "DIFFERENCE",
        ]

        for sheet_name, df in sheets_data.items():
            # 제외할 시트들 스킵
            excluded_sheets = [
                "SUMMARY",
                "DEC",
                "MasterData",
                "FEB",
                "InvoiceData",
                "LOG",
            ]
            if sheet_name.upper() in [s.upper() for s in excluded_sheets]:
                continue

            if df.empty:
                continue

            # Job Number와 Order Ref 정보 가져오기
            job_num = job_numbers.get(sheet_name, "") if job_numbers else ""
            order_ref = order_refs.get(sheet_name, "") if order_refs else ""

            # S/No 컬럼을 기준으로 데이터 행 식별
            if "S/No" in df.columns:
                # 숫자 값이 있는 행만 선택
                valid_rows = df[pd.to_numeric(df["S/No"], errors="coerce").notna()]

                for _, row in valid_rows.iterrows():
                    master_row = {
                        "CWI Job Number": job_num,
                        "Order Ref. Number": order_ref,
                    }

                    # 나머지 컬럼들 추가
                    for col in standard_headers[2:]:  # S/No부터 시작
                        if col in df.columns:
                            master_row[col] = row.get(col, "")
                        else:
                            master_row[col] = ""

                    master_data.append(master_row)

        # MasterData DataFrame 생성
        master_df = pd.DataFrame(master_data, columns=standard_headers)

        self.log_action(
            "CompileMaster",
            f"Compiled {len(master_df)} rows from {len(sheets_data)} sheets",
        )
        return master_df

    def run_full_pipeline(
        self,
        sheets_data: Dict[str, pd.DataFrame],
        job_numbers: Dict[str, str] = None,
        order_refs: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        VBA RunPipeline_Final 함수의 Python 구현
        전체 3단계 파이프라인 실행
        """
        self.log_action("PIPELINE", "START")

        results = {
            "processed_sheets": {},
            "master_data": None,
            "log_entries": [],
            "summary": {},
        }

        try:
            # 1단계: Formula 추출
            for sheet_name, df in sheets_data.items():
                if not df.empty and "RATE" in df.columns:
                    processed_df = self.extract_formulas_from_dataframe(df)
                    sheets_data[sheet_name] = processed_df

            # 2단계: REV RATE 적용
            for sheet_name, df in sheets_data.items():
                if not df.empty:
                    processed_df = self.apply_rev_rate_calculations(df)
                    sheets_data[sheet_name] = processed_df
                    results["processed_sheets"][sheet_name] = processed_df

            # 3단계: 마스터 데이터 생성
            master_data = self.compile_master_data(sheets_data, job_numbers, order_refs)
            results["master_data"] = master_data

            # 요약 정보 생성
            results["summary"] = {
                "total_sheets_processed": len(results["processed_sheets"]),
                "master_data_rows": len(master_data),
                "total_rev_amount": (
                    master_data["REV TOTAL"].sum()
                    if "REV TOTAL" in master_data.columns
                    else 0
                ),
                "total_difference": (
                    master_data["DIFFERENCE"].sum()
                    if "DIFFERENCE" in master_data.columns
                    else 0
                ),
            }

            self.log_action(
                "PIPELINE", f"SUCCESS - Processed {len(sheets_data)} sheets"
            )

        except Exception as e:
            self.log_action("PIPELINE", f"ERROR: {str(e)}")
            raise

        # 로그 엔트리 추가
        results["log_entries"] = self.log_entries.copy()

        return results

    def create_log_dataframe(self) -> pd.DataFrame:
        """로그 엔트리를 DataFrame으로 변환"""
        if not self.log_entries:
            return pd.DataFrame(columns=["TIMESTAMP", "TAG", "MESSAGE", "USER"])

        return pd.DataFrame(self.log_entries).rename(
            columns={
                "timestamp": "TIMESTAMP",
                "tag": "TAG",
                "message": "MESSAGE",
                "user": "USER",
            }
        )

    def analyze_differences(
        self, df: pd.DataFrame, threshold: float = 0.01
    ) -> Dict[str, Any]:
        """DIFFERENCE 분석 결과 생성"""
        if "DIFFERENCE" not in df.columns:
            return {"error": "DIFFERENCE column not found"}

        differences = pd.to_numeric(df["DIFFERENCE"], errors="coerce").fillna(0)

        analysis = {
            "total_items": len(df),
            "items_with_differences": len(differences[abs(differences) > threshold]),
            "total_difference": differences.sum(),
            "average_difference": differences.mean(),
            "max_positive_diff": differences.max(),
            "max_negative_diff": differences.min(),
            "difference_distribution": {
                "positive": len(differences[differences > threshold]),
                "negative": len(differences[differences < -threshold]),
                "within_threshold": len(differences[abs(differences) <= threshold]),
            },
        }

        return analysis


class VBAExcelIntegrator:
    """VBA 기능을 Excel 보고서에 통합하는 클래스"""

    def __init__(self):
        self.vba_logic = VBALogicImplementation()

    def process_invoice_data_with_vba_logic(
        self, invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """인보이스 데이터에 VBA 로직 적용"""

        # 기본 데이터 구조 생성
        if "sheets_data" not in invoice_data:
            # CSV 데이터를 시트 형태로 변환
            main_df = pd.DataFrame(invoice_data.get("items", []))
            sheets_data = {"Main_Invoice": main_df}
        else:
            sheets_data = invoice_data["sheets_data"]

        # Job Numbers와 Order Refs 정보 추출
        job_numbers = invoice_data.get("job_numbers", {})
        order_refs = invoice_data.get("order_refs", {})

        # VBA 파이프라인 실행
        vba_results = self.vba_logic.run_full_pipeline(
            sheets_data=sheets_data, job_numbers=job_numbers, order_refs=order_refs
        )

        # 결과를 Excel 보고서 형태로 구성
        excel_integration_results = {
            "vba_processed_sheets": vba_results["processed_sheets"],
            "vba_master_data": vba_results["master_data"],
            "vba_log_data": self.vba_logic.create_log_dataframe(),
            "vba_analysis": {
                "formula_extraction": self._analyze_formula_extraction(
                    vba_results["processed_sheets"]
                ),
                "rev_rate_analysis": self._analyze_rev_rates(
                    vba_results["master_data"]
                ),
                "difference_analysis": self.vba_logic.analyze_differences(
                    vba_results["master_data"]
                ),
                "summary": vba_results["summary"],
            },
        }

        return excel_integration_results

    def _analyze_formula_extraction(
        self, processed_sheets: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Formula 추출 분석"""
        total_formulas = 0
        sheets_with_formulas = 0

        for sheet_name, df in processed_sheets.items():
            if "Formula" in df.columns:
                formula_count = df["Formula"].notna().sum()
                total_formulas += formula_count
                if formula_count > 0:
                    sheets_with_formulas += 1

        return {
            "total_formulas_extracted": total_formulas,
            "sheets_with_formulas": sheets_with_formulas,
            "total_sheets_processed": len(processed_sheets),
        }

    def _analyze_rev_rates(self, master_data: pd.DataFrame) -> Dict[str, Any]:
        """REV RATE 분석"""
        if master_data.empty or "REV RATE" not in master_data.columns:
            return {"error": "No REV RATE data available"}

        rev_rates = pd.to_numeric(master_data["REV RATE"], errors="coerce").fillna(0)
        rev_totals = pd.to_numeric(master_data["REV TOTAL"], errors="coerce").fillna(0)

        return {
            "total_items": len(master_data),
            "items_with_rev_rates": len(rev_rates[rev_rates > 0]),
            "average_rev_rate": rev_rates.mean(),
            "total_rev_amount": rev_totals.sum(),
            "rate_distribution": {
                "min_rate": rev_rates.min(),
                "max_rate": rev_rates.max(),
                "median_rate": rev_rates.median(),
            },
        }


def main():
    """테스트 실행"""
    print("🧪 VBA Logic Python Implementation 테스트")

    # 테스트 데이터 생성
    test_data = {
        "Sheet1": pd.DataFrame(
            {
                "S/No": [1, 2, 3],
                "DESCRIPTION": ["Item A", "Item B", "Item C"],
                "RATE": [100.0, 150.0, 200.0],
                "Q'TY": [2, 3, 1],
                "TOTAL (USD)": [200.0, 450.0, 200.0],
                "REMARK": ["Test A", "Test B", "Test C"],
            }
        )
    }

    job_numbers = {"Sheet1": "CWI-001"}
    order_refs = {"Sheet1": "ORD-001"}

    # VBA 로직 실행
    vba_logic = VBALogicImplementation()
    results = vba_logic.run_full_pipeline(test_data, job_numbers, order_refs)

    print(f"\n✅ 처리 완료:")
    print(f"  - 처리된 시트: {results['summary']['total_sheets_processed']}")
    print(f"  - 마스터 데이터 행: {results['summary']['master_data_rows']}")
    print(f"  - 총 REV 금액: ${results['summary']['total_rev_amount']:,.2f}")
    print(f"  - 총 차이: ${results['summary']['total_difference']:,.2f}")


if __name__ == "__main__":
    main()
