#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlwings 기반 VBA-Python 브리지 모듈
===================================

Excel VBA에서 Python 함수를 직접 호출할 수 있도록 하는 브리지 모듈입니다.
xlwings를 사용하여 Excel과 Python 간 양방향 통신을 지원합니다.

사용법:
    1. Excel에서 xlwings 추가 기능 설치
    2. 이 모듈을 Python 경로에 추가
    3. VBA에서 RunPython 함수로 Python 함수 호출
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import xlwings as xw
    XLWINGS_AVAILABLE = True
except ImportError:
    XLWINGS_AVAILABLE = False
    xw = None  # type: ignore[assignment, misc]

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# 파이프라인 모듈 임포트
try:
    from run.run_pipeline import run_stage, run_all_stages
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    logger.warning("Pipeline modules not available")


@xw.func
def run_pipeline_stage(stage_num: int) -> Dict[str, Any]:
    """
    VBA에서 직접 호출 가능한 파이프라인 Stage 실행 함수
    
    Args:
        stage_num: 실행할 Stage 번호 (1-4)
    
    Returns:
        실행 결과 딕셔너리:
        {
            "status": "SUCCESS" | "ERROR",
            "message": "상세 메시지",
            "stage": stage_num,
            "output_files": ["파일 경로 리스트"]
        }
    
    사용 예시 (VBA):
        Dim result As Variant
        result = RunPython("run_pipeline_stage", 1)
        MsgBox result("message")
    """
    if not XLWINGS_AVAILABLE:
        return {
            "status": "ERROR",
            "message": "xlwings is not installed. Install with: pip install xlwings",
            "stage": stage_num,
            "output_files": []
        }
    
    if not PIPELINE_AVAILABLE:
        return {
            "status": "ERROR",
            "message": "Pipeline modules are not available",
            "stage": stage_num,
            "output_files": []
        }
    
    try:
        logger.info(f"Running Stage {stage_num} from Excel VBA")
        
        # 파이프라인 설정 로드
        from run.run_pipeline import (
            load_pipeline_config,
            load_stage2_config,
            configure_logging
        )
        import argparse
        
        pipeline_config = load_pipeline_config()
        stage2_config = load_stage2_config()
        configure_logging(pipeline_config)
        
        # 더미 args 객체 생성
        args = argparse.Namespace(
            no_sorting=False,
            use_polars=False,
            use_xlsxwriter=False,
            validate_with_ge=False,
            stage3_report_dir=None,
            stage4_visualize=False,
            stage4_no_visualize=False,
            stage4_excel_out=None,
            stage4_json_out=None,
            stage4_sheet_name=None,
            stage4_case_column=None
        )
        
        # 파이프라인 실행
        from run.run_pipeline import run_stage
        success = run_stage(stage_num, pipeline_config, stage2_config, args)
        
        if success:
            return {
                "status": "SUCCESS",
                "message": f"Stage {stage_num} completed successfully",
                "stage": stage_num,
                "output_files": []  # 실제 출력 파일 경로 반환 가능
            }
        else:
            return {
                "status": "ERROR",
                "message": f"Stage {stage_num} failed. Check logs for details.",
                "stage": stage_num,
                "output_files": []
            }
            
    except Exception as e:
        logger.error(f"Error running Stage {stage_num}: {e}", exc_info=True)
        return {
            "status": "ERROR",
            "message": f"Exception: {str(e)}",
            "stage": stage_num,
            "output_files": []
        }


