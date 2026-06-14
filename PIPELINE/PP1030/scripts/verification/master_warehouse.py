#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case List 파일(Master)과 HVDC 파일(Warehouse) 업데이트 시 동일 Case 처리 방식 분석
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def analyze_master_warehouse_update_logic():
    """Master와 Warehouse 동일 Case 처리 방식 분석"""
    print("=" * 80)
    print("Case List 파일(Master)과 HVDC 파일(Warehouse) 업데이트 시")
    print("동일 Case 처리 방식 상세 분석")
    print("=" * 80)
    
    print("\n[1] 처리 흐름 개요")
    print("-" * 80)
    print("""
Stage 1에서 Master(Case List) 파일과 Warehouse(HVDC WAREHOUSE) 파일을 병합할 때:

1. Case No 기준 매칭:
   - Master의 각 행에 대해 Warehouse에 동일 Case No가 있는지 확인
   - Case No가 있으면: 업데이트
   - Case No가 없으면: 신규 추가

2. 업데이트 우선순위:
   - Master 데이터가 항상 우선 (Master → Warehouse 방향)
   - Warehouse 데이터는 Master 데이터로 덮어씌워짐
   """)
    
    print("\n[2] 동일 Case No 발견 시 처리 방식")
    print("-" * 80)
    print("""
동일 Case No가 Master와 Warehouse에 모두 있을 때 (_apply_updates 함수):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Source_Sheet 업데이트 (Line 1698-1705)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - Master의 Source_Sheet 값으로 Warehouse를 업데이트
   - 원본 시트 이름을 반영하기 위함

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. Source_Vendor 업데이트 (Line 1707-1713)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - Master의 Source_Vendor 값으로 Warehouse를 업데이트
   - 벤더 정보를 반영하기 위함

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. 공통 컬럼 처리 (Line 1715-1764)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   A. 메타데이터 컬럼 제외 (Line 1721-1722):
      - Source_Sheet, Source_Vendor는 이미 위에서 처리
      - METADATA_COLUMNS에 포함된 컬럼은 Warehouse 원본 값 유지
   
   B. 날짜 컬럼 처리 (Line 1728-1748):
      조건: semantic_key in date_semantic_keys
      
      규칙:
      - Master에 값이 있으면 무조건 업데이트 (Master 우선)
      - Warehouse 값과 다르면 업데이트
      - 같은 날짜라도 형식 통일 (mval로 덮어쓰기)
      
      예시:
      Master: ETD/ATD = 2024-05-17
      Warehouse: ETD/ATD = 2024-05-18
      → 결과: ETD/ATD = 2024-05-17 (Master 값으로 업데이트)
   
   C. 비날짜 컬럼 처리 (Line 1749-1764):
      조건: ALWAYS_OVERWRITE_NONDATE = True (Line 232)
      
      규칙:
      - Master에 값이 있으면 무조건 업데이트
      - Warehouse 값과 다르면 업데이트
      
      예시:
      Master: Product = "A"
      Warehouse: Product = "B"
      → 결과: Product = "A" (Master 값으로 업데이트)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. Master 전용 컬럼 처리 (Line 1766-1790)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - Master에만 있는 컬럼을 Warehouse에 추가
   - 해당 Case의 값으로 업데이트
   - 예: "DHL WH" 컬럼이 Master에만 있는 경우
   """)
    
    print("\n[3] 실제 데이터 예시")
    print("-" * 80)
    print("""
[시나리오] 동일 Case No "207557"이 Master와 Warehouse에 모두 있음

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[처리 전]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Master (Case List):
Case No | ETD/ATD      | ETA/ATA      | Product | DHL WH
207557  | 2024-05-17  | 2024-06-25  | Item A  | 2024-06-01

Warehouse (HVDC):
Case No | ETD/ATD      | ETA/ATA      | Product | DHL WH
207557  | 2024-05-18  | 2024-06-25  | Item B  | (없음)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[처리 후]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Warehouse (업데이트됨):
Case No | ETD/ATD      | ETA/ATA      | Product | DHL WH
207557  | 2024-05-17  | 2024-06-25  | Item A  | 2024-06-01
        ↑ Master 값  ↑ 같음(유지)  ↑ Master 값 ↑ Master 값 추가

변경 사항:
- ETD/ATD: 2024-05-18 → 2024-05-17 (Master 값으로 업데이트)
- Product: Item B → Item A (Master 값으로 업데이트)
- DHL WH: (없음) → 2024-06-01 (Master 전용 컬럼 추가 및 값 업데이트)
- ETA/ATA: 변경 없음 (값이 동일)
   """)
    
    print("\n[4] 핵심 정책")
    print("-" * 80)
    print("""
1. Master 우선 정책 (Master → Warehouse):
   - 모든 컬럼에서 Master 데이터가 우선
   - Warehouse 데이터는 Master 데이터로 덮어씌워짐

2. 날짜 컬럼 처리:
   - Master에 값이 있으면 무조건 업데이트
   - 날짜 형식 통일 (Master 형식으로 표준화)
   - _dates_equal() 함수로 논리적 동등성 확인

3. 비날짜 컬럼 처리:
   - ALWAYS_OVERWRITE_NONDATE = True
   - Master에 값이 있으면 무조건 업데이트
   - 문자열 비교로 값 변경 확인

4. Master 전용 컬럼:
   - Warehouse에 없는 컬럼은 추가
   - 해당 Case의 값으로 업데이트

5. 메타데이터 컬럼:
   - Source_Sheet, Source_Vendor는 Master 값으로 업데이트
   - 원본 출처 정보 반영
   """)
    
    print("\n[5] 코드 위치")
    print("-" * 80)
    print("""
관련 코드 위치:

1. 업데이트 로직:
   scripts/stage1_sync_sorted/data_synchronizer_v30.py
   - Line 1587-1799: _apply_updates() 함수
   
2. 날짜 컬럼 처리:
   - Line 1728-1748: 날짜 컬럼 업데이트 로직
   - Line 390-405: _dates_equal() 함수 (날짜 동등성 확인)
   - Line 365: date_semantic_keys 초기화
   
3. 비날짜 컬럼 처리:
   - Line 1749-1764: 비날짜 컬럼 업데이트 로직
   - Line 232: ALWAYS_OVERWRITE_NONDATE = True 설정
   
4. 신규 케이스 추가:
   - Line 1658-1691: 신규 케이스 추가 로직
   """)
    
    print("\n[6] 통계 정보")
    print("-" * 80)
    
    merged_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
    
    if merged_file.exists():
        df = pd.read_excel(merged_file)
        
        if 'Case No.' in df.columns:
            total_cases = len(df)
            print(f"총 케이스 수: {total_cases:,}개")
            print(f"\n[참고] 실제 업데이트 통계는 Stage 1 실행 로그에서 확인 가능합니다:")
            print("  - Date updates: 날짜 컬럼 업데이트 수")
            print("  - Field updates: 비날짜 컬럼 업데이트 수")
            print("  - New records: 신규 추가된 케이스 수")
            print("  - Source_Sheet updates: Source_Sheet 업데이트 수")

def main():
    """메인 실행 함수"""
    try:
        analyze_master_warehouse_update_logic()
        
        print("\n" + "=" * 80)
        print("분석 완료")
        print("=" * 80)
        print("\n[요약]")
        print("-" * 80)
        print("""
동일 Case No 처리 규칙:
1. Master 데이터가 항상 우선
2. 날짜 컬럼: Master 값이 있으면 무조건 업데이트
3. 비날짜 컬럼: Master 값이 있으면 무조건 업데이트 (ALWAYS_OVERWRITE_NONDATE=True)
4. Master 전용 컬럼: Warehouse에 추가 및 값 업데이트
5. 메타데이터: Source_Sheet, Source_Vendor는 Master 값으로 업데이트
        """)
        
    except Exception as e:
        import traceback
        print(f"\n오류 발생: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

