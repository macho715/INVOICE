#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polars 기반 Excel I/O 최적화 모듈
==================================

Polars를 사용한 고성능 Excel 파일 읽기/쓰기 모듈입니다.
대용량 파일 처리 시 pandas 대비 5-30배 빠른 성능을 제공합니다.

사용법:
    from scripts.core.excel_io_polars import read_excel_polars, write_excel_polars
    
    # Excel 읽기
    df = read_excel_polars("input.xlsx", sheet_name="Sheet1")
    
    # Excel 쓰기
    write_excel_polars(df, "output.xlsx", sheet_name="Sheet1")
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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

logger = logging.getLogger(__name__)


def read_excel_polars(
    file_path: Union[str, Path],
    sheet_name: Optional[Union[str, int, List[Union[str, int]]]] = None,
    header_row: int = 0,
    **kwargs: Any,
) -> Union[pl.DataFrame, Dict[str, pl.DataFrame]]:
    """
    Polars로 Excel 파일 읽기 (고성능)
    
    Args:
        file_path: Excel 파일 경로
        sheet_name: 시트 이름 또는 인덱스 (None이면 첫 번째 시트)
        header_row: 헤더 행 인덱스 (기본값: 0)
        **kwargs: 추가 옵션 (read_excel에 전달)
    
    Returns:
        Polars DataFrame 또는 시트 이름을 키로 하는 딕셔너리
    
    Raises:
        ImportError: Polars가 설치되지 않은 경우
        FileNotFoundError: 파일이 존재하지 않는 경우
    
    성능:
        - pandas 대비 5-30배 빠른 읽기 속도
        - 메모리 효율적 처리
        - 대용량 파일(100MB+) 처리 최적화
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        # Polars의 read_excel 사용
        if sheet_name is None:
            # 첫 번째 시트만 읽기
            df = pl.read_excel(
                file_path,
                sheet_id=0,
                engine="calamine",  # Rust 기반 빠른 엔진
                **kwargs
            )
            return df
            
        elif isinstance(sheet_name, (str, int)):
            # 단일 시트 읽기
            if isinstance(sheet_name, str):
                # 시트 이름으로 읽기
                df = pl.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    engine="calamine",
                    **kwargs
                )
            else:
                # 시트 인덱스로 읽기
                df = pl.read_excel(
                    file_path,
                    sheet_id=sheet_name,
                    engine="calamine",
                    **kwargs
                )
            return df
            
        else:
            # 여러 시트 읽기
            result = {}
            for sheet in sheet_name:
                if isinstance(sheet, str):
                    df = pl.read_excel(
                        file_path,
                        sheet_name=sheet,
                        engine="calamine",
                        **kwargs
                    )
                    result[sheet] = df
                else:
                    df = pl.read_excel(
                        file_path,
                        sheet_id=sheet,
                        engine="calamine",
                        **kwargs
                    )
                    result[str(sheet)] = df
            return result
            
    except Exception as e:
        # Polars가 Excel 읽기를 지원하지 않는 경우 Pandas로 폴백
        logger.warning(
            f"Polars Excel reading failed, falling back to Pandas: {e}",
            exc_info=True
        )
        
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas is not available for fallback") from e
        
        # Pandas로 읽고 Polars로 변환
        try:
            pd_df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, **kwargs)
            
            if isinstance(pd_df, dict):
                # 여러 시트
                from scripts.core.polars_adapter import to_polars
                return {k: to_polars(v) for k, v in pd_df.items()}
            else:
                # 단일 시트
                from scripts.core.polars_adapter import to_polars
                return to_polars(pd_df)
                
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both Polars and Pandas Excel reading failed. "
                f"Polars error: {e}, Pandas error: {fallback_error}"
            ) from fallback_error


def write_excel_polars(
    df: pl.DataFrame,
    file_path: Union[str, Path],
    sheet_name: str = "Sheet1",
    autofit: bool = True,
    table_style: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Polars DataFrame을 Excel 파일로 쓰기 (고성능)
    
    Args:
        df: 쓸 Polars DataFrame
        file_path: 출력 Excel 파일 경로
        sheet_name: 시트 이름 (기본값: "Sheet1")
        autofit: 컬럼 너비 자동 조정 (기본값: True)
        table_style: 테이블 스타일 (기본값: None)
        **kwargs: 추가 옵션 (write_excel에 전달)
    
    Raises:
        ImportError: Polars가 설치되지 않은 경우
    
    성능:
        - pandas 대비 3-10배 빠른 쓰기 속도
        - 메모리 효율적 처리
        - 대용량 데이터 쓰기 최적화
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Polars의 write_excel 사용
        write_options = {
            "worksheet": sheet_name,
            **kwargs
        }
        
        if autofit:
            write_options["autofit"] = True
        
        if table_style:
            write_options["table_style"] = table_style
        
        df.write_excel(file_path, **write_options)
        
        logger.info(f"Successfully wrote Excel file: {file_path}")
        
    except Exception as e:
        # Polars 쓰기 실패 시 Pandas로 폴백
        logger.warning(
            f"Polars Excel writing failed, falling back to Pandas: {e}",
            exc_info=True
        )
        
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas is not available for fallback") from e
        
        # Pandas로 변환 후 쓰기
        from scripts.core.polars_adapter import to_pandas
        
        try:
            pd_df = to_pandas(df)
            pd_df.to_excel(
                file_path,
                sheet_name=sheet_name,
                index=False,
                engine="openpyxl",
                **kwargs
            )
            logger.info(f"Successfully wrote Excel file (via Pandas): {file_path}")
            
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both Polars and Pandas Excel writing failed. "
                f"Polars error: {e}, Pandas error: {fallback_error}"
            ) from fallback_error


def read_excel_polars_multi_sheet(
    file_path: Union[str, Path],
    sheet_names: Optional[List[Union[str, int]]] = None,
    **kwargs: Any,
) -> Dict[str, pl.DataFrame]:
    """
    여러 시트를 한 번에 읽기 (최적화)
    
    Args:
        file_path: Excel 파일 경로
        sheet_names: 읽을 시트 이름/인덱스 리스트 (None이면 모든 시트)
        **kwargs: 추가 옵션
    
    Returns:
        시트 이름을 키로 하는 Polars DataFrame 딕셔너리
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )
    
    file_path = Path(file_path)
    
    try:
        if sheet_names is None:
            # 모든 시트 읽기
            # Polars는 모든 시트를 한 번에 읽을 수 없으므로
            # Pandas로 시트 목록을 먼저 가져온 후 각각 읽기
            if PANDAS_AVAILABLE:
                xl_file = pd.ExcelFile(file_path)
                sheet_names = xl_file.sheet_names
            else:
                raise ImportError("Pandas is required to read all sheets")
        
        result = {}
        for sheet in sheet_names:
            df = read_excel_polars(file_path, sheet_name=sheet, **kwargs)
            if isinstance(sheet, str):
                result[sheet] = df
            else:
                # 시트 인덱스를 이름으로 변환
                if PANDAS_AVAILABLE:
                    xl_file = pd.ExcelFile(file_path)
                    sheet_name = xl_file.sheet_names[sheet]
                    result[sheet_name] = df
                else:
                    result[str(sheet)] = df
        
        return result
        
    except Exception as e:
        logger.error(f"Error reading multiple sheets: {e}", exc_info=True)
        raise


