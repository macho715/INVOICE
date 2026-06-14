#!/usr/bin/env python3
"""
VBA Excel File Analyzer for HVDC SHPT September 2025
Extracts and validates VBA-processed data from Excel file

Version: 1.0.0
Created: 2025-10-13
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
from datetime import datetime
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VBAExcelAnalyzer:
    """
    VBA 처리된 Excel 파일 분석기

    Features:
    - VBA Formula 추출 결과 분석
    - REV RATE 계산 검증
    - MasterData 컴파일 결과 추출
    - 데이터 무결성 검증
    """

    def __init__(self, excel_file_path: str):
        """
        초기화

        Args:
            excel_file_path: VBA 처리된 Excel 파일 경로
        """
        self.excel_file_path = Path(excel_file_path)
        self.sheets_data = {}
        self.vba_results = {}
        self.validation_results = {}

        if not self.excel_file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")

    def analyze_vba_file(self) -> Dict[str, Any]:
        """
        VBA Excel 파일 전체 분석

        Returns:
            Dict: 분석 결과
        """
        logger.info(f"🔍 VBA Excel 파일 분석 시작: {self.excel_file_path}")

        try:
            # 1. 모든 시트 로드
            self._load_all_sheets()

            # 2. VBA 처리 결과 추출
            self._extract_vba_results()

            # 3. 데이터 검증
            self._validate_vba_calculations()

            # 4. 분석 결과 컴파일
            analysis_results = self._compile_analysis_results()

            logger.info("✅ VBA Excel 파일 분석 완료")
            return analysis_results

        except Exception as e:
            logger.error(f"❌ VBA Excel 파일 분석 실패: {str(e)}")
            raise

    def _load_all_sheets(self):
        """모든 시트 데이터 로드"""
        logger.info("📊 Excel 시트 로드 중...")

        try:
            # Excel 파일의 모든 시트 읽기
            excel_file = pd.ExcelFile(self.excel_file_path)
            sheet_names = excel_file.sheet_names

            logger.info(f"  📋 발견된 시트: {len(sheet_names)}개")

            for sheet_name in sheet_names:
                try:
                    # 시트 데이터 로드
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

                    # 빈 시트 제외
                    if not df.empty:
                        self.sheets_data[sheet_name] = df
                        logger.info(f"  ✅ {sheet_name}: {df.shape}")

                except Exception as e:
                    logger.warning(f"  ⚠️ {sheet_name} 로드 실패: {e}")

        except Exception as e:
            logger.error(f"❌ 시트 로드 실패: {e}")
            raise

    def _extract_vba_results(self):
        """VBA 처리 결과 추출"""
        logger.info("🔧 VBA 처리 결과 추출 중...")

        self.vba_results = {
            "formula_extraction": self._extract_formula_results(),
            "rev_rate_calculations": self._extract_rev_rate_results(),
            "master_data": self._extract_master_data(),
            "sheet_analysis": self._analyze_individual_sheets(),
        }

    def _extract_formula_results(self) -> Dict[str, Any]:
        """Formula 추출 결과 분석"""
        logger.info("  📋 Formula 추출 결과 분석...")

        formula_results = {
            "sheets_with_formulas": [],
            "formula_count": 0,
            "formula_data": [],
        }

        for sheet_name, df in self.sheets_data.items():
            # Formula 컬럼 찾기
            formula_cols = []
            for col_idx in range(df.shape[1]):
                for row_idx in range(min(5, df.shape[0])):  # 상위 5행에서 헤더 찾기
                    cell_value = str(df.iloc[row_idx, col_idx]).strip().upper()
                    if "FORMULA" in cell_value:
                        formula_cols.append((col_idx, row_idx))
                        break

            if formula_cols:
                formula_results["sheets_with_formulas"].append(sheet_name)

                for col_idx, header_row in formula_cols:
                    # Formula 데이터 추출
                    formula_data = []
                    for row_idx in range(header_row + 1, df.shape[0]):
                        formula_value = df.iloc[row_idx, col_idx]
                        if pd.notna(formula_value) and str(formula_value).strip():
                            formula_data.append(
                                {
                                    "sheet": sheet_name,
                                    "row": row_idx + 1,
                                    "formula": str(formula_value),
                                }
                            )

                    formula_results["formula_data"].extend(formula_data)
                    formula_results["formula_count"] += len(formula_data)

        logger.info(f"  ✅ Formula 추출: {formula_results['formula_count']}개")
        return formula_results

    def _extract_rev_rate_results(self) -> Dict[str, Any]:
        """REV RATE 계산 결과 분석"""
        logger.info("  💰 REV RATE 계산 결과 분석...")

        rev_rate_results = {
            "sheets_with_rev_rates": [],
            "calculations": [],
            "validation_summary": {},
        }

        for sheet_name, df in self.sheets_data.items():
            # REV RATE 관련 컬럼 찾기
            rev_columns = self._find_rev_rate_columns(df)

            if rev_columns:
                rev_rate_results["sheets_with_rev_rates"].append(sheet_name)

                # 계산 데이터 추출
                calculations = self._extract_calculations(df, rev_columns, sheet_name)
                rev_rate_results["calculations"].extend(calculations)

        # 검증 요약
        rev_rate_results["validation_summary"] = self._validate_rev_calculations(
            rev_rate_results["calculations"]
        )

        logger.info(
            f"  ✅ REV RATE 분석: {len(rev_rate_results['calculations'])}개 항목"
        )
        return rev_rate_results

    def _find_rev_rate_columns(self, df: pd.DataFrame) -> Dict[str, int]:
        """REV RATE 관련 컬럼 찾기"""
        columns = {}

        for col_idx in range(df.shape[1]):
            for row_idx in range(min(10, df.shape[0])):
                cell_value = str(df.iloc[row_idx, col_idx]).strip().upper()

                if "REV RATE" in cell_value or "REV_RATE" in cell_value:
                    columns["rev_rate"] = (col_idx, row_idx)
                elif "REV TOTAL" in cell_value or "REV_TOTAL" in cell_value:
                    columns["rev_total"] = (col_idx, row_idx)
                elif "DIFFERENCE" in cell_value:
                    columns["difference"] = (col_idx, row_idx)
                elif "RATE" in cell_value and "REV" not in cell_value:
                    columns["rate"] = (col_idx, row_idx)
                elif (
                    "Q'TY" in cell_value
                    or "QTY" in cell_value
                    or "QUANTITY" in cell_value
                ):
                    columns["qty"] = (col_idx, row_idx)
                elif "TOTAL" in cell_value and "REV" not in cell_value:
                    columns["total"] = (col_idx, row_idx)

        return columns

    def _extract_calculations(
        self, df: pd.DataFrame, columns: Dict, sheet_name: str
    ) -> List[Dict]:
        """계산 데이터 추출"""
        calculations = []

        if not columns:
            return calculations

        # 데이터 시작 행 찾기
        data_start_row = max([row for col, row in columns.values()]) + 1

        for row_idx in range(data_start_row, df.shape[0]):
            calc_data = {"sheet": sheet_name, "row": row_idx + 1}

            # 각 컬럼 데이터 추출
            for col_name, (col_idx, _) in columns.items():
                try:
                    value = df.iloc[row_idx, col_idx]
                    if pd.notna(value):
                        # 숫자 변환 시도
                        if isinstance(value, str):
                            value = value.replace(",", "").strip()
                            try:
                                value = float(value)
                            except:
                                pass
                        calc_data[col_name] = value
                except:
                    calc_data[col_name] = None

            # 유효한 데이터만 추가
            if any(
                pd.notna(v) and v != ""
                for v in calc_data.values()
                if isinstance(v, (int, float, str))
            ):
                calculations.append(calc_data)

        return calculations

    def _validate_rev_calculations(self, calculations: List[Dict]) -> Dict[str, Any]:
        """REV RATE 계산 검증"""
        validation = {
            "total_items": len(calculations),
            "valid_calculations": 0,
            "calculation_errors": [],
            "accuracy_rate": 0.0,
        }

        for calc in calculations:
            try:
                rate = calc.get("rate")
                qty = calc.get("qty", 1)
                rev_rate = calc.get("rev_rate")
                rev_total = calc.get("rev_total")
                total = calc.get("total")
                difference = calc.get("difference")

                # REV RATE 검증 (RATE 반올림)
                if rate is not None and rev_rate is not None:
                    expected_rev_rate = round(float(rate), 2)
                    if abs(float(rev_rate) - expected_rev_rate) > 0.01:
                        validation["calculation_errors"].append(
                            {
                                "sheet": calc["sheet"],
                                "row": calc["row"],
                                "type": "REV_RATE_ERROR",
                                "expected": expected_rev_rate,
                                "actual": rev_rate,
                            }
                        )

                # REV TOTAL 검증 (REV RATE × QTY)
                if rev_rate is not None and qty is not None and rev_total is not None:
                    expected_rev_total = round(float(rev_rate) * float(qty), 2)
                    if abs(float(rev_total) - expected_rev_total) > 0.01:
                        validation["calculation_errors"].append(
                            {
                                "sheet": calc["sheet"],
                                "row": calc["row"],
                                "type": "REV_TOTAL_ERROR",
                                "expected": expected_rev_total,
                                "actual": rev_total,
                            }
                        )

                # DIFFERENCE 검증 (REV TOTAL - TOTAL)
                if (
                    rev_total is not None
                    and total is not None
                    and difference is not None
                ):
                    expected_difference = round(float(rev_total) - float(total), 2)
                    if abs(float(difference) - expected_difference) > 0.01:
                        validation["calculation_errors"].append(
                            {
                                "sheet": calc["sheet"],
                                "row": calc["row"],
                                "type": "DIFFERENCE_ERROR",
                                "expected": expected_difference,
                                "actual": difference,
                            }
                        )

                # 오류가 없으면 유효한 계산
                if not any(
                    err["sheet"] == calc["sheet"] and err["row"] == calc["row"]
                    for err in validation["calculation_errors"]
                ):
                    validation["valid_calculations"] += 1

            except Exception as e:
                validation["calculation_errors"].append(
                    {
                        "sheet": calc["sheet"],
                        "row": calc["row"],
                        "type": "VALIDATION_ERROR",
                        "error": str(e),
                    }
                )

        # 정확도 계산
        if validation["total_items"] > 0:
            validation["accuracy_rate"] = (
                validation["valid_calculations"] / validation["total_items"]
            )

        return validation

    def _extract_master_data(self) -> Dict[str, Any]:
        """MasterData 시트 분석"""
        logger.info("  📊 MasterData 시트 분석...")

        master_data = {
            "sheet_found": False,
            "data_summary": {},
            "column_mapping": {},
            "row_count": 0,
        }

        # MasterData 시트 찾기
        master_sheet_name = None
        for sheet_name in self.sheets_data.keys():
            if "MASTER" in sheet_name.upper() or "MASTERDATA" in sheet_name.upper():
                master_sheet_name = sheet_name
                break

        if master_sheet_name:
            master_data["sheet_found"] = True
            df = self.sheets_data[master_sheet_name]

            # 헤더 찾기
            header_row = None
            for row_idx in range(min(10, df.shape[0])):
                row_str = " ".join(
                    [str(cell) for cell in df.iloc[row_idx] if pd.notna(cell)]
                )
                if any(
                    keyword in row_str.upper()
                    for keyword in ["CWI JOB", "ORDER REF", "S/NO", "DESCRIPTION"]
                ):
                    header_row = row_idx
                    break

            if header_row is not None:
                # 컬럼 매핑
                headers = df.iloc[header_row].tolist()
                master_data["column_mapping"] = {
                    i: str(header)
                    for i, header in enumerate(headers)
                    if pd.notna(header)
                }

                # 데이터 요약
                data_rows = df.iloc[header_row + 1 :]
                master_data["row_count"] = len(data_rows.dropna(how="all"))

                # 컬럼별 통계
                master_data["data_summary"] = {}
                for col_idx, col_name in master_data["column_mapping"].items():
                    col_data = data_rows.iloc[:, col_idx].dropna()
                    if len(col_data) > 0:
                        master_data["data_summary"][col_name] = {
                            "non_null_count": len(col_data),
                            "unique_count": (
                                len(col_data.unique())
                                if hasattr(col_data, "unique")
                                else 0
                            ),
                        }

        logger.info(f"  ✅ MasterData 분석 완료: {master_data['row_count']}행")
        return master_data

    def _analyze_individual_sheets(self) -> Dict[str, Any]:
        """개별 시트 분석"""
        logger.info("  📋 개별 시트 분석...")

        sheet_analysis = {}

        for sheet_name, df in self.sheets_data.items():
            analysis = {
                "shape": df.shape,
                "has_headers": False,
                "data_start_row": None,
                "columns_identified": {},
                "data_quality": {},
            }

            # 헤더 찾기
            for row_idx in range(min(10, df.shape[0])):
                row_str = " ".join(
                    [str(cell) for cell in df.iloc[row_idx] if pd.notna(cell)]
                ).upper()
                if any(
                    keyword in row_str
                    for keyword in ["S/NO", "DESCRIPTION", "RATE", "TOTAL"]
                ):
                    analysis["has_headers"] = True
                    analysis["data_start_row"] = row_idx + 1

                    # 컬럼 식별
                    headers = df.iloc[row_idx].tolist()
                    for col_idx, header in enumerate(headers):
                        if pd.notna(header):
                            header_str = str(header).strip().upper()
                            analysis["columns_identified"][col_idx] = header_str
                    break

            # 데이터 품질 분석
            if analysis["data_start_row"] is not None:
                data_section = df.iloc[analysis["data_start_row"] :]
                analysis["data_quality"] = {
                    "total_rows": len(data_section),
                    "non_empty_rows": len(data_section.dropna(how="all")),
                    "completeness": (
                        len(data_section.dropna(how="all")) / len(data_section)
                        if len(data_section) > 0
                        else 0
                    ),
                }

            sheet_analysis[sheet_name] = analysis

        logger.info(f"  ✅ {len(sheet_analysis)}개 시트 분석 완료")
        return sheet_analysis

    def _validate_vba_calculations(self):
        """VBA 계산 결과 검증"""
        logger.info("🔍 VBA 계산 검증 중...")

        self.validation_results = {
            "formula_validation": self._validate_formulas(),
            "calculation_validation": self.vba_results["rev_rate_calculations"][
                "validation_summary"
            ],
            "data_integrity": self._check_data_integrity(),
            "overall_score": 0.0,
        }

        # 전체 점수 계산
        scores = []
        if self.validation_results["calculation_validation"]["total_items"] > 0:
            scores.append(
                self.validation_results["calculation_validation"]["accuracy_rate"]
            )

        if self.validation_results["data_integrity"]["total_checks"] > 0:
            scores.append(self.validation_results["data_integrity"]["pass_rate"])

        if scores:
            self.validation_results["overall_score"] = sum(scores) / len(scores)

    def _validate_formulas(self) -> Dict[str, Any]:
        """Formula 검증"""
        formula_data = self.vba_results["formula_extraction"]["formula_data"]

        validation = {
            "total_formulas": len(formula_data),
            "valid_formulas": 0,
            "formula_patterns": {},
            "issues": [],
        }

        for formula_item in formula_data:
            formula = formula_item["formula"]

            # 패턴 분석
            if "VLOOKUP" in formula.upper():
                validation["formula_patterns"]["VLOOKUP"] = (
                    validation["formula_patterns"].get("VLOOKUP", 0) + 1
                )
            elif "=" in formula:
                validation["formula_patterns"]["CALCULATION"] = (
                    validation["formula_patterns"].get("CALCULATION", 0) + 1
                )
            else:
                validation["formula_patterns"]["OTHER"] = (
                    validation["formula_patterns"].get("OTHER", 0) + 1
                )

            # 유효성 검사
            if formula.strip() and len(formula) > 1:
                validation["valid_formulas"] += 1
            else:
                validation["issues"].append(
                    {
                        "sheet": formula_item["sheet"],
                        "row": formula_item["row"],
                        "issue": "Empty or invalid formula",
                    }
                )

        return validation

    def _check_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검사"""
        integrity = {
            "total_checks": 0,
            "passed_checks": 0,
            "pass_rate": 0.0,
            "issues": [],
        }

        # 각 시트별 데이터 무결성 검사
        for sheet_name, analysis in self.vba_results["sheet_analysis"].items():
            if analysis["has_headers"] and analysis["data_start_row"] is not None:
                integrity["total_checks"] += 1

                # 데이터 완성도 검사
                completeness = analysis["data_quality"]["completeness"]
                if completeness >= 0.8:  # 80% 이상 완성도
                    integrity["passed_checks"] += 1
                else:
                    integrity["issues"].append(
                        {
                            "sheet": sheet_name,
                            "issue": f"Low data completeness: {completeness:.2%}",
                        }
                    )

        # 통과율 계산
        if integrity["total_checks"] > 0:
            integrity["pass_rate"] = (
                integrity["passed_checks"] / integrity["total_checks"]
            )

        return integrity

    def _compile_analysis_results(self) -> Dict[str, Any]:
        """분석 결과 컴파일"""
        logger.info("📊 분석 결과 컴파일 중...")

        results = {
            "file_info": {
                "file_path": str(self.excel_file_path),
                "file_size": self.excel_file_path.stat().st_size,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_sheets": len(self.sheets_data),
            },
            "vba_results": self.vba_results,
            "validation_results": self.validation_results,
            "summary": self._generate_summary(),
        }

        return results

    def _generate_summary(self) -> Dict[str, Any]:
        """분석 요약 생성"""
        formula_count = self.vba_results["formula_extraction"]["formula_count"]
        calc_count = len(self.vba_results["rev_rate_calculations"]["calculations"])
        master_data_rows = self.vba_results["master_data"]["row_count"]
        overall_score = self.validation_results["overall_score"]

        return {
            "total_sheets_analyzed": len(self.sheets_data),
            "formulas_extracted": formula_count,
            "calculations_analyzed": calc_count,
            "master_data_rows": master_data_rows,
            "overall_validation_score": overall_score,
            "validation_status": (
                "PASS"
                if overall_score >= 0.9
                else "REVIEW" if overall_score >= 0.7 else "FAIL"
            ),
        }

    def export_results(self, output_path: str) -> bool:
        """분석 결과 내보내기"""
        try:
            results = self._compile_analysis_results()

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"✅ 분석 결과 저장: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 결과 저장 실패: {e}")
            return False


def main():
    """메인 실행 함수"""
    excel_file = "Data/DSV 202509/SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"

    try:
        analyzer = VBAExcelAnalyzer(excel_file)
        results = analyzer.analyze_vba_file()

        # 결과 출력
        print("=" * 80)
        print("🔍 VBA Excel 파일 분석 결과")
        print("=" * 80)

        summary = results["summary"]
        print(f"📊 분석된 시트 수: {summary['total_sheets_analyzed']}")
        print(f"📋 추출된 Formula: {summary['formulas_extracted']}개")
        print(f"💰 분석된 계산: {summary['calculations_analyzed']}개")
        print(f"📈 MasterData 행: {summary['master_data_rows']}개")
        print(f"✅ 검증 점수: {summary['overall_validation_score']:.2%}")
        print(f"🎯 검증 상태: {summary['validation_status']}")

        # 결과 저장
        output_path = "Results/Sept_2025/vba_analysis_results.json"
        analyzer.export_results(output_path)

        return results

    except Exception as e:
        logger.error(f"❌ VBA 분석 실패: {e}")
        return None


if __name__ == "__main__":
    main()
