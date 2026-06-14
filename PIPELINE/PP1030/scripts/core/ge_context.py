#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Great Expectations 컨텍스트 초기화 (GE Context Initialization)
===============================================================

파이프라인에서 사용할 Great Expectations 컨텍스트를 초기화합니다.
각 Stage별 데이터 품질 검증을 위한 설정을 제공합니다.

사용법:
    from scripts.core.ge_context import get_ge_context
    
    context = get_ge_context()
    validator = context.get_validator(...)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

try:
    import great_expectations as ge
    from great_expectations.core import ExpectationSuite
    from great_expectations.data_context import DataContext
    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False
    ge = None  # type: ignore[assignment, misc]
    ExpectationSuite = None  # type: ignore[assignment, misc]
    DataContext = None  # type: ignore[assignment, misc]


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GE_ROOT = PROJECT_ROOT / "great_expectations"
GE_ROOT.mkdir(exist_ok=True)


class GEContextManager:
    """Great Expectations 컨텍스트 관리자"""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        GE 컨텍스트 초기화

        Args:
            root_dir: GE 루트 디렉토리 (기본값: 프로젝트 루트/great_expectations)
        """
        if not GE_AVAILABLE:
            raise ImportError(
                "Great Expectations is not installed. Install it with: pip install great-expectations"
            )

        self.root_dir = root_dir or GE_ROOT
        self._context: Optional[DataContext] = None

    def get_context(self, force_reload: bool = False) -> DataContext:
        """
        GE 컨텍스트 가져오기

        Args:
            force_reload: 강제 재로드 여부

        Returns:
            DataContext 객체
        """
        if self._context is None or force_reload:
            try:
                # 기존 컨텍스트가 있으면 사용
                if (self.root_dir / "great_expectations.yml").exists():
                    self._context = ge.get_context(context_root_dir=str(self.root_dir))
                else:
                    # 새 컨텍스트 초기화
                    self._context = ge.get_context(mode="file", project_root_dir=str(self.root_dir))
            except Exception as e:
                warnings.warn(
                    f"Failed to initialize GE context: {e}. Using minimal context.",
                    UserWarning,
                )
                # 최소 컨텍스트로 폴백
                self._context = ge.get_context(mode="ephemeral")

        return self._context

    def get_validator_for_dataframe(
        self,
        df: "pd.DataFrame",
        expectation_suite_name: str = "default",
        data_asset_name: str = "pandas_dataframe",
    ):
        """
        DataFrame용 Validator 생성

        Args:
            df: 검증할 DataFrame
            expectation_suite_name: Expectation Suite 이름
            data_asset_name: 데이터 자산 이름

        Returns:
            Validator 객체
        """
        if not GE_AVAILABLE:
            raise ImportError("Great Expectations is not available")

        context = self.get_context()

        # Expectation Suite 가져오기 또는 생성
        try:
            suite = context.get_expectation_suite(expectation_suite_name)
        except Exception:
            # Suite가 없으면 생성
            suite = context.create_expectation_suite(expectation_suite_name)

        # Validator 생성
        validator = context.get_validator(
            batch_request={
                "datasource_name": "pandas",
                "data_asset_name": data_asset_name,
            },
            expectation_suite_name=expectation_suite_name,
        )

        # DataFrame 설정
        validator.active_batch.data = df

        return validator


# 전역 컨텍스트 관리자
_global_ge_manager: Optional[GEContextManager] = None


def get_ge_context(root_dir: Optional[Path] = None) -> DataContext:
    """
    전역 GE 컨텍스트 가져오기

    Args:
        root_dir: GE 루트 디렉토리

    Returns:
        DataContext 객체
    """
    global _global_ge_manager

    if _global_ge_manager is None:
        _global_ge_manager = GEContextManager(root_dir)

    return _global_ge_manager.get_context()


def get_validator_for_dataframe(
    df: "pd.DataFrame",
    expectation_suite_name: str = "default",
    data_asset_name: str = "pandas_dataframe",
    root_dir: Optional[Path] = None,
):
    """
    DataFrame용 Validator 생성 (편의 함수)

    Args:
        df: 검증할 DataFrame
        expectation_suite_name: Expectation Suite 이름
        data_asset_name: 데이터 자산 이름
        root_dir: GE 루트 디렉토리

    Returns:
        Validator 객체
    """
    global _global_ge_manager

    if _global_ge_manager is None:
        _global_ge_manager = GEContextManager(root_dir)

    return _global_ge_manager.get_validator_for_dataframe(
        df, expectation_suite_name, data_asset_name
    )


def is_ge_available() -> bool:
    """Great Expectations 사용 가능 여부 확인"""
    return GE_AVAILABLE