@xw.func
def get_pipeline_status() -> Dict[str, Any]:
    """
    실시간 파이프라인 상태 조회
    
    Returns:
        파이프라인 상태 딕셔너리:
        {
            "stage1": "completed" | "running" | "pending" | "error",
            "stage2": "...",
            "stage3": "...",
            "stage4": "...",
            "last_update": "YYYY-MM-DD HH:MM:SS"
        }
    
    사용 예시 (VBA):
        Dim status As Variant
        status = RunPython("get_pipeline_status")
        Debug.Print status("stage1")
    """
    if not XLWINGS_AVAILABLE:
        return {
            "stage1": "error",
            "stage2": "error",
            "stage3": "error",
            "stage4": "error",
            "last_update": "",
            "message": "xlwings not available"
        }
    
    try:
        from datetime import datetime
        
        # 로그 파일 또는 상태 파일에서 상태 읽기
        # 실제 구현은 프로젝트의 상태 관리 방식에 맞게 조정 필요
        log_dir = PROJECT_ROOT / "logs"
        
        # 간단한 구현: 최근 로그 파일 확인
        status = {
            "stage1": "pending",
            "stage2": "pending",
            "stage3": "pending",
            "stage4": "pending",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if log_dir.exists():
            log_files = sorted(log_dir.glob("pipeline_*.log"), reverse=True)
            if log_files:
                # 최근 로그 파일에서 상태 파싱 (간단한 구현)
                # 실제로는 더 정교한 상태 추적 필요
                status["last_update"] = datetime.fromtimestamp(
                    log_files[0].stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}", exc_info=True)
        return {
            "stage1": "error",
            "stage2": "error",
            "stage3": "error",
            "stage4": "error",
            "last_update": "",
            "message": str(e)
        }


@xw.func
def get_pipeline_progress() -> Dict[str, Any]:
    """
    파이프라인 진행률 조회
    
    Returns:
        진행률 딕셔너리:
        {
            "stage1": 100,  # 0-100
            "stage2": 50,
            "stage3": 0,
            "stage4": 0,
            "overall": 37.5
        }
    """
    if not XLWINGS_AVAILABLE:
        return {
            "stage1": 0,
            "stage2": 0,
            "stage3": 0,
            "stage4": 0,
            "overall": 0,
            "message": "xlwings not available"
        }
    
    try:
        # 실제 구현은 로그 파일 파싱 또는 상태 파일 읽기
        # 여기서는 예시 구현
        progress = {
            "stage1": 0,
            "stage2": 0,
            "stage3": 0,
            "stage4": 0,
            "overall": 0
        }
        
        # 로그 파일에서 진행률 추출 로직 (구현 필요)
        # 예: 로그 파일의 마지막 라인에서 진행률 파싱
        
        overall = (progress["stage1"] + progress["stage2"] + 
                  progress["stage3"] + progress["stage4"]) / 4
        progress["overall"] = overall
        
        return progress
        
    except Exception as e:
        logger.error(f"Error getting pipeline progress: {e}", exc_info=True)
        return {
            "stage1": 0,
            "stage2": 0,
            "stage3": 0,
            "stage4": 0,
            "overall": 0,
            "message": str(e)
        }


@xw.func
def validate_pipeline_config() -> Dict[str, Any]:
    """
    파이프라인 설정 검증
    
    Returns:
        검증 결과 딕셔너리:
        {
            "valid": True | False,
            "errors": ["오류 메시지 리스트"],
            "warnings": ["경고 메시지 리스트"]
        }
    """
    if not XLWINGS_AVAILABLE:
        return {
            "valid": False,
            "errors": ["xlwings not available"],
            "warnings": []
        }
    
    try:
        errors = []
        warnings = []
        
        # 필수 파일 확인
        required_files = [
            PROJECT_ROOT / "config" / "pipeline_config.yaml",
            PROJECT_ROOT / "config" / "stage2_derived_config.yaml",
            PROJECT_ROOT / "run" / "run_pipeline.py"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                errors.append(f"Required file not found: {file_path}")
        
        # 입력 파일 확인
        input_files = [
            PROJECT_ROOT / "data" / "raw" / "Case List_Hitachi.xlsx",
            PROJECT_ROOT / "data" / "raw" / "HVDC WAREHOUSE_HITACHI(HE).xlsx"
        ]
        
        for file_path in input_files:
            if not file_path.exists():
                warnings.append(f"Input file not found: {file_path}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        logger.error(f"Error validating pipeline config: {e}", exc_info=True)
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }


# xlwings UDF 등록 (선택적)
if XLWINGS_AVAILABLE:
    try:
        # Excel에서 Python 함수를 직접 호출할 수 있도록 등록
        # 주의: 이 기능은 xlwings 추가 기능이 설치되어 있어야 함
        pass
    except Exception as e:
        logger.warning(f"Failed to register xlwings UDFs: {e}")

