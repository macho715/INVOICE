#!/usr/bin/env python3
"""
OFCO Header Core Module
========================

헤더(컬럼) 순서만 관리하는 코어 모듈
- OFCO INVOICE.xlsx의 헤더 순서를 기준으로 컬럼 정렬
- 각 Phase별 추가 컬럼은 마지막에 삽입

Author: MACHO-GPT v3.4-mini
Date: 2025-11-04
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from collections import OrderedDict


class HeaderCore:
    """헤더 순서 관리 코어 클래스"""

    # 컬럼명 매핑 규칙 (원본 DataFrame 컬럼명 → OFCO INVOICE.xlsx 컬럼명)
    COLUMN_MAPPING = {
        "invoice_no": "INVOICE NUMBER",
        "invoice_date": "INVOICE DATE",
        "voyage_no": "Voyage No",
        "description": "SUBJECT",
        "line_no": "NO",
        # 추가 매핑은 필요 시 확장
    }

    def __init__(self, reference_file: Optional[str] = None):
        """
        HeaderCore 초기화

        Args:
            reference_file: OFCO INVOICE.xlsx 파일 경로 (기본값: 현재 디렉토리의 "OFCO INVOICE.xlsx")
        """
        if reference_file is None:
            reference_file = "OFCO INVOICE.xlsx"
        
        self.reference_file = Path(reference_file)
        self.base_headers: List[str] = []
        self.phase1_headers: List[str] = []
        self.phase2_headers: List[str] = []
        self.phase3_headers: List[str] = []
        self.extra_headers: List[str] = []  # 추가 컬럼 (기준 파일에 없는 컬럼)
        
        # 기준 헤더 로드
        self.load_base_headers()

    def load_base_headers(self) -> List[str]:
        """
        OFCO INVOICE.xlsx에서 기준 헤더 순서 로드

        Returns:
            기준 헤더 순서 리스트
        """
        try:
            if not self.reference_file.exists():
                raise FileNotFoundError(
                    f"기준 파일을 찾을 수 없습니다: {self.reference_file}"
                )
            
            # 헤더만 읽기 (nrows=0)
            df = pd.read_excel(self.reference_file, nrows=0)
            self.base_headers = list(df.columns)
            
            print(f"[HeaderCore] 기준 헤더 로드 완료: {len(self.base_headers)}개 컬럼")
            return self.base_headers
        
        except Exception as e:
            print(f"[HeaderCore] WARNING: 기준 헤더 로드 실패: {e}")
            print(f"[HeaderCore] 빈 헤더 리스트로 초기화")
            self.base_headers = []
            return []

    def add_phase_headers(self, phase: int, headers: List[str]) -> None:
        """
        Phase별 추가 헤더 등록

        Args:
            phase: Phase 번호 (1, 2, 3)
            headers: 추가할 헤더 리스트
        """
        if phase == 1:
            self.phase1_headers = headers
        elif phase == 2:
            self.phase2_headers = headers
        elif phase == 3:
            self.phase3_headers = headers
        else:
            raise ValueError(f"잘못된 Phase 번호: {phase} (1, 2, 3만 허용)")

    def get_ordered_headers(self, phase: Optional[int] = None) -> List[str]:
        """
        정렬된 헤더 리스트 반환

        Args:
            phase: Phase 번호 (None이면 전체)

        Returns:
            정렬된 헤더 리스트
            - 기준 헤더 순서 (OFCO INVOICE.xlsx 순서)
            - Phase별 추가 헤더 (마지막에 추가)
            - 기타 추가 헤더 (마지막에 추가)
        """
        ordered = list(self.base_headers)  # 기준 헤더 복사
        
        # Phase별 추가 헤더
        if phase is None or phase >= 1:
            for h in self.phase1_headers:
                if h not in ordered:
                    ordered.append(h)
        
        if phase is None or phase >= 2:
            for h in self.phase2_headers:
                if h not in ordered:
                    ordered.append(h)
        
        if phase is None or phase >= 3:
            for h in self.phase3_headers:
                if h not in ordered:
                    ordered.append(h)
        
        # 기타 추가 헤더
        for h in self.extra_headers:
            if h not in ordered:
                ordered.append(h)
        
        return ordered

    def map_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame 컬럼명을 OFCO INVOICE.xlsx 기준 컬럼명으로 매핑

        Args:
            df: 매핑할 DataFrame

        Returns:
            컬럼명이 매핑된 DataFrame
        """
        df_mapped = df.copy()
        rename_dict = {}
        
        for old_name, new_name in self.COLUMN_MAPPING.items():
            if old_name in df_mapped.columns and new_name not in df_mapped.columns:
                rename_dict[old_name] = new_name
        
        if rename_dict:
            df_mapped = df_mapped.rename(columns=rename_dict)
        
        return df_mapped

    def reorder_dataframe(
        self, 
        df: pd.DataFrame, 
        phase: Optional[int] = None,
        fill_missing: bool = True,
        map_columns: bool = True
    ) -> pd.DataFrame:
        """
        DataFrame 컬럼을 기준 헤더 순서로 재정렬

        Args:
            df: 정렬할 DataFrame
            phase: Phase 번호 (None이면 전체)
            fill_missing: True이면 없는 컬럼을 None으로 채워서 추가
            map_columns: True이면 컬럼명을 기준 컬럼명으로 매핑

        Returns:
            정렬된 DataFrame
        """
        # Step 8: 컬럼명 매핑 (필요 시)
        if map_columns:
            df = self.map_column_names(df)
        
        ordered_headers = self.get_ordered_headers(phase)
        
        # DataFrame에 있는 실제 컬럼
        df_columns = list(df.columns)
        
        # 최종 컬럼 순서 결정: 기준 순서대로, 없는 컬럼은 None으로 채워서 추가
        final_columns = []
        
        # 1. 기준 순서에 있는 컬럼 (DataFrame에 있든 없든 모두 포함)
        for col in ordered_headers:
            final_columns.append(col)
        
        # 2. DataFrame에 있지만 기준 순서에 없는 컬럼 (마지막에 추가)
        for col in df_columns:
            if col not in final_columns:
                final_columns.append(col)
        
        # 3. DataFrame 재구성
        # DataFrame에 있는 컬럼만 먼저 추출
        existing_cols = [col for col in final_columns if col in df_columns]
        result_df = df[existing_cols].copy()
        
        # fill_missing이 False인 경우, DataFrame에 있는 컬럼만 포함
        if not fill_missing:
            return result_df[existing_cols]
        
        # 없는 컬럼 추가 (성능 개선: 한 번에 추가)
        missing_cols = [col for col in ordered_headers if col not in df_columns]
        if missing_cols:
            # 기준 순서에 맞게 컬럼 삽입
            # DataFrame.insert()는 성능이 느리므로, concat으로 한 번에 처리
            missing_data = {col: None for col in missing_cols}
            
            # 기준 순서에 맞게 컬럼 삽입하기 위해 reindex 사용
            all_cols = []
            for col in final_columns:
                if col in df_columns:
                    all_cols.append(col)
                elif col in missing_cols:
                    all_cols.append(col)
            
            # reindex로 기준 순서에 맞게 컬럼 추가
            result_df = result_df.reindex(columns=all_cols)
        
        # 최종 컬럼 순서 재정렬
        result_df = result_df[final_columns]
        
        return result_df

    def add_extra_headers(self, headers: List[str]) -> None:
        """
        추가 헤더 등록 (기준 파일에 없는 컬럼)

        Args:
            headers: 추가할 헤더 리스트
        """
        for h in headers:
            if h not in self.extra_headers:
                self.extra_headers.append(h)

    def get_base_headers(self) -> List[str]:
        """기준 헤더 리스트 반환"""
        return list(self.base_headers)

    def get_phase_headers(self, phase: int) -> List[str]:
        """Phase별 추가 헤더 리스트 반환"""
        if phase == 1:
            return list(self.phase1_headers)
        elif phase == 2:
            return list(self.phase2_headers)
        elif phase == 3:
            return list(self.phase3_headers)
        else:
            raise ValueError(f"잘못된 Phase 번호: {phase}")

    def get_header_count(self) -> Dict[str, int]:
        """헤더 개수 통계 반환"""
        return {
            "base": len(self.base_headers),
            "phase1": len(self.phase1_headers),
            "phase2": len(self.phase2_headers),
            "phase3": len(self.phase3_headers),
            "extra": len(self.extra_headers),
            "total": len(self.get_ordered_headers())
        }


