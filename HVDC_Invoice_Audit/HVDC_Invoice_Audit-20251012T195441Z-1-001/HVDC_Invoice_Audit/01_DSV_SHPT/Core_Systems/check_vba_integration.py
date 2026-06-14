#!/usr/bin/env python3
"""VBA 통합 결과 확인"""

import json
from pathlib import Path

# 최신 JSON 파일 찾기
json_dir = Path("../Results/Sept_2025/JSON")
json_files = sorted(json_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

if json_files:
    latest = json_files[0]
    print(f"📄 최신 파일: {latest.name}")
    
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)
    
    # VBA 통합 정보
    vba_info = data.get("vba_integration", {})
    
    print(f"\n📊 VBA 통합 상태:")
    print(f"  활성화: {vba_info.get('enabled', False)}")
    print(f"  MasterData rows: {vba_info.get('master_data_rows', 0)}")
    print(f"  계산 불일치: {vba_info.get('calculation_mismatches', 0)}건")
    
    # 불일치 샘플
    mismatches = vba_info.get('mismatch_details', [])
    if mismatches:
        print(f"\n⚠️ 불일치 샘플 (상위 5건):")
        for m in mismatches[:5]:
            print(f"  S/No {m['s_no']}: Python ${m['python_total']:.2f} vs VBA ${m['vba_total']:.2f} (Δ {m['delta_pct']:.2f}%)")
    
    # 전체 통계
    stats = data.get('statistics', {})
    print(f"\n📊 전체 통계:")
    print(f"  총 항목: {stats.get('total_items', 0)}")
    print(f"  PASS: {stats.get('pass_items', 0)}")
    print(f"  FAIL: {stats.get('fail_items', 0)}")
    
    # 첫 번째 항목 확인 (VBA 컬럼 포함 여부)
    items = data.get('items', [])
    if items:
        first_item = items[0]
        vba_columns = [k for k in first_item.keys() if 'REV' in k or 'DIFFERENCE' in k]
        print(f"\n✅ VBA 컬럼 확인 (첫 번째 항목):")
        for col in vba_columns:
            print(f"  {col}: {first_item.get(col, 'N/A')}")
else:
    print("❌ JSON 파일 없음")

