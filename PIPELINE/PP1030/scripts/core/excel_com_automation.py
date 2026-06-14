#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pywin32 기반 Excel COM 자동화 모듈
===================================

Windows COM을 사용한 Excel 자동화 모듈입니다.
VBA 없이 Python에서 Excel의 모든 기능을 직접 제어할 수 있습니다.

사용법:
    from scripts.core.excel_com_automation import ExcelCOMAutomation
    
    excel = ExcelCOMAutomation()
    excel.apply_color_formatting("file.xlsx", "Sheet1", case_numbers, color)
    excel.close()
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import win32com.client as win32
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    win32 = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


class ExcelCOMAutomation:
    """
    Excel COM 자동화 클래스
    
    Windows COM을 통해 Excel을 직접 제어합니다.
    색상 포맷팅, 차트 생성, 수식 입력 등 모든 Excel 기능을 사용할 수 있습니다.
    """
    
    def __init__(self, visible: bool = False, display_alerts: bool = False):
        """
        Excel COM 객체 초기화
        
        Args:
            visible: Excel 창 표시 여부 (기본값: False)
            display_alerts: 경고 메시지 표시 여부 (기본값: False)
        
        Raises:
            ImportError: pywin32가 설치되지 않은 경우
        """
        if not PYWIN32_AVAILABLE:
            raise ImportError(
                "pywin32 is not installed. Install it with: pip install pywin32"
            )
        
        try:
            self.excel = win32.Dispatch("Excel.Application")
            self.excel.Visible = visible
            self.excel.DisplayAlerts = display_alerts
            self.excel.ScreenUpdating = False  # 성능 향상
            self._workbooks: Dict[str, Any] = {}
            
            logger.info("Excel COM automation initialized")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Excel COM: {e}") from e
    
    def open_workbook(self, file_path: Union[str, Path]) -> str:
        """
        Excel 파일 열기
        
        Args:
            file_path: Excel 파일 경로
        
        Returns:
            워크북 키 (나중에 참조용)
        
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        try:
            wb = self.excel.Workbooks.Open(str(file_path))
            key = str(file_path)
            self._workbooks[key] = wb
            
            logger.info(f"Opened workbook: {file_path}")
            return key
            
        except Exception as e:
            raise RuntimeError(f"Failed to open workbook {file_path}: {e}") from e
    
    def apply_color_formatting(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        case_numbers: List[str],
        color: int,
        case_column: str = "Case No.",
    ) -> None:
        """
        Case 번호 기반 색상 포맷팅 적용 (정밀 제어)
        
        Args:
            file_path: Excel 파일 경로
            sheet_name: 시트 이름
            case_numbers: 색상을 적용할 Case 번호 리스트
            color: RGB 색상 값 (예: 0xFFA500 = Orange, 0xFFFF00 = Yellow)
            case_column: Case 번호 컬럼명 (기본값: "Case No.")
        
        성능:
            - COM을 통한 직접 제어로 정확한 색상 적용
            - 대량 셀 처리 시 배치 업데이트로 최적화
        """
        if not PYWIN32_AVAILABLE:
            raise ImportError("pywin32 is not available")
        
        file_path = Path(file_path).resolve()
        key = self.open_workbook(file_path)
        wb = self._workbooks[key]
        
        try:
            ws = wb.Worksheets(sheet_name)
            
            # Case 번호 컬럼 찾기
            header_row = 1
            case_col_index = None
            
            for col in range(1, ws.UsedRange.Columns.Count + 1):
                cell_value = ws.Cells(header_row, col).Value
                if cell_value and str(cell_value).strip() == case_column:
                    case_col_index = col
                    break
            
            if case_col_index is None:
                raise ValueError(f"Case column '{case_column}' not found in sheet '{sheet_name}'")
            
            # Case 번호를 키로 하는 딕셔너리 생성 (빠른 검색)
            case_set = set(str(c).strip() for c in case_numbers)
            
            # 배치 업데이트 시작
            self.excel.ScreenUpdating = False
            self.excel.Calculation = -4105  # xlCalculationManual
            
            applied_count = 0
            used_range = ws.UsedRange
            
            # 행별로 처리
            for row in range(header_row + 1, used_range.Rows.Count + 1):
                case_value = ws.Cells(row, case_col_index).Value
                if case_value and str(case_value).strip() in case_set:
                    # 전체 행에 색상 적용
                    ws.Rows(row).Interior.Color = color
                    applied_count += 1
            
            # 배치 업데이트 완료
            self.excel.Calculation = -4106  # xlCalculationAutomatic
            self.excel.ScreenUpdating = True
            
            # 저장
            wb.Save()
            
            logger.info(
                f"Applied color {hex(color)} to {applied_count} rows "
                f"in sheet '{sheet_name}'"
            )
            
        except Exception as e:
            logger.error(f"Error applying color formatting: {e}", exc_info=True)
            raise
        finally:
            wb.Close(SaveChanges=True)
            if key in self._workbooks:
                del self._workbooks[key]
    
    def apply_cell_color(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        cell_mappings: Dict[Tuple[int, int], int],
    ) -> None:
        """
        특정 셀에 색상 적용 (정밀 제어)
        
        Args:
            file_path: Excel 파일 경로
            sheet_name: 시트 이름
            cell_mappings: {(row, col): color} 딕셔너리
                예: {(2, 3): 0xFFA500, (5, 7): 0xFFFF00}
        """
        if not PYWIN32_AVAILABLE:
            raise ImportError("pywin32 is not available")
        
        file_path = Path(file_path).resolve()
        key = self.open_workbook(file_path)
        wb = self._workbooks[key]
        
        try:
            ws = wb.Worksheets(sheet_name)
            
            self.excel.ScreenUpdating = False
            
            for (row, col), color in cell_mappings.items():
                ws.Cells(row, col).Interior.Color = color
            
            self.excel.ScreenUpdating = True
            wb.Save()
            
            logger.info(f"Applied colors to {len(cell_mappings)} cells")
            
        except Exception as e:
            logger.error(f"Error applying cell colors: {e}", exc_info=True)
            raise
        finally:
            wb.Close(SaveChanges=True)
            if key in self._workbooks:
                del self._workbooks[key]
    
    def create_chart(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        chart_type: int,
        source_range: str,
        chart_position: Tuple[int, int] = (1, 1),
    ) -> None:
        """
        차트 생성
        
        Args:
            file_path: Excel 파일 경로
            sheet_name: 시트 이름
            chart_type: 차트 타입 (Excel 상수, 예: 51 = xlColumnClustered)
            source_range: 데이터 범위 (예: "A1:D10")
            chart_position: 차트 위치 (row, col)
        """
        if not PYWIN32_AVAILABLE:
            raise ImportError("pywin32 is not available")
        
        file_path = Path(file_path).resolve()
        key = self.open_workbook(file_path)
        wb = self._workbooks[key]
        
        try:
            ws = wb.Worksheets(sheet_name)
            
            # 차트 생성
            chart = ws.ChartObjects().Add(
                Left=chart_position[1] * 50,  # 열 위치
                Top=chart_position[0] * 200,   # 행 위치
                Width=400,
                Height=250
            )
            
            chart.Chart.ChartType = chart_type
            chart.Chart.SetSourceData(Source=ws.Range(source_range))
            
            wb.Save()
            logger.info(f"Created chart in sheet '{sheet_name}'")
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}", exc_info=True)
            raise
        finally:
            wb.Close(SaveChanges=True)
            if key in self._workbooks:
                del self._workbooks[key]
    
    def close_workbook(self, key: str, save: bool = True) -> None:
        """
        워크북 닫기
        
        Args:
            key: 워크북 키 (open_workbook에서 반환된 값)
            save: 저장 여부 (기본값: True)
        """
        if key in self._workbooks:
            try:
                if save:
                    self._workbooks[key].Save()
                self._workbooks[key].Close()
                del self._workbooks[key]
                logger.info(f"Closed workbook: {key}")
            except Exception as e:
                logger.warning(f"Error closing workbook {key}: {e}")
    
    def close_all(self) -> None:
        """모든 워크북 닫기"""
        for key in list(self._workbooks.keys()):
            self.close_workbook(key, save=True)
    
    def quit(self) -> None:
        """Excel 애플리케이션 종료"""
        try:
            self.close_all()
            self.excel.Quit()
            self.excel = None
            logger.info("Excel COM automation closed")
        except Exception as e:
            logger.warning(f"Error quitting Excel: {e}")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.quit()


# 편의 함수
def apply_color_to_cases(
    file_path: Union[str, Path],
    sheet_name: str,
    case_numbers: List[str],
    color: int,
    case_column: str = "Case No.",
) -> None:
    """
    Case 번호에 색상 적용 (편의 함수)
    
    Args:
        file_path: Excel 파일 경로
        sheet_name: 시트 이름
        case_numbers: Case 번호 리스트
        color: RGB 색상 값
        case_column: Case 번호 컬럼명
    """
    with ExcelCOMAutomation(visible=False) as excel:
        excel.apply_color_formatting(
            file_path, sheet_name, case_numbers, color, case_column
        )


# 색상 상수
class ExcelColors:
    """Excel 색상 상수"""
    ORANGE = 0xFFA500      # 주황색 (날짜 변경)
    YELLOW = 0xFFFF00      # 노란색 (신규 레코드)
    RED = 0xFF0000         # 빨간색 (CRITICAL 이상치)
    LIGHT_RED = 0xFF6B6B   # 연한 빨강 (HIGH 이상치)
    LIGHT_YELLOW = 0xFFFFE0  # 연한 노랑 (MEDIUM 이상치)
    LIGHT_GREEN = 0x90EE90   # 연한 초록 (LOW 이상치)