def write_excel_polars_multi_sheet(
    data: Dict[str, pl.DataFrame],
    file_path: Union[str, Path],
    **kwargs: Any,
) -> None:
    """
    여러 시트를 한 번에 쓰기 (최적화)
    
    Args:
        data: 시트 이름을 키로 하는 Polars DataFrame 딕셔너리
        file_path: 출력 Excel 파일 경로
        **kwargs: 추가 옵션
    """
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install it with: pip install polars[excel]"
        )
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Polars는 여러 시트를 한 번에 쓸 수 없으므로
        # 첫 번째 시트는 write_excel로, 나머지는 append 모드로 처리
        # 또는 Pandas ExcelWriter 사용
        
        if PANDAS_AVAILABLE:
            # Pandas ExcelWriter 사용 (더 안정적)
            from scripts.core.polars_adapter import to_pandas
            
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                for sheet_name, df in data.items():
                    pd_df = to_pandas(df)
                    pd_df.to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False,
                        **kwargs
                    )
            
            logger.info(f"Successfully wrote multi-sheet Excel file: {file_path}")
        else:
            # Polars만 사용 (첫 번째 시트만)
            first_sheet = next(iter(data))
            write_excel_polars(data[first_sheet], file_path, sheet_name=first_sheet, **kwargs)
            logger.warning(
                f"Only first sheet '{first_sheet}' written. "
                f"Install pandas for multi-sheet support."
            )
            
    except Exception as e:
        logger.error(f"Error writing multiple sheets: {e}", exc_info=True)
        raise

