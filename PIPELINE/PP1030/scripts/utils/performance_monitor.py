#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 모니터링 (Performance Monitor)
===================================

파이프라인 성능 벤치마크 및 모니터링 유틸리티입니다.
각 Stage의 실행 시간, 메모리 사용량을 측정하고 비교합니다.

사용법:
    python scripts/utils/performance_monitor.py --stage 1 --iterations 3
    python scripts/utils/performance_monitor.py --compare baseline new_version
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_DIR = PROJECT_ROOT / "backups" / "benchmarks"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class StageMetrics:
    """Stage 성능 메트릭"""
    stage: int
    execution_time: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_percent: float
    timestamp: str
    version: str = "unknown"


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""
    version: str
    stage: int
    iterations: int
    metrics: List[StageMetrics]
    avg_execution_time: float
    avg_memory_peak_mb: float
    timestamp: str


class PerformanceMonitor:
    """성능 모니터링"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.benchmark_dir = BENCHMARK_DIR

    def benchmark_stage(
        self, stage_num: int, iterations: int = 3, version: str = "current"
    ) -> BenchmarkResult:
        """
        특정 Stage 벤치마크

        Args:
            stage_num: Stage 번호 (1, 2, 3, 4)
            iterations: 반복 횟수
            version: 버전 식별자

        Returns:
            BenchmarkResult: 벤치마크 결과
        """
        print(f"[BENCHMARK] Stage {stage_num} - {iterations} iterations")
        print(f"Version: {version}\n")

        metrics_list = []

        for i in range(iterations):
            print(f"Iteration {i + 1}/{iterations}...")

            # 프로세스 시작 전 메모리 측정
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            # 실행 시간 측정
            start_time = time.time()
            start_mem = psutil.virtual_memory().used / 1024 / 1024  # MB

            try:
                # 파이프라인 실행
                result = subprocess.run(
                    [
                        sys.executable,
                        str(self.project_root / "run" / "run_pipeline.py"),
                        "--stage",
                        str(stage_num),
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                end_time = time.time()
                end_mem = psutil.virtual_memory().used / 1024 / 1024  # MB

                execution_time = end_time - start_time
                memory_peak = end_mem - start_mem
                memory_avg = (start_mem + end_mem) / 2
                cpu_percent = process.cpu_percent(interval=0.1)

                metrics = StageMetrics(
                    stage=stage_num,
                    execution_time=execution_time,
                    memory_peak_mb=memory_peak,
                    memory_avg_mb=memory_avg,
                    cpu_percent=cpu_percent,
                    timestamp=datetime.now().isoformat(),
                    version=version,
                )

                metrics_list.append(metrics)

                print(f"  Execution time: {execution_time:.2f}s")
                print(f"  Memory peak: {memory_peak:.2f} MB")
                print()

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Stage {stage_num} execution failed:")
                print(e.stderr)
                raise

        # 평균 계산
        avg_execution_time = sum(m.execution_time for m in metrics_list) / len(metrics_list)
        avg_memory_peak = sum(m.memory_peak_mb for m in metrics_list) / len(metrics_list)

        benchmark_result = BenchmarkResult(
            version=version,
            stage=stage_num,
            iterations=iterations,
            metrics=metrics_list,
            avg_execution_time=avg_execution_time,
            avg_memory_peak_mb=avg_memory_peak,
            timestamp=datetime.now().isoformat(),
        )

        # 결과 저장
        self._save_benchmark(benchmark_result)

        print(f"[SUMMARY]")
        print(f"  Average execution time: {avg_execution_time:.2f}s")
        print(f"  Average memory peak: {avg_memory_peak:.2f} MB")
        print(f"  Results saved to: {self._get_benchmark_file(version, stage_num)}")

        return benchmark_result

    def compare_versions(
        self, baseline: str, new_version: str, stage_num: int
    ) -> Dict:
        """
        두 버전 비교

        Args:
            baseline: 기준 버전
            new_version: 비교할 새 버전
            stage_num: Stage 번호

        Returns:
            비교 결과 딕셔너리
        """
        baseline_file = self._get_benchmark_file(baseline, stage_num)
        new_version_file = self._get_benchmark_file(new_version, stage_num)

        if not baseline_file.exists():
            print(f"[ERROR] Baseline benchmark not found: {baseline_file}")
            return {}

        if not new_version_file.exists():
            print(f"[ERROR] New version benchmark not found: {new_version_file}")
            return {}

        # 결과 로드
        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline_result = json.load(f)

        with open(new_version_file, "r", encoding="utf-8") as f:
            new_result = json.load(f)

        # 비교 계산
        baseline_time = baseline_result["avg_execution_time"]
        new_time = new_result["avg_execution_time"]

        time_diff = new_time - baseline_time
        time_diff_pct = (time_diff / baseline_time) * 100

        baseline_mem = baseline_result["avg_memory_peak_mb"]
        new_mem = new_result["avg_memory_peak_mb"]

        mem_diff = new_mem - baseline_mem
        mem_diff_pct = (mem_diff / baseline_mem) * 100

        comparison = {
            "baseline": baseline,
            "new_version": new_version,
            "stage": stage_num,
            "execution_time": {
                "baseline": baseline_time,
                "new": new_time,
                "diff": time_diff,
                "diff_percent": time_diff_pct,
                "improvement": time_diff < 0,
            },
            "memory": {
                "baseline": baseline_mem,
                "new": new_mem,
                "diff": mem_diff,
                "diff_percent": mem_diff_pct,
                "improvement": mem_diff < 0,
            },
        }

        # 결과 출력
        print(f"\n[COMPARISON] {baseline} vs {new_version} (Stage {stage_num})")
        print(f"\nExecution Time:")
        print(f"  Baseline: {baseline_time:.2f}s")
        print(f"  New:      {new_time:.2f}s")
        print(f"  Diff:     {time_diff:+.2f}s ({time_diff_pct:+.1f}%)")
        if time_diff < 0:
            print(f"  ✓ Improvement: {abs(time_diff_pct):.1f}% faster")
        else:
            print(f"  ✗ Regression: {time_diff_pct:.1f}% slower")

        print(f"\nMemory Peak:")
        print(f"  Baseline: {baseline_mem:.2f} MB")
        print(f"  New:      {new_mem:.2f} MB")
        print(f"  Diff:     {mem_diff:+.2f} MB ({mem_diff_pct:+.1f}%)")
        if mem_diff < 0:
            print(f"  ✓ Improvement: {abs(mem_diff_pct):.1f}% less memory")
        else:
            print(f"  ✗ Regression: {mem_diff_pct:.1f}% more memory")

        # 비교 결과 저장
        comparison_file = (
            self.benchmark_dir
            / f"comparison_{baseline}_vs_{new_version}_stage{stage_num}.json"
        )
        with open(comparison_file, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)

        print(f"\nComparison saved to: {comparison_file}")

        return comparison

    def generate_report(self, stage_num: Optional[int] = None) -> Dict:
        """
        성능 리포트 생성

        Args:
            stage_num: Stage 번호 (None이면 전체)

        Returns:
            리포트 딕셔너리
        """
        # 모든 벤치마크 파일 찾기
        pattern = "benchmark_*_stage*.json" if stage_num is None else f"benchmark_*_stage{stage_num}.json"
        benchmark_files = list(self.benchmark_dir.glob(pattern))

        if not benchmark_files:
            print("[WARNING] No benchmark files found")
            return {}

        # 결과 수집
        results = []
        for benchmark_file in benchmark_files:
            try:
                with open(benchmark_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Failed to read {benchmark_file}: {e}")

        # 리포트 생성
        report = {
            "generated_at": datetime.now().isoformat(),
            "stage": stage_num,
            "total_benchmarks": len(results),
            "results": results,
        }

        # 리포트 저장
        report_file = (
            self.benchmark_dir
            / f"report_stage{stage_num or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"[REPORT] Generated: {report_file}")
        print(f"  Total benchmarks: {len(results)}")

        return report

    def _save_benchmark(self, result: BenchmarkResult) -> Path:
        """벤치마크 결과 저장"""
        filename = f"benchmark_{result.version}_stage{result.stage}.json"
        filepath = self.benchmark_dir / filename

        # 딕셔너리로 변환 (dataclass → dict)
        data = asdict(result)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def _get_benchmark_file(self, version: str, stage_num: int) -> Path:
        """벤치마크 파일 경로"""
        return self.benchmark_dir / f"benchmark_{version}_stage{stage_num}.json"


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description="성능 모니터링")
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3, 4],
        help="Stage 번호",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="반복 횟수 (기본값: 3)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="current",
        help="버전 식별자",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "NEW_VERSION"),
        help="두 버전 비교",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="성능 리포트 생성",
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    if args.compare:
        if not args.stage:
            print("[ERROR] --stage required for comparison")
            sys.exit(1)
        monitor.compare_versions(args.compare[0], args.compare[1], args.stage)
    elif args.report:
        monitor.generate_report(args.stage)
    elif args.stage:
        monitor.benchmark_stage(args.stage, args.iterations, args.version)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

