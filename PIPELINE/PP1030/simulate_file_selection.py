#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 선택 시뮬레이션 - 실제 file_finder.py 로직 사용
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# file_finder.py 모듈 import
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "core"))
from file_finder import scan_raw_folder, find_vendor_files, RawFileHit

def extract_date_from_filename(filename: str) -> str | None:
    """파일명에서 날짜 추출 (YYYYMMDD 또는 YYYYMM)"""
    patterns = [
        r'(\d{8})',  # YYYYMMDD
        r'(\d{6})',  # YYYYMM
        r'(\d{4})[\.\-_]?(\d{2})[\.\-_]?(\d{2})',  # YYYY-MM-DD
    ]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(0).replace('-', '').replace('_', '').replace('.', '')
            if len(date_str) >= 6:
                return date_str
    return None

def format_date(date_str: str) -> str:
    """날짜 문자열 포맷팅"""
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    elif len(date_str) == 6:
        return f"{date_str[:4]}-{date_str[4:6]}"
    return date_str

def calculate_depth(path: Path, raw_dir: Path) -> int:
    """depth 계산 (file_finder.py와 동일한 로직)"""
    try:
        raw_dir_resolved = raw_dir.resolve()
        rel_path = path.resolve().relative_to(raw_dir_resolved)
        depth = len(rel_path.parts) - 1
    except (ValueError, AttributeError):
        depth = 0
    return depth

def main():
    raw_dir = Path("data/raw")
    
    print("=" * 100)
    print("파일 선택 시뮬레이션 - data/raw 폴더 분석")
    print("=" * 100)
    print(f"분석 대상 폴더: {raw_dir.absolute()}\n")
    
    if not raw_dir.exists():
        print(f"[오류] {raw_dir} 폴더를 찾을 수 없습니다.")
        return 1
    
    # 실제 file_finder.py 로직 사용
    print("[파일 스캔 중...]\n")
    all_hits = scan_raw_folder(raw_dir)
    selected = find_vendor_files(raw_dir)
    
    # 결과 출력
    for vendor in ["HE", "SIM"]:
        print(f"\n{'=' * 100}")
        print(f"[{vendor} Vendor 파일 분석]")
        print("=" * 100)
        
        files = all_hits[vendor]
        if not files:
            print(f"  [X] {vendor} vendor 파일 없음")
            continue
        
        # 점수순 정렬
        sorted_files = sorted(files, key=lambda h: h.score, reverse=True)
        
        print(f"  발견된 파일: {len(sorted_files)}개\n")
        print(f"  {'순위':<4} {'파일명':<55} {'점수':<8} {'depth':<6} {'날짜':<12} {'상태'}")
        print("  " + "-" * 100)
        
        selected_file = selected[vendor]
        
        for idx, hit in enumerate(sorted_files, 1):
            rel_path = hit.path.relative_to(raw_dir)
            depth = calculate_depth(hit.path, raw_dir)
            date_str = extract_date_from_filename(hit.path.name)
            date_display = format_date(date_str) if date_str else "없음"
            
            is_selected = selected_file and selected_file.path == hit.path
            status = "[선택됨]" if is_selected else ""
            
            print(f"  {idx:<4} {hit.path.name:<55} {hit.score:>7.2f} {depth:<6} {date_display:<12} {status}")
        
        # 선택된 파일 상세 정보
        if selected_file:
            print(f"\n  [최종 선택된 파일]")
            print(f"     경로: {selected_file.path}")
            print(f"     상대 경로: {selected_file.path.relative_to(raw_dir)}")
            print(f"     점수: {selected_file.score:.2f}")
            depth = calculate_depth(selected_file.path, raw_dir)
            print(f"     depth: {depth}")
            print(f"     파일명 길이: {len(selected_file.path.stem)}자")
            print(f"     점수 계산: 100.0 - {depth} * 2 - {len(selected_file.path.stem)} / 50.0 = {selected_file.score:.2f}")
            date_str = extract_date_from_filename(selected_file.path.name)
            if date_str:
                print(f"     추출된 날짜: {format_date(date_str)}")
            else:
                print(f"     추출된 날짜: 없음 (날짜 기반 선택 불가)")
    
    # 날짜 기반 선택 시뮬레이션
    print(f"\n{'=' * 100}")
    print("[날짜 기반 선택 시뮬레이션]")
    print("=" * 100)
    print("  현재 시스템은 날짜를 고려하지 않고 점수 기반으로만 선택합니다.")
    print("  만약 날짜 기반 선택이 있었다면:\n")
    
    for vendor in ["HE", "SIM"]:
        files = all_hits[vendor]
        files_with_dates = []
        for hit in files:
            date_str = extract_date_from_filename(hit.path.name)
            if date_str:
                files_with_dates.append((hit, date_str))
        
        if files_with_dates:
            # 날짜순 정렬 (최신 우선)
            files_with_dates.sort(key=lambda x: x[1], reverse=True)
            latest = files_with_dates[0]
            current = selected[vendor]
            
            print(f"  [{vendor}]")
            print(f"     날짜 기반 선택: {latest[0].path.name}")
            print(f"                    날짜: {format_date(latest[1])}")
            print(f"                    점수: {latest[0].score:.2f}")
            
            if current:
                print(f"     현재 선택:      {current.path.name}")
                print(f"                    점수: {current.score:.2f}")
                
                if current.path != latest[0].path:
                    print(f"     [!] 차이: 날짜 기반 선택과 다름!")
                    print(f"        날짜 기반: {latest[0].path.name} (날짜: {format_date(latest[1])})")
                    print(f"        점수 기반:  {current.path.name} (점수: {current.score:.2f})")
                else:
                    print(f"     [OK] 일치: 날짜 기반과 점수 기반 선택이 동일합니다.")
            print()
    
    # 요약
    print(f"\n{'=' * 100}")
    print("[요약]")
    print("=" * 100)
    for vendor in ["HE", "SIM"]:
        current = selected[vendor]
        if current:
            print(f"  {vendor}: {current.path.name} (점수: {current.score:.2f})")
        else:
            print(f"  {vendor}: 선택된 파일 없음")
    
    print(f"\n{'=' * 100}")
    print("시뮬레이션 완료!")
    print("=" * 100)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
