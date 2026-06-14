#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
헤더 순서 비교 보고서 생성 스크립트
각 스테이지별 실제 헤더 순서를 추출하여 Excel 보고서로 생성
"""

import pandas as pd
import openpyxl
from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple

def extract_stage1_headers():
    """Stage 1 출력 파일에서 헤더 추출"""
    file_path = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    
    if not file_path.exists():
        print(f"❌ Stage 1 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    try:
        # 첫 번째 시트의 헤더 추출
        df = pd.read_excel(file_path, sheet_name=0, nrows=0)
        headers = df.columns.tolist()
        print(f"✅ Stage 1 헤더 추출 완료: {len(headers)}개")
        return headers
    except Exception as e:
        print(f"❌ Stage 1 헤더 추출 실패: {e}")
        return []

def extract_stage2_headers():
    """Stage 2 출력 파일에서 헤더 추출"""
    file_path = Path("data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx")
    
    if not file_path.exists():
        print(f"❌ Stage 2 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    try:
        df = pd.read_excel(file_path, nrows=0)
        headers = df.columns.tolist()
        print(f"✅ Stage 2 헤더 추출 완료: {len(headers)}개")
        return headers
    except Exception as e:
        print(f"❌ Stage 2 헤더 추출 실패: {e}")
        return []

def extract_stage3_headers():
    """Stage 3 출력 파일에서 헤더 추출"""
    file_path = Path("data/processed/reports/HVDC_입고로직_종합리포트_20251029_061139_v3.0-corrected.xlsx")
    
    if not file_path.exists():
        print(f"❌ Stage 3 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    try:
        # '통합_원본데이터_Fixed' 시트 찾기
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        target_sheet = None
        for sheet_name in sheet_names:
            if '통합_원본데이터_Fixed' in sheet_name:
                target_sheet = sheet_name
                break
        
        if target_sheet is None:
            print(f"❌ '통합_원본데이터_Fixed' 시트를 찾을 수 없습니다. 사용 가능한 시트: {sheet_names}")
            return []
        
        df = pd.read_excel(file_path, sheet_name=target_sheet, nrows=0)
        headers = df.columns.tolist()
        print(f"✅ Stage 3 헤더 추출 완료: {len(headers)}개 (시트: {target_sheet})")
        return headers
    except Exception as e:
        print(f"❌ Stage 3 헤더 추출 실패: {e}")
        return []

def extract_standard_headers():
    """표준 헤더 순서 정의 추출"""
    file_path = Path("scripts/core/standard_header_order.py")
    
    if not file_path.exists():
        print(f"❌ 표준 헤더 순서 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # STANDARD_HEADER_ORDER 리스트 추출
        pattern = r'STANDARD_HEADER_ORDER\s*=\s*\[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("❌ STANDARD_HEADER_ORDER 리스트를 찾을 수 없습니다")
            return []
        
        # 리스트 내용 파싱
        list_content = match.group(1)
        headers = []
        
        # 각 라인에서 문자열 추출
        for line in list_content.split('\n'):
            line = line.strip()
            if line.startswith('"') and line.endswith('",'):
                header = line[1:-2]  # 따옴표와 쉼표 제거
                headers.append(header)
            elif line.startswith('"') and line.endswith('"'):
                header = line[1:-1]  # 따옴표 제거
                headers.append(header)
        
        print(f"✅ 표준 헤더 순서 추출 완료: {len(headers)}개")
        return headers
    except Exception as e:
        print(f"❌ 표준 헤더 순서 추출 실패: {e}")
        return []

def create_comparison_report():
    """헤더 순서 비교 보고서 생성"""
    print("=" * 60)
    print("헤더 순서 비교 보고서 생성 시작")
    print("=" * 60)
    
    # 각 스테이지별 헤더 추출
    stage1_headers = extract_stage1_headers()
    stage2_headers = extract_stage2_headers()
    stage3_headers = extract_stage3_headers()
    standard_headers = extract_standard_headers()
    
    if not all([stage1_headers, stage2_headers, stage3_headers, standard_headers]):
        print("❌ 일부 헤더 추출에 실패했습니다. 보고서 생성을 중단합니다.")
        return
    
    # 최대 길이 계산
    max_length = max(len(stage1_headers), len(stage2_headers), len(stage3_headers), len(standard_headers))
    
    # 비교 데이터 생성
    comparison_data = []
    for i in range(max_length):
        row = {
            '순번': i + 1,
            'Stage 1 헤더': stage1_headers[i] if i < len(stage1_headers) else '',
            'Stage 2 헤더': stage2_headers[i] if i < len(stage2_headers) else '',
            'Stage 3 헤더': stage3_headers[i] if i < len(stage3_headers) else '',
            '표준 순서': standard_headers[i] if i < len(standard_headers) else '',
            '일치여부': '',
            '비고': ''
        }
        
        # 일치 여부 확인
        if i < len(stage1_headers) and i < len(stage2_headers) and i < len(stage3_headers) and i < len(standard_headers):
            if (stage1_headers[i] == stage2_headers[i] == stage3_headers[i] == standard_headers[i]):
                row['일치여부'] = '✅'
            else:
                row['일치여부'] = '❌'
                row['비고'] = '순서 불일치'
        else:
            row['일치여부'] = '⚠️'
            row['비고'] = '길이 차이'
        
        comparison_data.append(row)
    
    # Excel 파일 생성
    output_file = Path("header_order_comparison_report.xlsx")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 시트 1: 헤더 순서 비교
        df_comparison = pd.DataFrame(comparison_data)
        df_comparison.to_excel(writer, sheet_name='헤더 순서 비교', index=False)
        
        # 시트 2: Stage 1 전체 헤더
        df_stage1 = pd.DataFrame({
            '순번': range(1, len(stage1_headers) + 1),
            'Stage 1 헤더': stage1_headers
        })
        df_stage1.to_excel(writer, sheet_name='Stage 1 전체 헤더', index=False)
        
        # 시트 3: Stage 2 전체 헤더
        df_stage2 = pd.DataFrame({
            '순번': range(1, len(stage2_headers) + 1),
            'Stage 2 헤더': stage2_headers
        })
        df_stage2.to_excel(writer, sheet_name='Stage 2 전체 헤더', index=False)
        
        # 시트 4: Stage 3 전체 헤더
        df_stage3 = pd.DataFrame({
            '순번': range(1, len(stage3_headers) + 1),
            'Stage 3 헤더': stage3_headers
        })
        df_stage3.to_excel(writer, sheet_name='Stage 3 전체 헤더', index=False)
        
        # 시트 5: 표준 순서 정의
        df_standard = pd.DataFrame({
            '순번': range(1, len(standard_headers) + 1),
            '표준 순서': standard_headers
        })
        df_standard.to_excel(writer, sheet_name='표준 순서 정의', index=False)
        
        # 시트 6: 차이점 분석
        analysis_data = []
        
        # 각 스테이지별 통계
        analysis_data.append({'분석 항목': 'Stage 1 헤더 수', '값': len(stage1_headers)})
        analysis_data.append({'분석 항목': 'Stage 2 헤더 수', '값': len(stage2_headers)})
        analysis_data.append({'분석 항목': 'Stage 3 헤더 수', '값': len(stage3_headers)})
        analysis_data.append({'분석 항목': '표준 헤더 수', '값': len(standard_headers)})
        
        # 차이점 분석
        stage1_only = set(stage1_headers) - set(standard_headers)
        stage2_only = set(stage2_headers) - set(standard_headers)
        stage3_only = set(stage3_headers) - set(standard_headers)
        
        analysis_data.append({'분석 항목': 'Stage 1 추가 헤더', '값': ', '.join(stage1_only) if stage1_only else '없음'})
        analysis_data.append({'분석 항목': 'Stage 2 추가 헤더', '값': ', '.join(stage2_only) if stage2_only else '없음'})
        analysis_data.append({'분석 항목': 'Stage 3 추가 헤더', '값': ', '.join(stage3_only) if stage3_only else '없음'})
        
        df_analysis = pd.DataFrame(analysis_data)
        df_analysis.to_excel(writer, sheet_name='차이점 분석', index=False)
    
    print(f"✅ 헤더 순서 비교 보고서 생성 완료: {output_file}")
    print(f"📊 총 {max_length}개 헤더 비교")
    print(f"📋 6개 시트로 구성된 상세 보고서")
    
    return output_file

if __name__ == "__main__":
    create_comparison_report()

