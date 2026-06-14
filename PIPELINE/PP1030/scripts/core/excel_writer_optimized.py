#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화된 Excel 쓰기 유틸리티 (Optimized Excel Writer)
====================================================

XlsxWriter를 사용한 고성능 Excel 파일 쓰기 유틸리티입니다.
대용량 데이터 처리를 위한 메모리 효율적 쓰기를 지원합니다.

사용법:
    from scripts.core.excel_writer_optimized import OptimizedExcelWriter
    
    with OptimizedExcelWriter("output.xlsx") as writer:
        writer.write_dataframe(df, sheet_name="Sheet1")
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore[assignment, misc]

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    xlsxwriter = None  # type: ignore[assignment, misc]


class OptimizedExcelWriter:
    """
    최적화된 Excel 쓰기 클래스
    
    XlsxWriter를 사용하여 대용량 데이터를 효율적으로 쓰는 클래스입니다.
    메모리 효율적 쓰기 옵션과 배치 처리를 지원합니다.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        use_xlsxwriter: bool = True,
        constant_memory: bool = True,
        default_format_properties: Optional[Dict[str, Any]] = None,
    ):
        """
        최적화된 Excel Writer 초기화

        Args:
            file_path: 출력 파일 경로
            use_xlsxwriter: XlsxWriter 사용 여부 (False면 openpyxl 사용)
            constant_memory: 메모리 효율적 쓰기 모드 (XlsxWriter만)
            default_format_properties: 기본 포맷 속성
        """
        self.file_path = Path(file_path)
        self.use_xlsxwriter = use_xlsxwriter and XLSXWRITER_AVAILABLE
        self.constant_memory = constant_memory
        self.default_format_properties = default_format_properties or {}

        if self.use_xlsxwriter and not XLSXWRITER_AVAILABLE:
            warnings.warn(
                "XlsxWriter not available, falling back to openpyxl",
                UserWarning,
            )
            self.use_xlsxwriter = False

        self._writer = None
        self._workbook = None
        self._worksheets: Dict[str, Any] = {}

    def __enter__(self):
        """Context manager 진입"""
        if self.use_xlsxwriter:
            # XlsxWriter 옵션 설정
            options = {
                "constant_memory": self.constant_memory,
                "default_format_properties": self.default_format_properties,
            }
            self._workbook = xlsxwriter.Workbook(str(self.file_path), options)
        else:
            # Pandas ExcelWriter (openpyxl)
            if not PANDAS_AVAILABLE:
                raise ImportError("Pandas is required for openpyxl mode")
            self._writer = pd.ExcelWriter(
                str(self.file_path),
                engine="openpyxl",
                if_sheet_exists="replace",
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        if self.use_xlsxwriter:
            if self._workbook:
                self._workbook.close()
        else:
            if self._writer:
                self._writer.close()

    def write_dataframe(
        self,
        df: "pd.DataFrame",
        sheet_name: str = "Sheet1",
        index: bool = False,
        header: bool = True,
        startrow: int = 0,
        startcol: int = 0,
    ) -> None:
        """
        DataFrame을 Excel 시트에 쓰기

        Args:
            df: 쓸 DataFrame
            sheet_name: 시트 이름
            index: 인덱스 포함 여부
            header: 헤더 포함 여부
            startrow: 시작 행 (0-based)
            startcol: 시작 열 (0-based)
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas is required")

        if self.use_xlsxwriter:
            self._write_with_xlsxwriter(df, sheet_name, index, header, startrow, startcol)
        else:
            self._write_with_pandas(df, sheet_name, index, header)

    def _write_with_xlsxwriter(
        self,
        df: "pd.DataFrame",
        sheet_name: str,
        index: bool,
        header: bool,
        startrow: int,
        startcol: int,
    ) -> None:
        """XlsxWriter를 사용한 쓰기"""
        # 시트 이름 정리 (Excel 제한: 31자, 특수문자 제거)
        clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]

        # 시트 가져오기 또는 생성
        if clean_sheet_name in self._worksheets:
            worksheet = self._worksheets[clean_sheet_name]
        else:
            worksheet = self._workbook.add_worksheet(clean_sheet_name)
            self._worksheets[clean_sheet_name] = worksheet

        # 헤더 쓰기
        if header:
            col_idx = startcol
            for col_name in df.columns:
                worksheet.write(startrow, col_idx, str(col_name))
                col_idx += 1
            current_row = startrow + 1
        else:
            current_row = startrow

        # 데이터 쓰기 (배치 처리)
        # XlsxWriter는 행 단위로 쓰는 것이 효율적
        for row_idx, (_, row) in enumerate(df.iterrows()):
            col_idx = startcol
            if index:
                worksheet.write(current_row + row_idx, col_idx, row.name)
                col_idx += 1

            for value in row:
                # None, NaN 처리
                if pd.isna(value):
                    worksheet.write(current_row + row_idx, col_idx, "")
                else:
                    worksheet.write(current_row + row_idx, col_idx, value)
                col_idx += 1

    def _write_with_pandas(
        self,
        df: "pd.DataFrame",
        sheet_name: str,
        index: bool,
        header: bool,
    ) -> None:
        """Pandas ExcelWriter를 사용한 쓰기 (기존 방식)"""
        if not self._writer:
            raise RuntimeError("Writer not initialized")

        df.to_excel(
            self._writer,
            sheet_name=sheet_name,
            index=index,
            header=header,
        )

    def add_format(self, format_properties: Dict[str, Any]) -> Any:
        """
        셀 포맷 추가 (XlsxWriter만)

        Args:
            format_properties: 포맷 속성 딕셔너리

        Returns:
            Format 객체
        """
        if not self.use_xlsxwriter:
            raise RuntimeError("add_format is only available with XlsxWriter")

        if not self._workbook:
            raise RuntimeError("Workbook not initialized")

        return self._workbook.add_format(format_properties)

    def set_column(self, sheet_name: str, column: Union[str, int], width: float) -> None:
        """
        컬럼 너비 설정 (XlsxWriter만)

        Args:
            sheet_name: 시트 이름
            column: 컬럼 (A, B, C 또는 0, 1, 2)
            width: 너비
        """
        if not self.use_xlsxwriter:
            return  # openpyxl에서는 무시

        clean_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")[:31]
        if clean_sheet_name not in self._worksheets:
            return

        worksheet = self._worksheets[clean_sheet_name]
        if isinstance(column, str):
            worksheet.set_column(column, column, width)
        else:
            # 숫자를 Excel 컬럼 문자로 변환
            col_letter = xlsxwriter.utility.xl_col_to_name(column)
            worksheet.set_column(col_letter, col_letter, width)


def write_excel_optimized(
    df: "pd.DataFrame",
    file_path: Union[str, Path],
    sheet_name: str = "Sheet1",
    use_xlsxwriter: bool = True,
    **kwargs,
) -> None:
    """
    DataFrame을 최적화된 방식으로 Excel 파일에 쓰기 (편의 함수)

    Args:
        df: 쓸 DataFrame
        file_path: 출력 파일 경로
        sheet_name: 시트 이름
        use_xlsxwriter: XlsxWriter 사용 여부
        **kwargs: 추가 옵션 (index, header 등)
    """
    with OptimizedExcelWriter(file_path, use_xlsxwriter=use_xlsxwriter) as writer:
        writer.write_dataframe(df, sheet_name=sheet_name, **kwargs)


def is_xlsxwriter_available() -> bool:
    """XlsxWriter 사용 가능 여부 확인"""
    return XLSXWRITER_AVAILABLE