# 전역 인스턴스 (싱글톤 패턴)
_global_header_core: Optional[HeaderCore] = None


def get_header_core(reference_file: Optional[str] = None) -> HeaderCore:
    """
    전역 HeaderCore 인스턴스 반환 (싱글톤)

    Args:
        reference_file: 기준 파일 경로 (첫 호출 시에만 적용)

    Returns:
        HeaderCore 인스턴스
    """
    global _global_header_core
    
    if _global_header_core is None:
        _global_header_core = HeaderCore(reference_file)
    
    return _global_header_core


def reset_header_core(reference_file: Optional[str] = None) -> HeaderCore:
    """
    전역 HeaderCore 인스턴스 리셋

    Args:
        reference_file: 기준 파일 경로

    Returns:
        새 HeaderCore 인스턴스
    """
    global _global_header_core
    _global_header_core = HeaderCore(reference_file)
    return _global_header_core


if __name__ == "__main__":
    # 테스트
    print("=" * 80)
    print("[HeaderCore] 테스트")
    print("=" * 80)
    
    try:
        core = HeaderCore()
        print(f"\n기준 헤더 개수: {len(core.base_headers)}")
        print(f"처음 10개 헤더:")
        for i, h in enumerate(core.base_headers[:10], 1):
            print(f"  {i:2d}. {h}")
        
        print(f"\n마지막 10개 헤더:")
        for i, h in enumerate(core.base_headers[-10:], 1):
            print(f"  {len(core.base_headers) - 10 + i:2d}. {h}")
        
        # 통계
        stats = core.get_header_count()
        print(f"\n헤더 통계:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n[OK] HeaderCore 테스트 완료")
        
    except Exception as e:
        print(f"\n[ERROR] HeaderCore 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

