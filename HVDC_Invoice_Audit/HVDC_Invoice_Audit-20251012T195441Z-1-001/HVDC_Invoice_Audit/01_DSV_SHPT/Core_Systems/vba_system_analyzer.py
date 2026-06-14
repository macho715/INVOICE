#!/usr/bin/env python3
"""
VBA System Analyzer for HVDC Invoice Audit System
기존 VBA 모듈들의 기능을 분석하고 Python과의 연동 인터페이스를 설계
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class VBAFunction:
    """VBA 함수 정보"""

    name: str
    module: str
    description: str
    parameters: List[str]
    returns: str
    dependencies: List[str]
    excel_operations: List[str]


@dataclass
class VBAModule:
    """VBA 모듈 정보"""

    name: str
    file_path: str
    description: str
    functions: List[VBAFunction]
    constants: Dict[str, str]
    workflow_step: int


@dataclass
class VBAWorkflow:
    """VBA 워크플로우 정보"""

    steps: List[Dict[str, Any]]
    data_flow: Dict[str, List[str]]
    excel_sheets: List[str]
    output_structure: Dict[str, Any]


class VBASystemAnalyzer:
    """VBA 시스템 분석기"""

    def __init__(self, vba_directory: str = "VBA"):
        self.vba_dir = Path(vba_directory)
        self.modules: List[VBAModule] = []
        self.workflow: Optional[VBAWorkflow] = None

    def analyze_vba_system(self) -> Dict[str, Any]:
        """전체 VBA 시스템 분석"""
        logger.info("🔍 VBA 시스템 분석 시작...")

        # VBA 파일들 분석
        self._analyze_vba_files()

        # 워크플로우 분석
        self._analyze_workflow()

        # 데이터 구조 분석
        data_structures = self._analyze_data_structures()

        # Excel 시트 구조 분석
        sheet_structures = self._analyze_excel_structures()

        analysis_result = {
            "modules": [asdict(module) for module in self.modules],
            "workflow": asdict(self.workflow) if self.workflow else None,
            "data_structures": data_structures,
            "excel_structures": sheet_structures,
            "integration_points": self._identify_integration_points(),
        }

        logger.info("✅ VBA 시스템 분석 완료")
        return analysis_result

    def _analyze_vba_files(self):
        """VBA 파일들 분석"""
        if not self.vba_dir.exists():
            logger.warning(f"⚠️ VBA 디렉토리를 찾을 수 없음: {self.vba_dir}")
            return

        vba_files = list(self.vba_dir.glob("*.bas"))
        logger.info(f"📁 발견된 VBA 파일 수: {len(vba_files)}")

        for vba_file in vba_files:
            logger.info(f"📄 분석 중: {vba_file.name}")
            module = self._parse_vba_file(vba_file)
            if module:
                self.modules.append(module)

    def _parse_vba_file(self, file_path: Path) -> Optional[VBAModule]:
        """개별 VBA 파일 파싱"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 모듈명 추출
            module_name_match = re.search(r'Attribute VB_Name = "([^"]+)"', content)
            module_name = (
                module_name_match.group(1) if module_name_match else file_path.stem
            )

            # 함수들 추출
            functions = self._extract_functions(content, module_name)

            # 상수들 추출
            constants = self._extract_constants(content)

            # 워크플로우 단계 결정
            workflow_step = self._determine_workflow_step(module_name, content)

            # 모듈 설명 생성
            description = self._generate_module_description(module_name, functions)

            return VBAModule(
                name=module_name,
                file_path=str(file_path),
                description=description,
                functions=functions,
                constants=constants,
                workflow_step=workflow_step,
            )

        except Exception as e:
            logger.error(f"❌ VBA 파일 파싱 오류 ({file_path}): {e}")
            return None

    def _extract_functions(self, content: str, module_name: str) -> List[VBAFunction]:
        """VBA 함수들 추출"""
        functions = []

        # Public Sub/Function 패턴 찾기
        function_pattern = (
            r"(?:Public\s+)?(?:Private\s+)?(Sub|Function)\s+(\w+)\s*\([^)]*\)"
        )
        matches = re.finditer(function_pattern, content, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            func_type = match.group(1)
            func_name = match.group(2)

            # 함수 본문 추출하여 상세 분석
            func_details = self._analyze_function_details(
                content, func_name, match.start()
            )

            functions.append(
                VBAFunction(
                    name=func_name,
                    module=module_name,
                    description=func_details.get("description", ""),
                    parameters=func_details.get("parameters", []),
                    returns=func_type,
                    dependencies=func_details.get("dependencies", []),
                    excel_operations=func_details.get("excel_operations", []),
                )
            )

        return functions

    def _analyze_function_details(
        self, content: str, func_name: str, start_pos: int
    ) -> Dict[str, Any]:
        """함수 상세 분석"""
        # 함수 본문 추출 (간단한 구현)
        lines = content[start_pos:].split("\n")
        func_body = []

        for line in lines:
            func_body.append(line)
            if line.strip().startswith("End Sub") or line.strip().startswith(
                "End Function"
            ):
                break

        func_content = "\n".join(func_body)

        # Excel 작업 식별
        excel_operations = []
        if "Worksheets" in func_content or "Sheets" in func_content:
            excel_operations.append("worksheet_manipulation")
        if "Range" in func_content or "Cells" in func_content:
            excel_operations.append("cell_operations")
        if "Formula" in func_content:
            excel_operations.append("formula_operations")
        if "PivotTable" in func_content:
            excel_operations.append("pivot_operations")

        # 의존성 식별
        dependencies = []
        for module in ["modHelpers", "modPipeline", "modCompileMaster"]:
            if module in func_content:
                dependencies.append(module)

        return {
            "description": self._generate_function_description(func_name, func_content),
            "parameters": self._extract_parameters(func_content),
            "dependencies": dependencies,
            "excel_operations": excel_operations,
        }

    def _extract_constants(self, content: str) -> Dict[str, str]:
        """상수들 추출"""
        constants = {}
        const_pattern = r'Private\s+Const\s+(\w+)\s+As\s+String\s*=\s*"([^"]+)"'
        matches = re.finditer(const_pattern, content)

        for match in matches:
            constants[match.group(1)] = match.group(2)

        return constants

    def _determine_workflow_step(self, module_name: str, content: str) -> int:
        """워크플로우 단계 결정"""
        if "ExtractFormulas" in content:
            return 1
        elif "ApplyFormula" in content or "REV RATE" in content:
            return 2
        elif "CompileAllSheets" in content or "MasterData" in content:
            return 3
        elif module_name == "modPipeline":
            return 0  # 메인 파이프라인
        else:
            return -1  # 유틸리티

    def _generate_module_description(
        self, module_name: str, functions: List[VBAFunction]
    ) -> str:
        """모듈 설명 생성"""
        descriptions = {
            "modPipeline": "메인 실행 파이프라인 - 3단계 자동화 워크플로우 관리",
            "modHelpers": "핵심 유틸리티 함수들 - 로깅, 데이터 검색, 시트 관리",
            "modCompileMaster": "데이터 통합 시스템 - 모든 시트를 MasterData로 통합",
            "modApplyFormula": "REV RATE 계산 및 DIFFERENCE 분석 - 공식 자동 적용",
            "modExtractFormulas": "Excel 공식 추출 - 공식을 텍스트로 변환하여 저장",
            "Module1": "사용자 인터페이스 - Excel 버튼 및 매크로 실행",
        }

        return descriptions.get(
            module_name, f"{len(functions)}개 함수를 포함한 VBA 모듈"
        )

    def _generate_function_description(self, func_name: str, func_content: str) -> str:
        """함수 설명 생성"""
        # 함수명 기반 설명 생성
        descriptions = {
            "START_PIPELINE": "전체 VBA 자동화 파이프라인 시작",
            "RunPipeline_Final": "3단계 파이프라인 실행 (공식추출→REV RATE→마스터데이터)",
            "CompileAllSheets": "모든 워크시트 데이터를 MasterData 시트로 통합",
            "ApplyFormula_ByDynamicRemark_ExactTotal_Safe": "REV RATE 계산 및 DIFFERENCE 분석",
            "ExtractFormulasWithExclusion": "Excel 공식을 Formula 컬럼에 텍스트로 추출",
            "LogAction": "작업 로그를 LOG 시트에 기록",
            "SafeFind": "안전한 셀 검색 기능",
        }

        return descriptions.get(func_name, f"{func_name} 함수")

    def _extract_parameters(self, func_content: str) -> List[str]:
        """함수 매개변수 추출"""
        # 간단한 매개변수 추출 (실제로는 더 정교한 파싱 필요)
        param_pattern = r"\(\s*([^)]+)\s*\)"
        match = re.search(param_pattern, func_content.split("\n")[0])

        if match:
            params_str = match.group(1)
            if params_str.strip():
                return [p.strip() for p in params_str.split(",")]

        return []

    def _analyze_workflow(self):
        """VBA 워크플로우 분석"""
        steps = [
            {
                "step": 1,
                "name": "Formula Extraction",
                "description": "Excel 공식을 텍스트로 추출하여 Formula 컬럼에 저장",
                "module": "modExtractFormulas",
                "function": "ExtractFormulasWithExclusion",
                "input": "Excel 워크시트의 RATE 컬럼",
                "output": "Formula 컬럼에 공식 텍스트",
            },
            {
                "step": 2,
                "name": "REV RATE Application",
                "description": "REV RATE 계산 및 DIFFERENCE 분석",
                "module": "modApplyFormula",
                "function": "ApplyFormula_ByDynamicRemark_ExactTotal_Safe",
                "input": "RATE, Q'TY, TOTAL (USD) 컬럼",
                "output": "REV RATE, REV TOTAL, DIFFERENCE 컬럼",
            },
            {
                "step": 3,
                "name": "Master Data Compilation",
                "description": "모든 시트 데이터를 MasterData로 통합",
                "module": "modCompileMaster",
                "function": "CompileAllSheets",
                "input": "모든 워크시트의 데이터 행",
                "output": "MasterData 시트",
            },
        ]

        data_flow = {
            "step1_to_step2": ["Formula 컬럼", "RATE 컬럼"],
            "step2_to_step3": ["REV RATE", "REV TOTAL", "DIFFERENCE"],
            "step3_output": ["통합된 MasterData"],
        }

        excel_sheets = ["LOG", "MasterData", "각 워크시트"]

        output_structure = {
            "Formula_Column": {
                "description": "Excel 공식을 텍스트로 저장",
                "format": "텍스트 (따옴표로 시작)",
            },
            "REV_RATE_Columns": {
                "REV RATE": "ROUND(RATE, 2)",
                "REV TOTAL": "REV RATE × Q'TY",
                "DIFFERENCE": "REV TOTAL - TOTAL (USD)",
            },
            "MasterData_Sheet": {
                "columns": [
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
            },
        }

        self.workflow = VBAWorkflow(
            steps=steps,
            data_flow=data_flow,
            excel_sheets=excel_sheets,
            output_structure=output_structure,
        )

    def _analyze_data_structures(self) -> Dict[str, Any]:
        """VBA에서 사용하는 데이터 구조 분석"""
        return {
            "input_columns": [
                "CWI Job Number",
                "Order Ref. Number",
                "S/No",
                "RATE SOURCE",
                "DESCRIPTION",
                "RATE",
                "Q'TY",
                "TOTAL (USD)",
                "REMARK",
            ],
            "generated_columns": ["Formula", "REV RATE", "REV TOTAL", "DIFFERENCE"],
            "sheet_types": {
                "data_sheets": "실제 인보이스 데이터가 있는 시트들",
                "log_sheet": "작업 로그 기록용 시트",
                "master_sheet": "통합 데이터 시트",
                "excluded_sheets": [
                    "SUMMARY",
                    "DEC",
                    "MasterData",
                    "FEB",
                    "InvoiceData",
                ],
            },
            "data_validation": {
                "s_no_column": "숫자 값이 있는 행만 처리",
                "rate_column": "공식이 있는 셀에서 추출",
                "job_number": "CW1 Job Number 라벨 옆 값",
                "order_ref": "Order Ref. Number 라벨 옆 값",
            },
        }

    def _analyze_excel_structures(self) -> Dict[str, Any]:
        """Excel 시트 구조 분석"""
        return {
            "standard_headers": [
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
            ],
            "header_locations": {
                "dynamic_search": "각 시트에서 헤더 위치를 동적으로 검색",
                "s_no_column": "S/No 컬럼을 기준으로 데이터 행 식별",
                "rate_column": "RATE 컬럼을 기준으로 공식 추출",
            },
            "formatting": {
                "number_format": "#,##0.00 (REV 컬럼들)",
                "bold_headers": "헤더 행 굵게 표시",
                "red_totals": "TOTAL 행의 REV 컬럼들 빨간색 굵게",
            },
            "formulas": {
                "rev_rate": "=ROUND(RC[RATE_COL],2)",
                "rev_total": "=RC[-1]*RC[QTY_COL]",
                "difference": "=RC[-1]-RC[TOTAL_COL]",
                "sum_formulas": "=SUM(R[START]:R[END]C)",
            },
        }

    def _identify_integration_points(self) -> Dict[str, Any]:
        """Python과의 통합 지점 식별"""
        return {
            "data_exchange": {
                "input_format": "Excel 워크북 (.xlsx/.xlsm)",
                "output_format": "Excel 워크북 with VBA results",
                "intermediate_format": "CSV/JSON for Python processing",
            },
            "integration_methods": {
                "method1": {
                    "name": "Excel Template with VBA",
                    "description": "VBA가 포함된 Excel 템플릿 생성",
                    "pros": "완전 자동화, 사용자 친화적",
                    "cons": "VBA 보안 설정 필요",
                },
                "method2": {
                    "name": "Python-driven VBA Execution",
                    "description": "Python에서 Excel 자동화로 VBA 실행",
                    "pros": "Python 제어 가능, 유연성",
                    "cons": "Excel 설치 필요, 복잡성",
                },
                "method3": {
                    "name": "Pure Python Implementation",
                    "description": "VBA 로직을 Python으로 재구현",
                    "pros": "플랫폼 독립적, 빠른 실행",
                    "cons": "개발 시간 필요",
                },
            },
            "recommended_approach": {
                "primary": "Pure Python Implementation",
                "reason": "기존 Python Excel 보고서 생성기와 완벽 통합 가능",
                "implementation": "VBA 로직을 Python 함수로 변환하여 Excel 보고서에 추가 시트로 포함",
            },
        }

    def save_analysis(self, output_path: str = "vba_analysis_result.json"):
        """분석 결과 저장"""
        analysis = self.analyze_vba_system()

        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 VBA 분석 결과 저장: {output_file}")
        return analysis


def main():
    """메인 실행 함수"""
    print("🚀 VBA System Analyzer 시작")

    analyzer = VBASystemAnalyzer()
    analysis_result = analyzer.save_analysis()

    # 요약 출력
    print("\n📋 VBA 시스템 분석 요약:")
    print(f"  - 분석된 모듈 수: {len(analysis_result['modules'])}")
    print(
        f"  - 워크플로우 단계: {len(analysis_result['workflow']['steps']) if analysis_result['workflow'] else 0}"
    )
    print(
        f"  - 통합 방법: {analysis_result['integration_points']['recommended_approach']['primary']}"
    )

    print("\n📊 모듈별 요약:")
    for module in analysis_result["modules"]:
        print(
            f"  - {module['name']}: {len(module['functions'])}개 함수, Step {module['workflow_step']}"
        )

    print("\n✅ VBA 시스템 분석 완료!")


if __name__ == "__main__":
    main()
