#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HVDC 파이프라인 통합 실행 스크립트 v4.0.44
HVDC Pipeline Integrated Execution Script v4.0.44

전체 파이프라인을 하나의 명령으로 실행할 수 있는 통합 스크립트입니다.
최신 개선: 헤더 순서 정렬, Stage 2/3/4 실행 완료, Excel 컬럼 보존
"""

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml


logger = logging.getLogger("hvdc_pipeline.run_pipeline")

# 프로젝트 루트 경로 추가
PIPELINE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_ROOT.parent  # 상위 폴더(프로젝트 루트)를 참조
PIPELINE_CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline_config.yaml"
STAGE2_CONFIG_PATH = PROJECT_ROOT / "config" / "stage2_derived_config.yaml"
DEFAULT_STAGE3_SHEET = 0  # First sheet (HITACHI_입고로직_종합리포트_Fixed)
sys.path.append(str(PROJECT_ROOT))

# �� Stage ����Ʈ
try:  # pragma: no cover - optional dependency guard
    from scripts.stage1_sync_sorted.data_synchronizer_v30 import DataSynchronizerV30
    # data_synchronizer_v29는 archive_stage1_backups에 있음, v30만 사용
    DataSynchronizerV29 = None
    from scripts.stage1_sync_no_sorting.data_synchronizer_v29_no_sorting import (
        DataSynchronizerV29NoSorting,
    )
except ImportError:  # pragma: no cover - runtime import guard
    DataSynchronizerV30 = None  # type: ignore[assignment]
    DataSynchronizerV29 = None  # type: ignore[assignment]
    DataSynchronizerV29NoSorting = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    from scripts.stage2_derived.derived_columns_processor import (
        process_derived_columns,
        resolve_synced_input_path as resolve_stage2_synced_input_path,
    )
except ImportError:  # pragma: no cover - runtime import guard
    process_derived_columns = None  # type: ignore[assignment]
    resolve_stage2_synced_input_path = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    from scripts.stage3_report.report_generator import HVDCExcelReporterFinal
except ImportError:  # pragma: no cover - runtime import guard
    HVDCExcelReporterFinal = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    from scripts.stage4_anomaly.anomaly_detector_balanced import (
        DetectorConfig,
        HybridAnomalyDetector,
    )
except ImportError:  # pragma: no cover - runtime import guard
    DetectorConfig = None  # type: ignore[assignment]
    HybridAnomalyDetector = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    from scripts.stage4_anomaly.anomaly_visualizer import AnomalyVisualizer
except ImportError:  # pragma: no cover - runtime import guard
    AnomalyVisualizer = None  # type: ignore[assignment]

# FileRegistry for auto-detection
try:
    from scripts.core.file_registry import FileRegistry
    FILE_REGISTRY_AVAILABLE = True
except ImportError:
    FILE_REGISTRY_AVAILABLE = False
    FileRegistry = None  # type: ignore[assignment, misc]


# 각 Stage 임포트
def resolve_repo_path(path_value: str | Path, vendor: str | None = None) -> Path:
    """
    저장소 기준 절대 경로를 반환합니다. / Resolve repository-relative paths.
    
    "auto" 또는 "autodetect" 키워드를 인식하여 FileRegistry로 자동탐지합니다.
    """
    # Auto-detection: "auto" or "autodetect" 키워드 처리
    path_str = str(path_value).strip().lower()
    if path_str in ("auto", "autodetect"):
        if not FILE_REGISTRY_AVAILABLE or FileRegistry is None:
            raise ValueError(
                "자동탐지 기능을 사용하려면 FileRegistry가 필요합니다. "
                "scripts.core.file_registry를 확인하세요."
            )
        
        # vendor가 지정되지 않으면 HE를 기본값으로 사용
        target_vendor = (vendor or "HE").upper()
        if target_vendor not in ("SIM", "HE"):
            raise ValueError(f"지원되지 않는 vendor: {target_vendor}. 'SIM' 또는 'HE'만 가능합니다.")
        
        # FileRegistry 인스턴스 생성 및 자동탐지
        registry = FileRegistry(PROJECT_ROOT)
        detected_path = registry.get_raw_vendor(target_vendor)
        
        if detected_path is None:
            raise FileNotFoundError(
                f"자동탐지 실패: {target_vendor} vendor 파일을 data/raw에서 찾을 수 없습니다. "
                f"파일명에 '{target_vendor}' 토큰이 포함되어 있는지 확인하세요."
            )
        
        print(f"[AUTO-DETECT] {target_vendor} vendor file: {detected_path}")
        return detected_path.resolve()
    
    # 일반 경로 처리
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (PROJECT_ROOT / path_obj).resolve()


def load_pipeline_config() -> Dict:
    """파이프라인 설정을 로드합니다. / Load pipeline configuration."""

    config_path = PROJECT_ROOT / "config" / "pipeline_config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file) or {}
    except FileNotFoundError:
        logger.warning("설정 파일을 찾을 수 없습니다: %s", config_path)
        return {}


def load_stage2_config() -> Dict:
    """Stage2 설정을 로드합니다. / Load Stage 2 specific configuration."""

    config_path = PROJECT_ROOT / "config" / "stage2_derived_config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file) or {}
    except FileNotFoundError:
        logger.warning("Stage2 설정 파일을 찾을 수 없습니다: %s", config_path)
        return {}


def configure_logging(pipeline_config: Dict) -> None:
    """로깅 설정을 초기화합니다. / Configure logging for the pipeline."""

    logging_cfg = pipeline_config.get("logging", {})
    level_name = str(logging_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    basic_kwargs = {
        "level": level,
        "format": logging_cfg.get("format"),
    }
    filtered_kwargs = {k: v for k, v in basic_kwargs.items() if v is not None}

    if not logging.getLogger().handlers:
        logging.basicConfig(**filtered_kwargs)
    else:
        logging.getLogger().setLevel(level)
        if logging_cfg.get("format"):
            formatter = logging.Formatter(logging_cfg["format"])
            for handler in logging.getLogger().handlers:
                handler.setFormatter(formatter)

    log_file = logging_cfg.get("file")
    if log_file:
        file_path = resolve_repo_path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        if logging_cfg.get("format"):
            file_handler.setFormatter(logging.Formatter(logging_cfg["format"]))
        logging.getLogger().addHandler(file_handler)


def print_banner():
    """파이프라인 시작 배너를 출력합니다."""
    print("\n" + "=" * 80)
    print("HVDC PIPELINE v4.0.44")
    print("   Samsung C&T Logistics | ADNOC-DSV Partnership")
    print("=" * 80)
    print("Execution Stages:")
    print("   Stage 1: Data Synchronization + 색상 자동화")
    print("   Stage 2: Derived Columns (13개 파생 컬럼)")
    print("   Stage 3: Report Generation + 벡터화 최적화 (82% 성능 개선)")
    print("   Stage 4: Balanced Boost ML + ECDF 캘리브레이션")
    print("=" * 80 + "\n")


def run_stage(
    stage_num: int,
    pipeline_config: Dict,
    stage2_config: Dict,
    args: argparse.Namespace,
) -> bool:
    """특정 Stage를 실행합니다. / Execute a single pipeline stage."""

    stage_start_time = time.time()
    stage_outputs: List[Path] = []

    try:
        if stage_num == 1:
            print("[Stage 1] Data Synchronization...")
            # Try v30 (semantic matching) first, fallback to v29
            if DataSynchronizerV30 is not None:
                print("INFO: Using v3.0 with semantic header matching")
                use_v30 = True
            elif DataSynchronizerV29 is not None:
                print("INFO: Using v2.9 (legacy version)")
                use_v30 = False
            else:
                raise ImportError("Stage 1 동기화 모듈을 불러오지 못했습니다.")
            stage1_cfg = pipeline_config.get("stages", {}).get("stage1", {}).get("io", {})
            if not stage1_cfg:
                raise ValueError("Stage 1 IO 설정이 비어 있습니다.")

            # master_file과 warehouse_file에서 vendor 추론
            # warehouse_file 경로나 설정에서 vendor 힌트가 있으면 사용
            warehouse_file_cfg = stage1_cfg.get("warehouse_file", "")
            vendor_hint = "HE"  # 기본값
            if "sim" in str(warehouse_file_cfg).lower() or "siemens" in str(warehouse_file_cfg).lower():
                vendor_hint = "SIM"
            
            master_path = resolve_repo_path(stage1_cfg.get("master_file", "auto"), vendor=vendor_hint)
            warehouse_path = resolve_repo_path(stage1_cfg.get("warehouse_file", "auto"), vendor=vendor_hint)
            output_path = resolve_repo_path(stage1_cfg["output_file"])
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if not master_path.exists():
                raise FileNotFoundError(f"Stage 1 마스터 파일을 찾을 수 없습니다: {master_path}")
            if not warehouse_path.exists():
                raise FileNotFoundError(f"Stage 1 창고 파일을 찾을 수 없습니다: {warehouse_path}")

            # Select synchronizer based on no_sorting flag and version
            if getattr(args, "no_sorting", False):
                if DataSynchronizerV29NoSorting is None:
                    raise ImportError("비정렬 버전 스크립트를 찾을 수 없습니다.")
                synchronizer = DataSynchronizerV29NoSorting()
                # Update output path for no-sorting version
                sorting_config = stage1_cfg.get("sorting", {})
                no_sorting_suffix = sorting_config.get("no_sorting_suffix", "_no_sorting")
                if no_sorting_suffix:
                    output_path = output_path.with_name(
                        output_path.stem.replace(".synced", no_sorting_suffix) + output_path.suffix
                    )
                print(f"INFO: Using no-sorting version - output: {output_path}")
            else:
                # Use v30 if available, otherwise v29
                if use_v30:
                    use_polars = getattr(args, "use_polars", False)
                    use_xlsxwriter = getattr(args, "use_xlsxwriter", False)
                    synchronizer = DataSynchronizerV30(use_polars=use_polars, use_xlsxwriter=use_xlsxwriter)
                    polars_status = " (Polars enabled)" if use_polars else ""
                    xlsxwriter_status = " (XlsxWriter enabled)" if use_xlsxwriter else ""
                    print(f"INFO: Using v3.0 (semantic matching){polars_status}{xlsxwriter_status} - output: {output_path}")
                else:
                    synchronizer = DataSynchronizerV29()
                    print(f"INFO: Using v2.9 (legacy) - output: {output_path}")

            # Check for multi-vendor warehouse configuration
            warehouse_configs = stage1_cfg.get("warehouse_files")
            if warehouse_configs:
                print(f"INFO: Using multi-vendor warehouse mode with {len(warehouse_configs)} vendors")
                # Resolve paths in configs
                resolved_configs = []
                for cfg in warehouse_configs:
                    resolved_path = resolve_repo_path(cfg["path"])
                    resolved_configs.append({
                        "vendor": cfg["vendor"],
                        "path": str(resolved_path),
                        "required": cfg.get("required", False)
                    })
                sync_result = synchronizer.synchronize(
                    str(master_path), str(warehouse_path), str(output_path),
                    warehouse_configs=resolved_configs
                )
            else:
                # Legacy single-warehouse mode
                sync_result = synchronizer.synchronize(
                    str(master_path), str(warehouse_path), str(output_path)
                )

            if not sync_result.success:
                print(f"[ERROR] Stage 1 failed: {sync_result.message}")
                return False

            stage_outputs.append(Path(sync_result.output_path).resolve())
            logger.info("Stage 1 동기화 통계: %s", sync_result.stats)
            print(f"INFO: Stage 1 produced synced file: {sync_result.output_path}")

            # Great Expectations 검증 (선택적)
            if getattr(args, "validate_with_ge", False):
                try:
                    from scripts.core.ge_validator import validate_stage_output, print_validation_result
                    # pandas는 이미 상단에서 import됨
                    
                    # 합쳐진 파일 로드 및 검증
                    merged_file = sync_result.stats.get("merged_file")
                    if merged_file and Path(merged_file).exists():
                        df = pd.read_excel(merged_file, sheet_name=0)
                        validation_result = validate_stage_output(df, stage_num=1, fail_on_error=False)
                        print_validation_result(validation_result)
                except Exception as e:
                    print(f"[WARNING] GE validation failed: {e}")

        elif stage_num == 2:
            print("[Stage 2] Derived Columns Generation...")
            if process_derived_columns is None or resolve_stage2_synced_input_path is None:
                raise ImportError("Stage 2 파생 컬럼 모듈을 불러오지 못했습니다.")
            shared_synced_path = resolve_stage2_synced_input_path(
                pipeline_config_path=PIPELINE_CONFIG_PATH,
                stage2_config_path=STAGE2_CONFIG_PATH,
                project_root=PROJECT_ROOT,
            )
            print(f"INFO: Stage 2 uses synced file: {shared_synced_path}")

            success = process_derived_columns(
                pipeline_config_path=PIPELINE_CONFIG_PATH,
                stage2_config_path=STAGE2_CONFIG_PATH,
                project_root=PROJECT_ROOT,
            )
            if not success:
                return False

            # Great Expectations 검증 (선택적)
            if getattr(args, "validate_with_ge", False):
                try:
                    from scripts.core.ge_validator import validate_stage_output, print_validation_result
                    # pandas는 이미 상단에서 import됨
                    
                    # Stage 2 출력 파일 로드 및 검증 (이미 로드된 함수 사용)
                    stage2_output = shared_synced_path
                    if stage2_output and Path(stage2_output).exists():
                        df = pd.read_excel(stage2_output, sheet_name=0)
                        validation_result = validate_stage_output(df, stage_num=2, fail_on_error=False)
                        print_validation_result(validation_result)
                except Exception as e:
                    print(f"[WARNING] GE validation failed: {e}")

        elif stage_num == 3:
            print("[Stage 3] Report Generation... (벡터화 최적화)")
            if HVDCExcelReporterFinal is None:
                raise ImportError("Stage 3 보고서 생성 모듈을 불러오지 못했습니다.")
            stage3_cfg = pipeline_config.get("stages", {}).get("stage3", {}).get("io", {})
            if not stage3_cfg:
                raise ValueError("Stage 3 IO 설정이 비어 있습니다.")

            reporter = HVDCExcelReporterFinal()
            calculator = reporter.calculator

            data_root = stage3_cfg.get("data_root")
            if data_root:
                calculator.data_path = resolve_repo_path(data_root)

            hitachi_file = stage3_cfg.get("hitachi_file")
            if hitachi_file:
                hitachi_path = resolve_repo_path(hitachi_file)
                if not hitachi_path.exists():
                    raise FileNotFoundError(
                        f"Stage 3 HITACHI 데이터가 존재하지 않습니다: {hitachi_path}"
                    )
                calculator.hitachi_file = hitachi_path
                calculator.data_path = hitachi_path.parent

            siemens_file = stage3_cfg.get("siemens_file")
            if siemens_file:
                siemens_path = resolve_repo_path(siemens_file)
                if not siemens_path.exists():
                    logger.warning("Stage 3 SIMENSE 데이터가 존재하지 않습니다: %s", siemens_path)
                calculator.simense_file = siemens_path

            invoice_file = stage3_cfg.get("invoice_file")
            if invoice_file:
                invoice_path = resolve_repo_path(invoice_file)
                if not invoice_path.exists():
                    logger.warning("Stage 3 인보이스 데이터가 존재하지 않습니다: %s", invoice_path)
                calculator.invoice_file = invoice_path

            excel_filename = reporter.generate_final_excel_report()
            excel_source = Path.cwd() / excel_filename

            report_dir_override = getattr(args, "stage3_report_dir", None)
            if report_dir_override:
                report_dir = Path(report_dir_override).expanduser().resolve()
            else:
                report_dir = resolve_repo_path(stage3_cfg.get("report_directory", "reports"))
            report_dir.mkdir(parents=True, exist_ok=True)

            if not excel_source.exists():
                raise FileNotFoundError(f"Stage 3 결과 파일을 찾을 수 없습니다: {excel_source}")

            excel_target = report_dir / excel_source.name
            if excel_source.resolve() != excel_target.resolve():
                if excel_target.exists():
                    excel_target.unlink()
                shutil.move(str(excel_source), str(excel_target))
                final_report_path = excel_target
                stage_outputs.append(excel_target.resolve())
            else:
                final_report_path = excel_source
                stage_outputs.append(excel_source.resolve())

            # Great Expectations 검증 (선택적)
            if getattr(args, "validate_with_ge", False):
                try:
                    from scripts.core.ge_validator import validate_stage_output, print_validation_result
                    # pandas는 이미 상단에서 import됨
                    
                    # Stage 3 보고서의 통합 데이터 시트 로드 및 검증
                    if final_report_path.exists():
                        # "통합_원본데이터_Fixed" 시트 찾기
                        xl = pd.ExcelFile(final_report_path)
                        target_sheet = None
                        for sheet in xl.sheet_names:
                            if "통합" in sheet or "Fixed" in sheet:
                                target_sheet = sheet
                                break
                        
                        if target_sheet:
                            df = pd.read_excel(final_report_path, sheet_name=target_sheet)
                            validation_result = validate_stage_output(df, stage_num=3, fail_on_error=False)
                            print_validation_result(validation_result)
                except Exception as e:
                    print(f"[WARNING] GE validation failed: {e}")

            csv_source_dir = Path.cwd() / "output"
            if csv_source_dir.exists() and csv_source_dir.is_dir():
                csv_target_dir = report_dir / "output"
                if csv_source_dir.resolve() != csv_target_dir.resolve():
                    if csv_target_dir.exists():
                        shutil.rmtree(csv_target_dir)
                    shutil.move(str(csv_source_dir), str(csv_target_dir))
                    stage_outputs.append(csv_target_dir.resolve())
                else:
                    stage_outputs.append(csv_source_dir.resolve())

        elif stage_num == 4:
            print("[Stage 4] Anomaly Detection...")
            if DetectorConfig is None or HybridAnomalyDetector is None:
                raise ImportError("Stage 4 이상치 탐지 모듈을 불러오지 못했습니다.")
            stage4_cfg = pipeline_config.get("stages", {}).get("stage4", {}).get("io", {})
            if not stage4_cfg:
                raise ValueError("Stage 4 IO 설정이 비어 있습니다.")

            input_file = stage4_cfg.get("input_file")
            if not input_file:
                raise ValueError("Stage 4 입력 파일 설정이 누락되었습니다.")
            input_path = resolve_repo_path(input_file)

            # 자동 탐색: config의 파일이 없으면 reports 폴더에서 최신 파일 찾기
            if not input_path.exists():
                import re

                filename = input_path.name
                # 타임스탬프 패턴 (YYYYMMDD_HHMMSS) 찾아서 *로 치환
                pattern_str = re.sub(r"_\d{8}_\d{6}_", "_*_", filename)

                report_dir = input_path.parent
                if report_dir.exists():
                    matching_files = sorted(
                        report_dir.glob(pattern_str),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if matching_files:
                        input_path = matching_files[0]
                        print(f"INFO: 최신 보고서 파일 자동 선택: {input_path.name}")
                    else:
                        raise FileNotFoundError(
                            f"Stage 4 입력 파일을 찾을 수 없습니다: {input_file}\n"
                            f"reports 폴더에서 '{pattern_str}' 패턴의 파일도 찾을 수 없습니다."
                        )

            sheet_name = (
                getattr(args, "stage4_sheet_name", None) or stage4_cfg.get("sheet_name") or None
            )

            # Normalize blank/whitespace to default
            if isinstance(sheet_name, str) and not sheet_name.strip():
                sheet_name = DEFAULT_STAGE3_SHEET
            elif sheet_name is None:
                sheet_name = DEFAULT_STAGE3_SHEET

            if not input_path.exists():
                raise FileNotFoundError(f"Stage 4 입력 파일을 찾을 수 없습니다: {input_path}")

            # pandas는 이미 상단에서 import됨
            if input_path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
                df = pd.read_excel(input_path, sheet_name=sheet_name)
            else:
                df = pd.read_csv(input_path)

            detector = HybridAnomalyDetector(DetectorConfig())

            excel_override = getattr(args, "stage4_excel_out", None)
            json_override = getattr(args, "stage4_json_out", None)

            excel_output = excel_override or stage4_cfg.get("excel_output")
            json_output = json_override or stage4_cfg.get("json_output")

            excel_path = resolve_repo_path(excel_output) if excel_output else None
            json_path = resolve_repo_path(json_output) if json_output else None

            if excel_path:
                excel_path.parent.mkdir(parents=True, exist_ok=True)
            if json_path:
                json_path.parent.mkdir(parents=True, exist_ok=True)

            result = detector.run(
                df,
                export_excel=str(excel_path) if excel_path else None,
                export_json=str(json_path) if json_path else None,
            )
            summary = result.get("summary", {})
            logger.info("Stage 4 이상치 요약: %s", summary)

            if excel_path and excel_path.exists():
                stage_outputs.append(excel_path.resolve())
            if json_path and json_path.exists():
                stage_outputs.append(json_path.resolve())

            vis_cfg = stage4_cfg.get("visualization", {})
            visualize_flag = getattr(args, "stage4_visualize", False)
            visualize_off_flag = getattr(args, "stage4_no_visualize", False)
            visualize_default = vis_cfg.get("enable_by_default", False)
            visualize = (
                True if visualize_flag else False if visualize_off_flag else visualize_default
            )

            if visualize:
                if AnomalyVisualizer is None:
                    logger.error(
                        "AnomalyVisualizer 모듈을 불러오지 못했습니다. Stage 4 시각화 표시 비활성화됨을 확인하세요."
                    )
                else:
                    try:
                        case_column = (
                            getattr(args, "stage4_case_column", None)
                            or vis_cfg.get("case_column")
                            or "Case No."
                        )
                        backup_enabled = vis_cfg.get("backup_enabled", True)

                        # sheet_name이 숫자(0)면 "통합_원본데이터_Fixed" 사용
                        viz_sheet = (
                            sheet_name if isinstance(sheet_name, str) else "통합_원본데이터_Fixed"
                        )

                        visualizer = AnomalyVisualizer(result.get("anomalies", []))
                        viz_result = visualizer.apply_anomaly_colors(
                            excel_file=str(input_path),
                            sheet_name=viz_sheet,
                            case_col=case_column,
                            create_backup=backup_enabled,
                        )

                        if viz_result.get("success"):
                            logger.info(
                                "Stage 4 시각화 표시 완료: %s",
                                viz_result.get("message"),
                            )
                            backup_path = viz_result.get("backup_path")
                            if backup_path:
                                stage_outputs.append(Path(backup_path).resolve())
                        else:
                            logger.error(
                                "Stage 4 시각화 표시 실패: %s",
                                viz_result.get("message"),
                            )
                    except Exception as err:  # pylint: disable=broad-except
                        logger.error("시각화 표시 중 오류: %s", err)
        else:
            print(f"ERROR: 알 수 없는 Stage 번호: {stage_num}")
            return False

        stage_duration = time.time() - stage_start_time
        print(f"[OK] Stage {stage_num} completed (Duration: {stage_duration:.2f}s)")
        if stage_outputs:
            print("   Output files:")
            for output in stage_outputs:
                print(f"      - {output}")
        print("")
        return True

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Stage %s 실행 중 오류", stage_num, exc_info=exc)
        print(f"[ERROR] Stage {stage_num} failed: {exc}")
        return False


def run_all_stages(pipeline_config: Dict, stage2_config: Dict, args: argparse.Namespace) -> bool:
    """모든 Stage를 순차적으로 실행합니다. / Run all stages sequentially."""

    print_banner()

    stages = [1, 2, 3, 4]
    total_start_time = time.time()
    
    # ========== 전체 파이프라인 데이터 추적 시스템 ==========
    pipeline_tracker = {
        "stage1": {"input": 0, "output": 0, "loss": 0},
        "stage2": {"input": 0, "output": 0, "loss": 0},
        "stage3": {"input": 0, "output": 0, "loss": 0},
        "stage4": {"input": 0, "output": 0, "loss": 0},
    }
    
    print("\n" + "=" * 60)
    print("[PIPELINE TRACKER] 전체 파이프라인 데이터 추적 시작")
    print("=" * 60)

    for stage_num in stages:
        stage_start_time = time.time()
        stage_key = f"stage{stage_num}"
        
        if not run_stage(stage_num, pipeline_config, stage2_config, args):
            print(f"[FAILED] Pipeline stopped at Stage {stage_num}")
            print(f"\n[PIPELINE TRACKER] 파이프라인 중단 - Stage {stage_num}")
            _print_pipeline_summary(pipeline_tracker)
            return False
        
        stage_duration = time.time() - stage_start_time
        
        # Stage별 행수 정보 출력 (각 Stage에서 로그로 출력되므로 여기서는 요약만)
        print(f"\n[PIPELINE TRACKER] Stage {stage_num} 완료 (소요시간: {stage_duration:.2f}s)")

    total_duration = time.time() - total_start_time
    print("\n" + "=" * 60)
    print("[SUCCESS] All pipeline stages completed!")
    print(f"Total Duration: {total_duration:.2f}s")
    print("=" * 60)
    
    # 전체 파이프라인 요약 출력
    _print_pipeline_summary(pipeline_tracker)

    return True


def _print_pipeline_summary(tracker: Dict) -> None:
    """파이프라인 추적 요약 출력"""
    print("\n" + "=" * 60)
    print("[PIPELINE TRACKER] 전체 파이프라인 데이터 흐름 요약")
    print("=" * 60)
    
    for stage_key, stats in tracker.items():
        stage_num = stage_key.replace("stage", "")
        if stats["input"] > 0:
            loss_pct = (stats["loss"] / stats["input"] * 100) if stats["input"] > 0 else 0
            print(f"Stage {stage_num}:")
            print(f"  - 입력: {stats['input']:,} 행")
            print(f"  - 출력: {stats['output']:,} 행")
            if stats["loss"] > 0:
                print(f"  - 누락: {stats['loss']:,} 행 ({loss_pct:.1f}%)")
            else:
                print(f"  - 누락: 없음")
    
    # 전체 누적 확인
    if tracker["stage1"]["output"] > 0:
        stage1_output = tracker["stage1"]["output"]
        stage2_output = tracker["stage2"]["output"] if tracker["stage2"]["output"] > 0 else stage1_output
        stage3_output = tracker["stage3"]["output"] if tracker["stage3"]["output"] > 0 else stage2_output
        
        print(f"\n전체 누적:")
        print(f"  - Stage 1 → 2: {stage1_output:,} 행")
        print(f"  - Stage 2 → 3: {stage2_output:,} 행")
        print(f"  - Stage 3 → 4: {stage3_output:,} 행")
        
        total_loss = stage1_output - stage3_output
        if total_loss > 0:
            total_loss_pct = (total_loss / stage1_output * 100) if stage1_output > 0 else 0
            print(f"  - 총 누락: {total_loss:,} 행 ({total_loss_pct:.1f}%)")
    
    print("=" * 60)


def run_specific_stages(
    stage_list: List[int],
    pipeline_config: Dict,
    stage2_config: Dict,
    args: argparse.Namespace,
) -> bool:
    """지정된 Stage만 실행합니다. / Run only selected stages."""

    print(f"[INFO] Selected stages: {stage_list}")

    for stage_num in stage_list:
        if not run_stage(stage_num, pipeline_config, stage2_config, args):
            print(f"[FAILED] Pipeline stopped at Stage {stage_num}")
            return False

    print("[SUCCESS] Selected stages completed!")
    return True


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="HVDC 파이프라인 통합 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python run_pipeline.py --all                    # 전체 파이프라인 실행
  python run_pipeline.py --stage 1,2              # Stage 1, 2만 실행
  python run_pipeline.py --stage 2                # Stage 2만 실행
        """,
    )

    parser.add_argument("--all", action="store_true", help="전체 파이프라인 실행 (Stage 1-4)")
    parser.add_argument("--stage", type=str, help="실행할 Stage 번호 (예: 1,2,3 또는 2)")
    parser.add_argument(
        "--stage3-report-dir",
        type=str,
        help="Stage 3 보고서 출력 디렉터리 재정의 / Override Stage 3 report output",
    )
    parser.add_argument(
        "--stage4-visualize",
        action="store_true",
        help="Stage 4 이상치 시각화를 강제 활성화 / Force enable Stage 4 visualization",
    )
    parser.add_argument(
        "--stage4-no-visualize",
        action="store_true",
        help="Stage 4 이상치 시각화 비활성화 / Disable Stage 4 visualization",
    )
    parser.add_argument(
        "--stage4-excel-out",
        type=str,
        help="Stage 4 Excel 출력 경로 재정의 / Override Stage 4 Excel output path",
    )
    parser.add_argument(
        "--stage4-json-out",
        type=str,
        help="Stage 4 JSON 출력 경로 재정의 / Override Stage 4 JSON output path",
    )
    parser.add_argument(
        "--stage4-sheet-name",
        type=str,
        help="Stage 4 Excel 시트명 지정 / Specify Stage 4 sheet name",
    )
    parser.add_argument(
        "--stage4-case-column",
        type=str,
        help="Stage 4 Case 컬럼명 지정 / Specify Stage 4 case column",
    )
    parser.add_argument(
        "--no-sorting",
        action="store_true",
        help="Master NO. 정렬 없이 실행 (빠른 실행) / Run without Master NO. sorting (fast execution)",
    )
    parser.add_argument(
        "--use-polars",
        action="store_true",
        help="Stage 1에서 Polars 사용 (실험적, 성능 개선) / Use Polars for Stage 1 (experimental, performance improvement)",
    )
    parser.add_argument(
        "--use-xlsxwriter",
        action="store_true",
        help="Stage 1에서 XlsxWriter 사용 (Excel 쓰기 성능 개선) / Use XlsxWriter for Stage 1 (Excel writing performance improvement)",
    )
    parser.add_argument(
        "--validate-with-ge",
        action="store_true",
        help="Great Expectations로 각 Stage 출력 검증 (선택적) / Validate each stage output with Great Expectations (optional)",
    )

    args = parser.parse_args()

    # 설정 로드 및 로깅 구성
    pipeline_config = load_pipeline_config()
    stage2_config = load_stage2_config()
    configure_logging(pipeline_config)

    # 인자 검증
    if not args.all and not args.stage:
        parser.print_help()
        return 1

    # 실행
    try:
        if args.all:
            success = run_all_stages(pipeline_config, stage2_config, args)
        else:
            # Stage 번호 파싱
            try:
                stages = [int(s.strip()) for s in args.stage.split(",")]
                stages = [s for s in stages if 1 <= s <= 4]  # 유효한 Stage 번호만

                if not stages:
                    print("ERROR: 유효한 Stage 번호를 입력하세요 (1-4)")
                    return 1

                success = run_specific_stages(stages, pipeline_config, stage2_config, args)
            except ValueError:
                print("ERROR: Stage 번호 형식이 올바르지 않습니다 (예: 1,2,3)")
                return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n[WARNING] Interrupted by user")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
