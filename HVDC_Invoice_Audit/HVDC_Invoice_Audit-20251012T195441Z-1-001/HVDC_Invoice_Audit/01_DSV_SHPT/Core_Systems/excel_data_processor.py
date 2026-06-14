#!/usr/bin/env python3
"""
Excel Data Processor for SHPT PDF Integration System
JSON 결과를 Excel 친화적 형태로 변환

Version: 1.0.0
Created: 2025-10-13
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import pandas as pd
import json
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExcelDataProcessor:
    """
    PDF 통합 결과를 Excel 형태로 구조화하는 데이터 처리기

    Features:
    - JSON 결과를 Excel 친화적 형태로 변환
    - PDF 검증 결과 정규화
    - Gate 점수 계산 및 시각화 데이터 준비
    """

    def __init__(self):
        """초기화"""
        self.raw_data = None
        self.processed_data = None

    def load_json_data(self, json_path: str) -> bool:
        """
        JSON 데이터 로드

        Args:
            json_path: JSON 파일 경로

        Returns:
            bool: 로드 성공 여부
        """
        try:
            logger.info(f"Loading JSON data from: {json_path}")

            with open(json_path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)

            logger.info("JSON data loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load JSON data: {str(e)}")
            return False

    def extract_pdf_integration_stats(self) -> Dict[str, Any]:
        """
        PDF 통합 통계 추출 (Documentation 기준)

        Returns:
            Dict: PDF 통합 관련 통계
        """
        if not self.raw_data:
            return {}

        stats = {}

        # 기본 통계
        audit_info = self.raw_data.get("audit_info", {})
        statistics = self.raw_data.get("statistics", {})

        stats["total_supporting_docs"] = audit_info.get("total_supporting_docs", 0)
        stats["total_items"] = statistics.get("total_items", 0)
        stats["pass_rate"] = statistics.get("pass_rate", "0%")
        stats["total_amount_usd"] = statistics.get("total_amount_usd", 0)

        # PDF 검증 통계 (Documentation 기준)
        pdf_validation = statistics.get("pdf_validation", {})
        stats["pdf_stats"] = {
            "total_parsed": pdf_validation.get("total_parsed", 0),
            "shipments_with_pdfs": pdf_validation.get("shipments_with_pdfs", 0),
            "avg_pdfs_per_shipment": pdf_validation.get("avg_pdfs_per_shipment", 0),
            "cross_doc_pass": pdf_validation.get("cross_doc_pass", 0),
            "cross_doc_fail": pdf_validation.get("cross_doc_fail", 0),
            "demurrage_risks_found": pdf_validation.get("demurrage_risks_found", 0),
        }

        # Gate 검증 통계
        gate_validation = statistics.get("gate_validation", {})
        stats["gate_stats"] = {
            "avg_gate_score": gate_validation.get("avg_gate_score", 0),
            "gate_pass_rate": gate_validation.get("gate_pass_rate", "0%"),
            "gate_statistics": gate_validation.get("gate_statistics", {}),
        }

        return stats

    def process_supporting_docs_data(self) -> pd.DataFrame:
        """
        Supporting Documents 데이터 처리

        Returns:
            DataFrame: 증빙문서 상세 데이터
        """
        if not self.raw_data:
            return pd.DataFrame()

        supporting_docs = self.raw_data.get("supporting_docs", {})
        docs_data = []

        for shipment_id, docs in supporting_docs.items():
            for doc in docs:
                docs_data.append(
                    {
                        "shipment_id": shipment_id,
                        "file_name": doc.get("file_name", ""),
                        "doc_type": doc.get("doc_type", ""),
                        "file_size_kb": doc.get("file_size", 0) / 1024,
                        "file_path": doc.get("file_path", ""),
                        "status": "Parsed",
                    }
                )

        return pd.DataFrame(docs_data)

    def extract_gate_analysis_data(self) -> pd.DataFrame:
        """
        Gate 분석 데이터 추출 (Gate-11~14)

        Returns:
            DataFrame: Gate 분석 결과
        """
        if not self.raw_data:
            return pd.DataFrame()

        gate_stats = (
            self.raw_data.get("statistics", {})
            .get("gate_validation", {})
            .get("gate_statistics", {})
        )

        gate_data = []
        gate_definitions = {
            "Gate-11": {
                "description": "MBL Consistency Check",
                "rule": "Validates MBL numbers across documents",
            },
            "Gate-12": {
                "description": "Container Consistency Check",
                "rule": "Validates container numbers across documents",
            },
            "Gate-13": {
                "description": "Weight Consistency Check",
                "rule": "Validates weight data (±3% tolerance)",
            },
            "Gate-14": {
                "description": "Certificate Validation",
                "rule": "Validates required certificates (FANR/MOIAT)",
            },
        }

        for gate_id, definition in gate_definitions.items():
            gate_stat = gate_stats.get(gate_id, {"pass": 0, "fail": 0, "skip": 0})

            total = (
                gate_stat.get("pass", 0)
                + gate_stat.get("fail", 0)
                + gate_stat.get("skip", 0)
            )
            pass_rate = (gate_stat.get("pass", 0) / total * 100) if total > 0 else 0

            gate_data.append(
                {
                    "gate": gate_id,
                    "description": definition["description"],
                    "validation_rule": definition["rule"],
                    "pass_count": gate_stat.get("pass", 0),
                    "fail_count": gate_stat.get("fail", 0),
                    "skip_count": gate_stat.get("skip", 0),
                    "pass_rate": f"{pass_rate:.1f}%",
                }
            )

        return pd.DataFrame(gate_data)

    def extract_cross_document_issues(self) -> pd.DataFrame:
        """
        Cross-Document 이슈 추출

        Returns:
            DataFrame: Cross-Document 검증 이슈
        """
        if not self.raw_data:
            return pd.DataFrame()

        # all_results에서 cross-document 이슈 추출
        all_results = self.raw_data.get("all_results", [])
        issues_data = []

        for result in all_results:
            pdf_validation = result.get("pdf_validation", {})
            cross_doc_validation = pdf_validation.get("cross_doc_validation", {})

            if cross_doc_validation.get("status") == "FAIL":
                issues = cross_doc_validation.get("issues", [])

                for issue in issues:
                    issues_data.append(
                        {
                            "shipment_id": result.get("shipment_id", ""),
                            "issue_type": issue.get("type", ""),
                            "description": issue.get("description", ""),
                            "severity": issue.get("severity", "MEDIUM"),
                            "affected_documents": ", ".join(
                                issue.get("affected_documents", [])
                            ),
                            "recommendation": issue.get("recommendation", ""),
                        }
                    )

        return pd.DataFrame(issues_data)

    def extract_demurrage_risk_data(self) -> pd.DataFrame:
        """
        Demurrage Risk 데이터 추출

        Returns:
            DataFrame: Demurrage 리스크 분석
        """
        if not self.raw_data:
            return pd.DataFrame()

        all_results = self.raw_data.get("all_results", [])
        demurrage_data = []

        for result in all_results:
            pdf_validation = result.get("pdf_validation", {})
            demurrage_risk = pdf_validation.get("demurrage_risk", {})

            if demurrage_risk:
                demurrage_data.append(
                    {
                        "shipment_id": result.get("shipment_id", ""),
                        "risk_level": demurrage_risk.get("risk_level", "LOW"),
                        "days_remaining": demurrage_risk.get("days_remaining", 0),
                        "days_overdue": demurrage_risk.get("days_overdue", 0),
                        "estimated_cost_usd": demurrage_risk.get(
                            "estimated_cost_usd", 0
                        ),
                        "do_validity_date": demurrage_risk.get("do_validity_date", ""),
                        "current_date": demurrage_risk.get("current_date", ""),
                    }
                )

        return pd.DataFrame(demurrage_data)

    def create_executive_summary_data(self) -> Dict[str, Any]:
        """
        Executive Summary 데이터 생성

        Returns:
            Dict: Executive Summary용 구조화된 데이터
        """
        stats = self.extract_pdf_integration_stats()

        summary = {
            "overview": {
                "report_title": "SHPT September 2025 - PDF Integrated Audit Report",
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_items": stats.get("total_items", 0),
                "total_amount_usd": stats.get("total_amount_usd", 0),
                "pass_rate": stats.get("pass_rate", "0%"),
                "pdf_integration_enabled": True,
            },
            "pdf_integration": stats.get("pdf_stats", {}),
            "gate_validation": stats.get("gate_stats", {}),
            "key_metrics": {
                "documents_processed": stats.get("total_supporting_docs", 0),
                "shipments_analyzed": stats.get("pdf_stats", {}).get(
                    "shipments_with_pdfs", 0
                ),
                "cross_doc_success_rate": self._calculate_cross_doc_success_rate(stats),
                "avg_gate_score": stats.get("gate_stats", {}).get("avg_gate_score", 0),
            },
        }

        return summary

    def _calculate_cross_doc_success_rate(self, stats: Dict) -> str:
        """Cross-Document 성공률 계산"""
        pdf_stats = stats.get("pdf_stats", {})
        total_pass = pdf_stats.get("cross_doc_pass", 0)
        total_fail = pdf_stats.get("cross_doc_fail", 0)
        total = total_pass + total_fail

        if total == 0:
            return "N/A"

        success_rate = (total_pass / total) * 100
        return f"{success_rate:.1f}%"

    def process_all_data(self) -> Dict[str, Any]:
        """
        모든 데이터 처리 및 구조화

        Returns:
            Dict: 처리된 모든 데이터
        """
        if not self.raw_data:
            return {}

        logger.info("Processing all JSON data for Excel conversion...")

        processed = {
            "statistics": self.extract_pdf_integration_stats(),
            "supporting_docs": self.process_supporting_docs_data(),
            "gate_analysis": self.extract_gate_analysis_data(),
            "cross_doc_issues": self.extract_cross_document_issues(),
            "demurrage_risks": self.extract_demurrage_risk_data(),
            "executive_summary": self.create_executive_summary_data(),
        }

        self.processed_data = processed

        logger.info("Data processing completed successfully")
        return processed

    def save_processed_data(self, output_path: str) -> bool:
        """
        처리된 데이터 저장

        Args:
            output_path: 출력 파일 경로

        Returns:
            bool: 저장 성공 여부
        """
        if not self.processed_data:
            logger.error("No processed data to save")
            return False

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                # DataFrame은 dict로 변환하여 저장
                save_data = {}
                for key, value in self.processed_data.items():
                    if isinstance(value, pd.DataFrame):
                        save_data[key] = value.to_dict("records")
                    else:
                        save_data[key] = value

                json.dump(save_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Processed data saved to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save processed data: {str(e)}")
            return False


def main():
    """메인 실행 함수 - 테스트 및 예제"""

    # JSON 파일 경로
    json_path = "HVDC_Invoice_Audit-20251012T195441Z-1-001/HVDC_Invoice_Audit/01_DSV_SHPT/Results/Sept_2025/shpt_sept_2025_enhanced_result_20251012_123701.json"

    # 데이터 처리기 초기화
    processor = ExcelDataProcessor()

    # JSON 데이터 로드 및 처리
    if processor.load_json_data(json_path):
        processed_data = processor.process_all_data()

        # 처리 결과 출력
        print("✅ JSON Data Processing Complete!")
        print(f"   📊 Statistics: {len(processed_data.get('statistics', {}))}")
        print(
            f"   📄 Supporting Docs: {len(processed_data.get('supporting_docs', []))}"
        )
        print(f"   🎯 Gate Analysis: {len(processed_data.get('gate_analysis', []))}")
        print(
            f"   ⚠️ Cross-Doc Issues: {len(processed_data.get('cross_doc_issues', []))}"
        )
        print(
            f"   🚨 Demurrage Risks: {len(processed_data.get('demurrage_risks', []))}"
        )

        # 처리된 데이터 저장 (선택사항)
        output_path = "Results/Sept_2025/processed_excel_data.json"
        processor.save_processed_data(output_path)
    else:
        print("❌ Failed to load JSON data")


if __name__ == "__main__":
    main()
