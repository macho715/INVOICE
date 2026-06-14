#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Great Expectations 검증 유틸리티 (GE Validator Utility)
=======================================================

각 Stage별 데이터 품질 검증을 수행하는 유틸리티입니다.

사용법:
    from scripts.core.ge_validator import validate_stage_output
    
    result = validate_stage_output(df, stage_num=1)
    if not result.success:
        print(f"Validation failed: {result.failures}")
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore[assignment, misc]

try:
    import great_expectations as ge
    from great_expectations.core import ExpectationSuite
    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False
    ge = None  # type: ignore[assignment, misc]
    ExpectationSuite = None  # type: ignore[assignment, misc]

from scripts.core.ge_context import get_validator_for_dataframe, is_ge_available

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPECTATIONS_DIR = PROJECT_ROOT / "expectations"


@dataclass
class ValidationResult:
    """검증 결과"""
    success: bool
    stage: int
    total_expectations: int
    successful_expectations: int
    failed_expectations: int
    failures: List[Dict[str, Any]]
    warnings: List[str]


def load_expectation_suite(stage_num: int) -> Optional[Dict[str, Any]]:
    """
    Stage별 Expectation Suite 로드

    Args:
        stage_num: Stage 번호 (1, 2, 3)

    Returns:
        Expectation Suite 딕셔너리 또는 None
    """
    suite_file = EXPECTATIONS_DIR / f"stage{stage_num}_expectations.json"

    if not suite_file.exists():
        warnings.warn(f"Expectation suite not found: {suite_file}", UserWarning)
        return None

    try:
        with open(suite_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        warnings.warn(f"Failed to load expectation suite: {e}", UserWarning)
        return None


def validate_stage_output(
    df: "pd.DataFrame",
    stage_num: int,
    fail_on_error: bool = False,
) -> ValidationResult:
    """
    Stage 출력 데이터 검증

    Args:
        df: 검증할 DataFrame
        stage_num: Stage 번호 (1, 2, 3)
        fail_on_error: 오류 시 예외 발생 여부

    Returns:
        ValidationResult 객체
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas is required")

    if not is_ge_available():
        warnings.warn(
            "Great Expectations is not available. Skipping validation.",
            UserWarning,
        )
        return ValidationResult(
            success=True,
            stage=stage_num,
            total_expectations=0,
            successful_expectations=0,
            failed_expectations=0,
            failures=[],
            warnings=["Great Expectations not available"],
        )

    # Expectation Suite 로드
    suite_data = load_expectation_suite(stage_num)
    if not suite_data:
        return ValidationResult(
            success=True,
            stage=stage_num,
            total_expectations=0,
            successful_expectations=0,
            failed_expectations=0,
            failures=[],
            warnings=[f"Expectation suite for Stage {stage_num} not found"],
        )

    try:
        # Validator 생성
        suite_name = suite_data.get("expectation_suite_name", f"stage{stage_num}_expectations")
        validator = get_validator_for_dataframe(
            df,
            expectation_suite_name=suite_name,
            data_asset_name=f"stage{stage_num}_output",
        )

        # Expectation Suite에 규칙 추가
        expectations = suite_data.get("expectations", [])
        for exp in expectations:
            exp_type = exp.get("expectation_type")
            kwargs = exp.get("kwargs", {})
            meta = exp.get("meta", {})

            try:
                # 동적 expectation 메서드 호출
                exp_method = getattr(validator, exp_type, None)
                if exp_method:
                    exp_method(**kwargs)
                else:
                    warnings.warn(
                        f"Unknown expectation type: {exp_type}",
                        UserWarning,
                    )
            except Exception as e:
                warnings.warn(
                    f"Failed to add expectation {exp_type}: {e}",
                    UserWarning,
                )

        # 검증 실행
        result = validator.validate()

        # 결과 파싱
        total = len(expectations)
        successful = sum(1 for r in result.results if r.success)
        failed = total - successful

        failures = []
        for r in result.results:
            if not r.success:
                failures.append({
                    "expectation_type": r.expectation_config.expectation_type,
                    "kwargs": r.expectation_config.kwargs,
                    "exception_info": str(r.exception_info) if r.exception_info else None,
                })

        validation_result = ValidationResult(
            success=failed == 0,
            stage=stage_num,
            total_expectations=total,
            successful_expectations=successful,
            failed_expectations=failed,
            failures=failures,
            warnings=[],
        )

        if fail_on_error and not validation_result.success:
            raise ValueError(
                f"Validation failed for Stage {stage_num}: {len(failures)} expectations failed"
            )

        return validation_result

    except Exception as e:
        warnings.warn(f"Validation error: {e}", UserWarning)
        return ValidationResult(
            success=False,
            stage=stage_num,
            total_expectations=0,
            successful_expectations=0,
            failed_expectations=0,
            failures=[{"error": str(e)}],
            warnings=[f"Validation exception: {e}"],
        )


def print_validation_result(result: ValidationResult) -> None:
    """
    검증 결과 출력

    Args:
        result: ValidationResult 객체
    """
    print(f"\n[VALIDATION] Stage {result.stage}")
    print(f"  Success: {result.success}")
    print(f"  Total expectations: {result.total_expectations}")
    print(f"  Successful: {result.successful_expectations}")
    print(f"  Failed: {result.failed_expectations}")

    if result.failures:
        print(f"\n  Failures:")
        for failure in result.failures[:5]:  # 최대 5개만 출력
            exp_type = failure.get("expectation_type", "unknown")
            print(f"    - {exp_type}")

    if result.warnings:
        print(f"\n  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")

