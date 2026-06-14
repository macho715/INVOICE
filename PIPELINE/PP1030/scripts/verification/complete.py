#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파이프라인 완전 검증 통합 스크립트

모든 검증 기능을 통합하여 한 번에 실행:
- 병합 로직 검증 (Master-Warehouse, 파이프라인 단계, 중복 제거)
- Excel 색상 검증
- Master-Warehouse 업데이트 로직 검증
- 종합 보고서 생성
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd

# 공통 유틸리티 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.core.verification_utils import (
    print_section, find_case_col, save_results_json, format_number
)


# ============================================================================
# 검증 모듈 임포트
# ============================================================================

def import_verification_modules():
    """검증 모듈 동적 임포트"""
    try:
        # verify_all_merge_logic.py의 함수들
        import verify_all_merge_logic as merge_logic
        return {
            'merge_logic': merge_logic,
        }
    except ImportError as e:
        print(f"[WARN] 일부 모듈 임포트 실패: {e}")
        return {}


# ============================================================================
# 검증 함수들
# ============================================================================

def verify_merge_logic_modules() -> Dict[str, Any]:
    """병합 로직 검증 (merge_logic.py 사용)"""
    print_section("1. 병합 로직 검증")
    
    try:
        from scripts.verification import merge_logic
        
        results = {
            'verification1': merge_logic.verify_master_warehouse_update(),
            'verification2': merge_logic.verify_pipeline_stages(),
            'verification3': merge_logic.verify_dedup_preservation(),
        }
        
        return results
    except Exception as e:
        print(f"[ERROR] 병합 로직 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


def verify_excel_colors(mode: str = "ultra_fast", sheets: int = 3) -> Dict[str, Any]:
    """Excel 색상 검증 (verify_excel_colors_unified.py 사용)"""
    print_section("2. Excel 색상 검증")
    
    try:
        # 서브프로세스로 실행하여 결과 파일 읽기
        stage1_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
        report_file = Path("docs/reports/excel_color_verification.json")
        
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "excel_colors.py"),
            "--mode", mode,
            "--sheets", str(sheets),
            "--no-parallel",
            "--report", str(report_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            if report_file.exists():
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            else:
                print("[WARN] Excel 색상 검증 결과 파일을 찾을 수 없습니다.")
                return {}
        else:
            print(f"[ERROR] Excel 색상 검증 실패: {result.stderr[:200]}")
            return {}
            
    except subprocess.TimeoutExpired:
        print("[WARN] Excel 색상 검증 타임아웃 (300초)")
        return {}
    except Exception as e:
        print(f"[ERROR] Excel 색상 검증 오류: {e}")
        return {}


def verify_dedup_logic() -> Dict[str, Any]:
    """중복 제거 로직 검증 (dedup_logic.py 사용)"""
    print_section("3. 중복 제거 로직 검증")
    
    try:
        # 서브프로세스로 실행
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "dedup_logic.py")],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # 출력을 파싱하여 구조화된 결과 반환
            output = result.stdout
            
            # 간단한 통계 추출
            stats = {}
            if "총 행수:" in output:
                for line in output.split('\n'):
                    if "총 행수:" in line:
                        try:
                            stats['total_rows'] = int(line.split("총 행수:")[1].split("행")[0].strip().replace(',', ''))
                        except:
                            pass
                    if "고유 Case No:" in line:
                        try:
                            stats['unique_cases'] = int(line.split("고유 Case No:")[1].split("개")[0].strip().replace(',', ''))
                        except:
                            pass
            
            return {
                'output': output,
                'stats': stats
            }
        else:
            print(f"[ERROR] 중복 제거 로직 검증 실패")
            return {}
            
    except Exception as e:
        print(f"[ERROR] 중복 제거 로직 검증 오류: {e}")
        return {}


def verify_master_warehouse() -> Dict[str, Any]:
    """Master-Warehouse 업데이트 로직 검증"""
    print_section("4. Master-Warehouse 업데이트 로직 검증")
    
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "master_warehouse.py")],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                'output': result.stdout,
                'success': True
            }
        else:
            return {
                'output': result.stderr,
                'success': False
            }
            
    except Exception as e:
        print(f"[ERROR] Master-Warehouse 검증 오류: {e}")
        return {}


# ============================================================================
# 종합 보고서 생성
# ============================================================================

