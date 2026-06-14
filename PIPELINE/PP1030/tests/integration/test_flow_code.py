"""Flow Code v3.5 통합 테스트 - 실제 데이터"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from stage3_report.report_generator import CorrectedWarehouseIOCalculator
import pandas as pd

def main():
    print("=" * 60)
    print("Flow Code v3.5 통합 테스트 - 실제 데이터")
    print("=" * 60)
    
    # 계산기 초기화 및 데이터 로드
    print("\n[1] 데이터 로드 중...")
    calc = CorrectedWarehouseIOCalculator()
    
    try:
        calc.load_real_hvdc_data()
        print(f"✓ 데이터 로드 완료: {len(calc.combined_data):,}건")
    except Exception as e:
        print(f"✗ 데이터 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Flow Code 계산
    print("\n[2] Flow Code v3.5 계산 중...")
    try:
        calc._override_flow_code()
        print("✓ Flow Code 계산 완료")
    except Exception as e:
        print(f"✗ Flow Code 계산 실패: {e}")
        return
    
    # 결과 분석
    print("\n[3] 결과 분석:")
    print("-" * 60)
    
    # Flow Code 분포
    dist = calc.combined_data['FLOW_CODE'].value_counts().sort_index()
    print(f"\nFlow Code 분포:")
    for code in sorted(dist.index):
        count = dist[code]
        pct = (count / len(calc.combined_data)) * 100
        print(f"  Flow {code}: {count:,}건 ({pct:.1f}%)")
    
    # AGI/DAS 강제 승급
    agi_das = calc.combined_data[calc.combined_data['FLOW_OVERRIDE_REASON'].notna()]
    if len(agi_das) > 0:
        print(f"\nAGI/DAS 강제 승급:")
        print(f"  총 {len(agi_das):,}건")
        
        # 원본 Flow Code 분포
        orig_dist = agi_das['FLOW_CODE_ORIG'].value_counts().sort_index()
        print(f"  원본 Flow Code 분포:")
        for code in sorted(orig_dist.index):
            print(f"    {code} → 3: {orig_dist[code]:,}건")
    else:
        print(f"\nAGI/DAS 강제 승급: 0건")
    
    # Flow 5 케이스 분석
    flow5 = calc.combined_data[calc.combined_data['FLOW_CODE'] == 5]
    if len(flow5) > 0:
        print(f"\nFlow 5 (혼합/미완료) 케이스:")
        print(f"  총 {len(flow5):,}건")
        
        # Flow 5 설명 확인
        desc_dist = flow5['FLOW_DESCRIPTION'].value_counts()
        print(f"  상세:")
        for desc, count in desc_dist.items():
            print(f"    {desc}: {count:,}건")
    
    # 검증: 0~5 범위 확인
    invalid = calc.combined_data[~calc.combined_data['FLOW_CODE'].isin([0, 1, 2, 3, 4, 5])]
    if len(invalid) > 0:
        print(f"\n⚠️ 경고: 잘못된 Flow Code 발견: {invalid['FLOW_CODE'].unique()}")
    else:
        print(f"\n✓ 검증: 모든 Flow Code가 0~5 범위 내")
    
    # 샘플 데이터 확인
    print(f"\n[4] 샘플 데이터 확인:")
    print("-" * 60)
    # 존재하는 컬럼만 선택
    available_cols = []
    for col in ['Item_ID', 'Master No', 'Status_Location', 'Final_Location', 'FLOW_CODE', 'FLOW_CODE_ORIG', 'FLOW_DESCRIPTION']:
        if col in calc.combined_data.columns:
            available_cols.append(col)
    
    if 'FLOW_OVERRIDE_REASON' in calc.combined_data.columns:
        available_cols.append('FLOW_OVERRIDE_REASON')
    
    if available_cols:
        sample = calc.combined_data[available_cols].head(10)
        print(sample.to_string(index=False))
    else:
        print("표시할 컬럼을 찾을 수 없습니다.")
    
    print("\n" + "=" * 60)
    print("통합 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()

