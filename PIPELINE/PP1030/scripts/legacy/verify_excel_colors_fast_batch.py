#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 색상 검증 - 배치 처리 버전 (2000개씩 여러 번 나눠서 실행)
"""

from pathlib import Path
import json
import subprocess
import sys

def run_batch_verification():
    """2000개씩 여러 번 나눠서 검증"""
    
    stage1_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    report_base = Path("docs/reports/excel_color_verification_fast.json")
    
    # 배치 설정
    batches = [
        {"name": "상단", "rows": 200, "cols": 10, "tail_rows": 0, "random_sample": 0},
        {"name": "중간상단", "rows": 0, "cols": 10, "tail_rows": 0, "random_sample": 100, "random_seed": 42},
        {"name": "중간", "rows": 0, "cols": 10, "tail_rows": 0, "random_sample": 100, "random_seed": 123},
        {"name": "중간하단", "rows": 0, "cols": 10, "tail_rows": 0, "random_sample": 100, "random_seed": 456},
        {"name": "하단", "rows": 0, "cols": 10, "tail_rows": 200, "random_sample": 0},
    ]
    
    all_results = {
        "batches": [],
        "total_orange": 0,
        "total_yellow": 0
    }
    
    print("=" * 80)
    print("Excel 색상 검증 - 배치 처리 (2000개씩)".center(80))
    print("=" * 80)
    
    for i, batch in enumerate(batches, 1):
        print(f"\n[{i}/{len(batches)}] 배치 실행: {batch['name']}")
        print("-" * 80)
        
        # 명령어 구성
        cmd = [
            sys.executable,
            "verify_excel_colors_optimized.py",
            "--rows", str(batch["rows"]),
            "--cols", str(batch["cols"]),
            "--tail-rows", str(batch.get("tail_rows", 0)),
            "--random-sample", str(batch.get("random_sample", 0)),
            "--sheets", "1",
            "--no-parallel",
            "--max-cells", "2000"
        ]
        
        if batch.get("random_seed"):
            cmd.extend(["--random-seed", str(batch["random_seed"])])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30초 타임아웃
            )
            
            if result.returncode == 0:
                # 결과 파일 읽기
                if report_base.exists():
                    with open(report_base, "r", encoding="utf-8") as f:
                        batch_result = json.load(f)
                    
                    orange = batch_result.get("verification", {}).get("sample_orange", 0)
                    yellow = batch_result.get("verification", {}).get("sample_yellow", 0)
                    
                    all_results["batches"].append({
                        "name": batch["name"],
                        "orange": orange,
                        "yellow": yellow,
                        "params": batch
                    })
                    
                    all_results["total_orange"] += orange
                    all_results["total_yellow"] += yellow
                    
                    print(f"  ✅ 완료: ORANGE={orange}, YELLOW={yellow}")
                else:
                    print(f"  ⚠️ 결과 파일을 찾을 수 없습니다")
            else:
                print(f"  ❌ 실행 실패: {result.stderr[:100]}")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏱️ 타임아웃 (30초 초과)")
        except Exception as e:
            print(f"  ❌ 오류: {e}")
    
    # 최종 결과 저장
    final_report = Path("docs/reports/excel_color_verification_batch.json")
    final_report.parent.mkdir(parents=True, exist_ok=True)
    
    with open(final_report, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("배치 검증 완료".center(80))
    print("=" * 80)
    print(f"총 ORANGE: {all_results['total_orange']}개")
    print(f"총 YELLOW: {all_results['total_yellow']}개")
    print(f"\n결과 저장: {final_report}")
    
    return all_results

if __name__ == "__main__":
    run_batch_verification()