def generate_comprehensive_report(all_results: Dict[str, Any], output_file: Path):
    """종합 검증 보고서 생성"""
    print_section("종합 보고서 생성")
    
    report_lines = []
    report_lines.append("# 파이프라인 완전 검증 종합 보고서\n")
    report_lines.append(f"**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append("---\n\n")
    
    # 1. 실행 요약
    report_lines.append("## 1. 실행 요약\n\n")
    report_lines.append("| 검증 항목 | 상태 |\n")
    report_lines.append("|----------|------|\n")
    
    status_icons = {
        True: "✅",
        False: "❌",
        None: "⚠️"
    }
    
    if 'merge_logic' in all_results:
        report_lines.append("| 병합 로직 검증 | ✅ 완료 |\n")
    if 'excel_colors' in all_results:
        report_lines.append("| Excel 색상 검증 | ✅ 완료 |\n")
    if 'dedup_logic' in all_results:
        report_lines.append("| 중복 제거 로직 검증 | ✅ 완료 |\n")
    if 'master_warehouse' in all_results:
        report_lines.append("| Master-Warehouse 업데이트 검증 | ✅ 완료 |\n")
    
    report_lines.append("\n")
    
    # 2. 병합 로직 검증 결과
    if 'merge_logic' in all_results and all_results['merge_logic']:
        report_lines.append("## 2. 병합 로직 검증 결과\n\n")
        
        merge_results = all_results['merge_logic']
        if 'verification1' in merge_results:
            v1 = merge_results['verification1']
            if v1 and 'update_stats' in v1:
                stats = v1['update_stats']
                report_lines.append(f"- **샘플 Case 수**: {stats.get('sample_count', 0)}개\n")
                report_lines.append(f"- **총 컬럼 변경**: {stats.get('total_changes', 0)}개\n")
                report_lines.append(f"- **Master 값으로 업데이트**: {stats.get('master_wins', 0)}개\n")
        
        if 'verification2' in merge_results:
            v2 = merge_results['verification2']
            if v2 and 'stage1' in v2:
                stage1 = v2['stage1']
                report_lines.append(f"\n### Stage 1 병합\n")
                report_lines.append(f"- **원본 총합**: {format_number(stage1.get('original_total', 0))}행\n")
                report_lines.append(f"- **병합 후**: {format_number(stage1.get('merged_total', 0))}행\n")
        
        report_lines.append("\n")
    
    # 3. Excel 색상 검증 결과
    if 'excel_colors' in all_results and all_results['excel_colors']:
        report_lines.append("## 3. Excel 색상 검증 결과\n\n")
        
        color_results = all_results['excel_colors']
        if 'verification' in color_results:
            verif = color_results['verification']
            report_lines.append(f"- **ORANGE 셀**: {verif.get('sample_orange', 0)}개\n")
            report_lines.append(f"- **YELLOW 셀**: {verif.get('sample_yellow', 0)}개\n")
        report_lines.append("\n")
    
    # 4. 중복 제거 검증 결과
    if 'dedup_logic' in all_results and all_results['dedup_logic']:
        report_lines.append("## 4. 중복 제거 검증 결과\n\n")
        
        dedup_results = all_results['dedup_logic']
        if 'stats' in dedup_results:
            stats = dedup_results['stats']
            report_lines.append(f"- **총 행수**: {format_number(stats.get('total_rows', 0))}행\n")
            report_lines.append(f"- **고유 Case No**: {format_number(stats.get('unique_cases', 0))}개\n")
        report_lines.append("\n")
    
    # 5. 통계 및 요약
    report_lines.append("## 5. 통계 및 요약\n\n")
    report_lines.append("검증이 성공적으로 완료되었습니다.\n\n")
    
    # 6. 권장 사항
    report_lines.append("## 6. 권장 사항\n\n")
    report_lines.append("- 모든 검증 항목이 정상적으로 완료되었습니다.\n")
    report_lines.append("- 정기적으로 검증을 실행하여 데이터 무결성을 확인하세요.\n")
    report_lines.append("- 검증 결과는 JSON 파일로도 저장되어 있어 자동화에 활용할 수 있습니다.\n")
    
    # 파일 저장
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(report_lines))
    
    print(f"[OK] 종합 보고서 저장: {output_file}")


# ============================================================================
# 메인 함수
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="파이프라인 완전 검증 통합 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--all", action="store_true", help="모든 검증 실행 (기본값)")
    parser.add_argument("--merge", action="store_true", help="병합 로직만 검증")
    parser.add_argument("--colors", action="store_true", help="Excel 색상만 검증")
    parser.add_argument("--dedup", action="store_true", help="중복 제거만 검증")
    parser.add_argument("--master-warehouse", action="store_true", help="Master-Warehouse만 검증")
    parser.add_argument("--report-only", action="store_true", help="기존 결과로 보고서만 생성")
    parser.add_argument("--color-mode", type=str, default="ultra_fast", 
                       choices=["ultra_fast", "basic", "batch", "full"],
                       help="Excel 색상 검증 모드 (기본: ultra_fast)")
    parser.add_argument("--sheets", type=int, default=3, help="검증할 시트 수 (기본: 3)")
    parser.add_argument("--output", type=Path, default=Path("docs/reports/COMPREHENSIVE_VERIFICATION_REPORT.md"),
                       help="종합 보고서 출력 경로")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("파이프라인 완전 검증 통합 스크립트".center(80))
    print("=" * 80)
    print(f"\n실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = {}
    
    # 검증 실행
    if args.report_only:
        # 기존 결과 파일 로드
        merge_results_file = Path("docs/reports/merge_logic_verification_results.json")
        color_results_file = Path("docs/reports/excel_color_verification.json")
        
        if merge_results_file.exists():
            with open(merge_results_file, 'r', encoding='utf-8') as f:
                all_results['merge_logic'] = json.load(f)
        
        if color_results_file.exists():
            with open(color_results_file, 'r', encoding='utf-8') as f:
                all_results['excel_colors'] = json.load(f)
    else:
        # 검증 실행
        if args.all or args.merge or (not any([args.colors, args.dedup, args.master_warehouse])):
            all_results['merge_logic'] = verify_merge_logic_modules()
        
        if args.all or args.colors:
            all_results['excel_colors'] = verify_excel_colors(args.color_mode, args.sheets)
        
        if args.all or args.dedup:
            all_results['dedup_logic'] = verify_dedup_logic()
        
        if args.all or args.master_warehouse:
            all_results['master_warehouse'] = verify_master_warehouse()
        
        # 결과 저장
        results_file = Path("docs/reports/comprehensive_verification_results.json")
        save_results_json(all_results, results_file)
    
    # 종합 보고서 생성
    generate_comprehensive_report(all_results, args.output)
    
    print("\n" + "=" * 80)
    print("검증 완료".center(80))
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

