#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polars 호환성 어댑터 (Polars Compatibility Adapter)
====================================================

Pandas와 Polars 간 변환을 제공하는 호환성 레이어입니다.
기존 Pandas 코드를 점진적으로 Polars로 전환할 수 있도록 지원합니다.

사용법:
    from scripts.core.polars_adapter import to_polars, to_pandas
    
    # Pandas DataFrame을 Polars로 변환
    pl_df = to_polars(pd_df)
    
    # Polars DataFrame을 Pandas로 변환
    pd_df = to_pandas(pl_df)
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None  # type: ignore[assignment, misc]

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore[assignment, misc]


def to_polars(df: "pd.DataFrame") -> "pl.DataFrame":
    """
    Pandas DataFrame을 Polars DataFrame으로 변환

    Args:
        df: Pandas DataFrame

    Returns:
        Polars DataFrame

    Raises:
        ImportError: Polars가 설치되지 않은 경우
        ValueError: 입력이 Pandas DataFrame이 아닌 경우
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )

    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas is not installed")

    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected pandas.DataFrame, got {type(df)}")

    try:
        # Pandas → Polars 변환
        # Polars는 Pandas의 from_pandas를 사용
        pl_df = pl.from_pandas(df)
        return pl_df
    except Exception as e:
        raise ValueError(f"Failed to convert Pandas DataFrame to Polars: {e}") from e


def to_pandas(df: "pl.DataFrame") -> "pd.DataFrame":
    """
    Polars DataFrame을 Pandas DataFrame으로 변환

    Args:
        df: Polars DataFrame

    Returns:
        Pandas DataFrame

    Raises:
        ImportError: Pandas가 설치되지 않은 경우
        ValueError: 입력이 Polars DataFrame이 아닌 경우
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas is not installed")

    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )

    if not isinstance(df, pl.DataFrame):
        raise ValueError(f"Expected polars.DataFrame, got {type(df)}")

    try:
        # Polars → Pandas 변환
        pd_df = df.to_pandas()
        return pd_df
    except Exception as e:
        raise ValueError(f"Failed to convert Polars DataFrame to Pandas: {e}") from e


def read_excel_polars(
    file_path: Union[str, "Path"],
    sheet_name: Optional[Union[str, int, list]] = None,
    **kwargs,
) -> Union["pl.DataFrame", dict[str, "pl.DataFrame"]]:
    """
    Excel 파일을 Polars로 읽기

    Args:
        file_path: Excel 파일 경로
        sheet_name: 시트 이름 또는 인덱스 (None이면 첫 번째 시트)
        **kwargs: 추가 옵션 (read_excel에 전달)

    Returns:
        Polars DataFrame 또는 시트 이름을 키로 하는 딕셔너리

    Raises:
        ImportError: Polars가 설치되지 않은 경우
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )

    try:
        # Polars의 read_excel 사용
        if sheet_name is None:
            # 첫 번째 시트만 읽기
            df = pl.read_excel(file_path, **kwargs)
            return df
        elif isinstance(sheet_name, (str, int)):
            # 단일 시트 읽기
            df = pl.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            return df
        else:
            # 여러 시트 읽기
            result = {}
            for sheet in sheet_name:
                df = pl.read_excel(file_path, sheet_name=sheet, **kwargs)
                result[str(sheet)] = df
            return result
    except Exception as e:
        # Polars가 Excel 읽기를 지원하지 않는 경우 Pandas로 폴백
        warnings.warn(
            f"Polars Excel reading failed, falling back to Pandas: {e}",
            UserWarning,
        )
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas is not available for fallback") from e

        # Pandas로 읽고 Polars로 변환
        pd_df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        if isinstance(pd_df, dict):
            return {k: to_polars(v) for k, v in pd_df.items()}
        else:
            return to_polars(pd_df)


def write_excel_polars(
    df: "pl.DataFrame",
    file_path: Union[str, "Path"],
    sheet_name: str = "Sheet1",
    **kwargs,
) -> None:
    """
    Polars DataFrame을 Excel 파일로 쓰기

    Args:
        df: Polars DataFrame
        file_path: 출력 파일 경로
        sheet_name: 시트 이름
        **kwargs: 추가 옵션 (write_excel에 전달)

    Raises:
        ImportError: Polars가 설치되지 않은 경우
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )

    if not isinstance(df, pl.DataFrame):
        raise ValueError(f"Expected polars.DataFrame, got {type(df)}")

    try:
        # Polars의 write_excel 사용
        df.write_excel(file_path, worksheet=sheet_name, **kwargs)
    except Exception as e:
        # Polars가 Excel 쓰기를 지원하지 않는 경우 Pandas로 폴백
        warnings.warn(
            f"Polars Excel writing failed, falling back to Pandas: {e}",
            UserWarning,
        )
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas is not available for fallback") from e

        # Polars → Pandas → Excel
        pd_df = to_pandas(df)
        pd_df.to_excel(file_path, sheet_name=sheet_name, **kwargs)


def is_polars_available() -> bool:
    """Polars 사용 가능 여부 확인"""
    return POLARS_AVAILABLE


def is_pandas_available() -> bool:
    """Pandas 사용 가능 여부 확인"""
    return PANDAS_AVAILABLE


# 편의 함수: DataFrame 타입 확인
def get_dataframe_type(df: Union["pd.DataFrame", "pl.DataFrame"]) -> str:
    """
    DataFrame 타입 확인

    Args:
        df: DataFrame (Pandas 또는 Polars)

    Returns:
        "pandas" 또는 "polars"
    """
    if not POLARS_AVAILABLE and not PANDAS_AVAILABLE:
        raise ImportError("Neither Pandas nor Polars is available")

    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        return "polars"
    elif PANDAS_AVAILABLE and isinstance(df, pd.DataFrame):
        return "pandas"
    else:
        raise ValueError(f"Unknown DataFrame type: {type(df)}")

