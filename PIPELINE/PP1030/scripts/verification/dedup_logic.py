#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중복 제거 시 남겨두는 데이터 처리 방식 상세 분석
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def analyze_dedup_keep_logic():
    """중복 제거 시 keep='first' 처리 방식 분석"""
    print("=" * 80)
    print("중복 제거 시 남겨두는 데이터 처리 방식 분석")
    print("=" * 80)
    
    print("\n[1] drop_duplicates_by_case 함수 동작 원리")
    print("-" * 80)
    print("""
drop_duplicates_by_case 함수는 다음과 같이 작동합니다:

1. Case No 정규화:
   - Case No 값을 정규화 (대문자 변환, 공백 제거, 구분자 통일)
   - 예: "Case 123", "CASE-123", "case_123" → 모두 "CASE-123"으로 통일

2. keep='first' 정책:
   - pandas의 duplicated(keep='first') 메서드 사용
   - 데이터프레임의 인덱스 순서상 첫 번째로 나타나는 행을 유지
   - 이후에 나타나는 중복 행은 제거됨

3. 빈 키 행 보존:
   - Case No가 비어있거나 NaN인 행은 중복 제거 대상에서 제외
   - preserve_empty_keys=True (기본값)일 때 모든 빈 키 행 보존
   """)
    
    print("\n[2] Stage 1에서 시트 결합 순서")
    print("-" * 80)
    print("""
Stage 1에서 여러 시트를 결합할 때 순서가 중요합니다:

1. 시트 순서 정의 (line 2076-2087):
   - Case List, RIL (우선순위 1)
   - HE Local (우선순위 2)
   - HE-0214,0252 (Capacitor) (우선순위 3)
   - 기타 시트들 (우선순위 4)

2. pd.concat() 실행 (line 2185):
   - sheet_order 순서대로 결합
   - ignore_index=True: 인덱스 재설정
   - sort=False: 정렬 없음 (순서 유지)

3. 중복 제거 실행 (line 2241):
   - 결합된 데이터프레임 전체에 대해 drop_duplicates_by_case 실행
   - keep='first'로 인해 앞쪽 시트(Case List, RIL)의 데이터가 우선 유지됨
   """)
    
    print("\n[3] 실제 데이터 확인")
    print("-" * 80)
    
    merged_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
    
    if merged_file.exists():
        df = pd.read_excel(merged_file)
        
        if 'Case No.' in df.columns and 'Source_Sheet' in df.columns:
            # 중복이 있었던 Case No 샘플 찾기
            case_col = 'Case No.'
            
            # 빈 키 제외
            non_empty = df[case_col].notna() & (df[case_col].astype(str).str.strip() != "")
            df_valid = df[non_empty].copy()
            
            # 중복 Case No 찾기 (현재는 중복 제거 후이므로, Source_Sheet 분포로 확인)
            if len(df_valid) > 0:
                case_counts = df_valid[case_col].value_counts()
                
                # Source_Sheet 분포 확인
                sheet_dist = df_valid['Source_Sheet'].value_counts()
                print(f"전체 유효 Case No: {len(df_valid):,}개")
                print(f"\nSource_Sheet 분포:")
                for sheet, count in sheet_dist.items():
                    print(f"  - {sheet}: {count:,}행 ({count/len(df_valid)*100:.1f}%)")
                
                # 시트별 Case No 개수 확인
                print(f"\n시트별 고유 Case No 개수:")
                for sheet in sheet_dist.index:
                    sheet_df = df_valid[df_valid['Source_Sheet'] == sheet]
                    unique_cases = sheet_df[case_col].nunique()
                    print(f"  - {sheet}: {unique_cases:,}개 고유 Case No")
                
                # 중복 제거 후 결과 확인
                print(f"\n중복 제거 후 결과:")
                print(f"  - 총 행수: {len(df):,}행")
                print(f"  - 고유 Case No: {df_valid[case_col].nunique():,}개")
                print(f"  - CASE_LIST 시트 우선 유지: {sheet_dist.get('CASE_LIST', 0):,}행")
                
                # 만약 동일 Case No가 여러 시트에 있었을 경우, CASE_LIST가 우선
                # 하지만 현재는 이미 중복 제거가 완료된 상태이므로 확인이 어려움
                print(f"\n  [참고] 중복 제거가 이미 완료된 상태이므로,")
                print(f"        실제 중복 케이스는 Stage 1 실행 로그에서 확인 가능합니다.")
        else:
            print("Case No. 또는 Source_Sheet 컬럼을 찾을 수 없습니다.")
    else:
        print(f"파일을 찾을 수 없습니다: {merged_file}")
    
    print("\n[4] 중복 제거 시 우선순위 정리")
    print("-" * 80)
    print("""
중복 제거 시 남겨지는 데이터의 우선순위:

1. 시트 순서 우선순위:
   Case List, RIL > HE Local > Capacitor > 기타 시트

2. keep='first' 동작:
   - 데이터프레임에서 먼저 나타나는 행이 유지됨
   - pd.concat()으로 시트를 결합할 때 Case List, RIL이 먼저 오므로
   - 동일 Case No가 여러 시트에 있으면 Case List, RIL의 데이터가 유지됨

3. 빈 키 행:
   - Case No가 비어있는 행은 중복 제거 대상에서 제외
   - 모든 빈 키 행이 보존됨

4. 데이터 처리 예시:
   
   시트1 (Case List, RIL):
   Case No | Value
   123     | A
   456     | B
   
   시트2 (HE Local):
   Case No | Value
   123     | C  ← 중복
   789     | D
   
   결합 후:
   Case No | Value | Source_Sheet
   123     | A     | CASE_LIST     ← keep='first'로 유지
   456     | B     | CASE_LIST
   123     | C     | HE_LOCAL      ← 중복으로 제거됨
   789     | D     | HE_LOCAL
   
   중복 제거 후:
   Case No | Value | Source_Sheet
   123     | A     | CASE_LIST     ← 첫 번째 발생만 유지
   456     | B     | CASE_LIST
   789     | D     | HE_LOCAL
   """)
    
    print("\n[5] 코드 위치")
    print("-" * 80)
    print("""
관련 코드 위치:

1. 시트 순서 정의:
   scripts/stage1_sync_sorted/data_synchronizer_v30.py
   - Line 2076-2087: sheet_order 정의

2. 시트 결합:
   scripts/stage1_sync_sorted/data_synchronizer_v30.py
   - Line 2185: pd.concat(combined_dfs, ignore_index=True, sort=False)

3. 중복 제거:
   scripts/stage1_sync_sorted/data_synchronizer_v30.py
   - Line 2241-2243: drop_duplicates_by_case(keep="first")
   
   scripts/core/duplicate_handler.py
   - Line 178-246: drop_duplicates_by_case 함수 구현
   - Line 229: duplicated(keep='first') 실행
   """)

def main():
    """메인 실행 함수"""
    try:
        analyze_dedup_keep_logic()
        
        print("\n" + "=" * 80)
        print("분석 완료")
        print("=" * 80)
        
    except Exception as e:
        import traceback
        print(f"\n오류 발생: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

