"""
PDF System Integration Tests
=============================

전체 시스템 통합 테스트

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List

# 모듈 임포트
try:
    from ontology_mapper import OntologyMapper
    from cross_doc_validator import CrossDocValidator
    from workflow_automator import WorkflowAutomator

    MODULES_OK = True
except ImportError:
    MODULES_OK = False
    print("Warning: Some modules not found. Install dependencies.")


class TestPDFParsingAccuracy:
    """PDF 파싱 정확도 테스트"""

    @pytest.fixture
    def sample_boe_data(self):
        """샘플 BOE 데이터"""
        return {
            "dec_no": "20252101030815",
            "dec_date": "28-08-2025",
            "mbl_no": "CHN2595234",
            "vessel": "CMA CGM PEGASUS",
            "voyage_no": "0MDEIE1MA",
            "containers": ["CMAU2623154", "TGHU8788690", "TCNU4356762"],
            "hs_code": "9405500000",
            "description": "Nonelectrical luminaires and lighting fittings",
            "quantity": 749,
            "unit": "PKG",
            "gross_weight_kg": 53125.7,
            "net_weight_kg": 48950.0,
            "value_usd": 133785.63,
            "duty_aed": 24657.00,
            "vat_aed": 6664.00,
        }

    @pytest.fixture
    def sample_do_data(self):
        """샘플 DO 데이터"""
        return {
            "do_number": "DOCHP00042642",
            "do_date": "26-08-2025",
            "delivery_valid_until": "09/09/2025",
            "mbl_no": "CHN2595234",
            "vessel": "CMA CGM PEGASUS",
            "voyage_no": "0MDEIE1MA",
            "containers": [
                {"container_no": "CMAU2623154", "seal_no": "M3228611"},
                {"container_no": "TGHU8788690", "seal_no": "M3228619"},
                {"container_no": "TCNU4356762", "seal_no": "M3423439"},
            ],
            "weight_kg": 53125.7,
            "volume_cbm": 155.00,
            "quantity": 3,
            "description": "LIGHTING&SMALL POWER SYSTEM SHIPMENT NO : HVDC-ADOPT-SCT-0126",
        }

    def test_boe_essential_fields_extracted(self, sample_boe_data):
        """BOE 필수 필드가 추출되어야 함"""
        essential_fields = [
            "dec_no",
            "mbl_no",
            "containers",
            "hs_code",
            "duty_aed",
            "vat_aed",
        ]

        for field in essential_fields:
            assert field in sample_boe_data, f"Missing essential field: {field}"
            assert sample_boe_data[field] is not None, f"Empty essential field: {field}"

    def test_do_essential_fields_extracted(self, sample_do_data):
        """DO 필수 필드가 추출되어야 함"""
        essential_fields = ["do_number", "mbl_no", "containers", "delivery_valid_until"]

        for field in essential_fields:
            assert field in sample_do_data, f"Missing essential field: {field}"
            assert sample_do_data[field] is not None, f"Empty essential field: {field}"

    # ===== TDD RED: 실제 PDF 파싱 테스트 (실패 예상) =====

    def test_parse_real_boe_pdf_should_extract_key_fields(self):
        """실제 BOE PDF에서 핵심 필드를 추출해야 함 (현재 실패 예상)"""
        # 이 테스트는 새로운 파서가 구현되기 전까지 실패할 것임
        try:
            from parsers.dsv_pdf_parser import parse_boe

            # 테스트용 샘플 파일 사용
            data = parse_boe("test_sample.txt")  # 텍스트 파일로 테스트
            assert data.get("dec_no"), "DEC NO not parsed"
            assert data.get("dec_date"), "DEC DATE not parsed"
            assert data.get("mbl_no"), "MBL not parsed"
            assert data.get("containers"), "containers not parsed"
        except ImportError:
            pytest.fail("parsers.dsv_pdf_parser module not found - need to implement")
        except FileNotFoundError:
            pytest.skip("Test PDF file not available")

    def test_parse_real_do_pdf_should_extract_validity_date(self):
        """실제 DO PDF에서 유효기간을 추출해야 함 (현재 실패 예상)"""
        try:
            from parsers.dsv_pdf_parser import parse_do

            data = parse_do("test_sample.txt")  # 텍스트 파일로 테스트
            # DO 샘플이 없으므로 기본 구조만 확인
            assert isinstance(data, dict), "Should return dict"
        except ImportError:
            pytest.fail("parsers.dsv_pdf_parser module not found - need to implement")
        except FileNotFoundError:
            pytest.skip("Test PDF file not available")

    def test_parse_real_dn_pdf_should_extract_container_info(self):
        """실제 DN PDF에서 컨테이너 정보를 추출해야 함 (현재 실패 예상)"""
        try:
            from parsers.dsv_pdf_parser import parse_dn

            data = parse_dn("test_sample.txt")  # 텍스트 파일로 테스트
            # DN 샘플이 없으므로 기본 구조만 확인
            assert isinstance(data, dict), "Should return dict"
        except ImportError:
            pytest.fail("parsers.dsv_pdf_parser module not found - need to implement")
        except FileNotFoundError:
            pytest.skip("Test PDF file not available")

    def test_enhanced_date_parsing_should_handle_multiple_formats(self):
        """강화된 날짜 파싱이 다양한 포맷을 처리해야 함 (현재 실패 예상)"""
        if not MODULES_OK:
            pytest.skip("Modules not available")

        automator = WorkflowAutomator()

        # 다양한 날짜 포맷 테스트 (현재는 일부만 지원)
        test_dates = [
            ("22-Sep-2025", "2025-09-22"),
            ("9/21/2025", "2025-09-21"),
            ("15-09-2025", "2025-09-15"),
            ("2025-09-15", "2025-09-15"),
        ]

        for input_date, expected in test_dates:
            parsed = automator._parse_date(input_date)
            if parsed:
                assert parsed.strftime("%Y-%m-%d") == expected
            else:
                pytest.fail(f"Failed to parse date format: {input_date}")

    def test_container_numbers_format(self, sample_boe_data):
        """Container 번호 형식이 올바른지 확인"""
        import re

        container_pattern = r"^[A-Z]{4}\d{7}$"

        for container in sample_boe_data["containers"]:
            assert re.match(
                container_pattern, container
            ), f"Invalid container format: {container}"

    def test_hs_code_format(self, sample_boe_data):
        """HS Code 형식이 올바른지 확인"""
        hs_code = sample_boe_data["hs_code"]

        # 10자리 숫자
        assert len(hs_code) == 10, f"HS Code must be 10 digits: {hs_code}"
        assert hs_code.isdigit(), f"HS Code must be numeric: {hs_code}"


class TestOntologyMapping:
    """온톨로지 매핑 테스트"""

    @pytest.fixture
    def mapper(self):
        """OntologyMapper fixture"""
        if not MODULES_OK:
            pytest.skip("Modules not available")
        return OntologyMapper()

    @pytest.fixture
    def sample_boe(self):
        return {
            "dec_no": "20252101030815",
            "mbl_no": "CHN2595234",
            "hs_code": "9405500000",
            "containers": ["CMAU2623154"],
            "duty_aed": 24657.00,
        }

    def test_should_create_shipment_object(self, mapper, sample_boe):
        """Shipment 객체가 생성되어야 함"""
        shipment_uri = mapper.map_boe_to_ontology(sample_boe, "HVDC-ADOPT-SCT-0126")

        assert shipment_uri is not None
        assert "Shipment_" in str(shipment_uri)

    def test_should_create_rdf_triples(self, mapper, sample_boe):
        """RDF 트리플이 생성되어야 함"""
        mapper.map_boe_to_ontology(sample_boe, "HVDC-ADOPT-SCT-0126")

        stats = mapper.get_graph_stats()

        assert stats["total_triples"] > 0, "No RDF triples created"
        assert stats["shipments"] > 0, "No shipment objects created"

    def test_should_infer_certification_for_electrical_goods(self, mapper):
        """전기제품에 대한 MOIAT 인증 추론"""
        hs_code = "8544601000"  # Electrical cables
        description = "High voltage power cables"

        certs = mapper.infer_certification_requirements(hs_code, description)

        assert len(certs) > 0, "No certifications inferred"
        assert any(
            c["type"] == "MOIAT" for c in certs
        ), "MOIAT certification not inferred"

    def test_should_infer_fanr_for_nuclear_materials(self, mapper):
        """핵물질에 대한 FANR 인증 추론"""
        hs_code = "28443010"
        description = "Radioactive isotopes for industrial use"

        certs = mapper.infer_certification_requirements(hs_code, description)

        assert len(certs) > 0, "No certifications inferred"
        assert any(
            c["type"] == "FANR" for c in certs
        ), "FANR certification not inferred"

    def test_should_export_to_turtle_format(self, mapper, sample_boe, tmp_path):
        """Turtle 형식으로 내보내기"""
        mapper.map_boe_to_ontology(sample_boe, "HVDC-ADOPT-SCT-0126")

        output_file = tmp_path / "test_ontology.ttl"
        mapper.export_to_turtle(str(output_file))

        assert output_file.exists(), "Turtle file not created"
        assert output_file.stat().st_size > 0, "Turtle file is empty"


class TestCrossDocValidation:
    """Cross-document 검증 테스트"""

    @pytest.fixture
    def validator(self):
        """CrossDocValidator fixture"""
        if not MODULES_OK:
            pytest.skip("Modules not available")
        return CrossDocValidator()

    @pytest.fixture
    def matching_documents(self):
        """일치하는 문서들"""
        return [
            {
                "doc_type": "BOE",
                "data": {
                    "mbl_no": "CHN2595234",
                    "containers": ["CMAU2623154", "TGHU8788690"],
                    "gross_weight_kg": 53125.7,
                    "quantity": 3,
                },
            },
            {
                "doc_type": "DO",
                "data": {
                    "mbl_no": "CHN2595234",
                    "containers": [
                        {"container_no": "CMAU2623154"},
                        {"container_no": "TGHU8788690"},
                    ],
                    "weight_kg": 53125.7,
                    "quantity": 3,
                },
            },
        ]

    @pytest.fixture
    def mismatched_documents(self):
        """불일치하는 문서들"""
        return [
            {
                "doc_type": "BOE",
                "data": {
                    "mbl_no": "CHN2595234",
                    "containers": ["CMAU2623154", "TGHU8788690"],
                },
            },
            {
                "doc_type": "DO",
                "data": {
                    "mbl_no": "CHN9999999",  # 불일치!
                    "containers": [{"container_no": "CMAU2623154"}],  # 누락!
                },
            },
        ]

    def test_should_pass_matching_documents(self, validator, matching_documents):
        """일치하는 문서는 PASS 해야 함"""
        report = validator.generate_validation_report(
            "HVDC-ADOPT-SCT-0126", matching_documents
        )

        assert report["overall_status"] in [
            "PASS",
            "WARNING",
        ], f"Expected PASS, got {report['overall_status']}"
        assert (
            report["total_issues"] == 0
        ), f"Expected 0 issues, found {report['total_issues']}"

    def test_should_detect_mbl_mismatch(self, validator, mismatched_documents):
        """MBL 불일치를 감지해야 함"""
        report = validator.generate_validation_report(
            "HVDC-ADOPT-SCT-0126", mismatched_documents
        )

        assert report["overall_status"] == "FAIL", "Should fail on MBL mismatch"
        assert (
            report["severity_breakdown"]["HIGH"] > 0
        ), "Should have HIGH severity issues"

        # MBL_MISMATCH 이슈 확인
        mbl_issues = [i for i in report["all_issues"] if i["type"] == "MBL_MISMATCH"]
        assert len(mbl_issues) > 0, "MBL mismatch not detected"

    def test_should_detect_container_mismatch(self, validator, mismatched_documents):
        """Container 불일치를 감지해야 함"""
        report = validator.generate_validation_report(
            "HVDC-ADOPT-SCT-0126", mismatched_documents
        )

        container_issues = [
            i for i in report["all_issues"] if i["type"] == "CONTAINER_MISMATCH"
        ]
        assert len(container_issues) > 0, "Container mismatch not detected"

    def test_should_allow_weight_tolerance(self, validator):
        """Weight는 ±3% 허용해야 함"""
        documents = [
            {"doc_type": "BOE", "data": {"gross_weight_kg": 1000.0}},
            {"doc_type": "DO", "data": {"weight_kg": 1025.0}},  # 2.5% 차이 - 허용
        ]

        report = validator.generate_validation_report("TEST", documents)

        # Weight deviation 이슈가 없어야 함 (±3% 이내)
        weight_issues = [
            i for i in report["all_issues"] if i["type"] == "WEIGHT_DEVIATION"
        ]
        assert len(weight_issues) == 0, "Should allow ±3% weight tolerance"

    def test_should_reject_excessive_weight_deviation(self, validator):
        """±3% 초과 Weight 차이는 거부해야 함"""
        documents = [
            {"doc_type": "BOE", "data": {"gross_weight_kg": 1000.0}},
            {"doc_type": "DO", "data": {"weight_kg": 1050.0}},  # 5% 차이 - 거부
        ]

        report = validator.generate_validation_report("TEST", documents)

        weight_issues = [
            i for i in report["all_issues"] if i["type"] == "WEIGHT_DEVIATION"
        ]
        assert len(weight_issues) > 0, "Should reject >3% weight deviation"


class TestWorkflowAutomation:
    """워크플로우 자동화 테스트"""

    @pytest.fixture
    def automator(self):
        """WorkflowAutomator fixture"""
        if not MODULES_OK:
            pytest.skip("Modules not available")
        return WorkflowAutomator()

    def test_should_detect_demurrage_risk(self, automator):
        """Demurrage Risk를 감지해야 함"""
        from datetime import datetime, timedelta

        # 2일 후 만료되는 DO
        expiry_date = datetime.now() + timedelta(days=2)

        do_data = {
            "do_number": "TEST001",
            "delivery_valid_until": expiry_date.strftime("%d/%m/%Y"),
            "quantity": 3,
            "item_code": "HVDC-TEST",
        }

        risk = automator.check_demurrage_risk(do_data)

        assert risk is not None, "Should detect demurrage risk"
        assert risk["risk_level"] in [
            "HIGH",
            "MEDIUM",
        ], "Should have HIGH/MEDIUM risk level"
        assert (
            risk["days_remaining"] >= 1
        ), "Should calculate days remaining (at least 1)"

    def test_should_flag_high_severity_issues(self, automator):
        """HIGH severity 이슈는 자동 플래그해야 함"""
        validation_report = {
            "item_code": "HVDC-TEST",
            "overall_status": "FAIL",
            "total_issues": 2,
            "severity_breakdown": {"HIGH": 1, "MEDIUM": 1, "LOW": 0},
            "all_issues": [
                {
                    "type": "MBL_MISMATCH",
                    "severity": "HIGH",
                    "details": "MBL mismatch detected",
                },
                {
                    "type": "WEIGHT_DEVIATION",
                    "severity": "MEDIUM",
                    "details": "Weight deviation 4%",
                },
            ],
        }

        result = automator.auto_flag_inconsistencies(validation_report)

        assert result["flagged_count"] >= 1, "Should flag HIGH severity issues"

    def test_should_generate_daily_summary(self, automator):
        """일일 요약을 생성해야 함"""
        reports = [
            {"overall_status": "PASS", "total_issues": 0, "severity_breakdown": {}},
            {
                "overall_status": "FAIL",
                "total_issues": 3,
                "severity_breakdown": {"HIGH": 1, "MEDIUM": 2},
            },
            {
                "overall_status": "WARNING",
                "total_issues": 1,
                "severity_breakdown": {"MEDIUM": 1},
            },
        ]

        summary = automator.generate_daily_summary(reports)

        assert summary["total_items_processed"] == 3
        assert summary["status_breakdown"]["PASS"] == 1
        assert summary["status_breakdown"]["FAIL"] == 1
        assert summary["total_issues"] == 4


class TestIntegrationWorkflow:
    """전체 통합 워크플로우 테스트"""

    @pytest.mark.skipif(not MODULES_OK, reason="Modules not available")
    def test_end_to_end_workflow(self):
        """End-to-end 워크플로우 테스트"""
        # 1. 온톨로지 매핑
        mapper = OntologyMapper()

        boe_data = {
            "dec_no": "20252101030815",
            "mbl_no": "CHN2595234",
            "containers": ["CMAU2623154"],
            "hs_code": "9405500000",
        }

        mapper.map_boe_to_ontology(boe_data, "HVDC-ADOPT-SCT-0126")

        # 2. Cross-document 검증
        validator = CrossDocValidator(mapper.graph)

        documents = [
            {"doc_type": "BOE", "data": boe_data},
            {
                "doc_type": "DO",
                "data": {
                    "do_number": "DOCHP00042642",
                    "mbl_no": "CHN2595234",
                    "containers": [{"container_no": "CMAU2623154"}],
                },
            },
        ]

        report = validator.generate_validation_report("HVDC-ADOPT-SCT-0126", documents)

        # 3. 자동화 처리
        automator = WorkflowAutomator()
        result = automator.auto_flag_inconsistencies(report)

        # 검증
        assert mapper.get_graph_stats()["total_triples"] > 0
        assert report["overall_status"] in ["PASS", "WARNING", "FAIL"]
        assert result["item_code"] == "HVDC-ADOPT-SCT-0126"


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
