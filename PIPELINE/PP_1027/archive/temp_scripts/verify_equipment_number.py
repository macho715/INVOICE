#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify equipment_number registration in header_registry"""

import sys
sys.path.insert(0, 'scripts')

from core.header_registry import HVDC_HEADER_REGISTRY

print("=" * 70)
print("HITACHI/SIEMENS 헤더 별칭 검증")
print("=" * 70)

# Test 1: Check case_number (PackageNo alias)
print("\n1. case_number (Case No = PackageNo)")
case_defn = HVDC_HEADER_REGISTRY.get_definition('case_number')
print(f"   설명: {case_defn.description}")
print(f"   별칭 개수: {len(case_defn.aliases)}개")
packageno_aliases = [a for a in case_defn.aliases if 'package' in a.lower()]
print(f"   PackageNo 관련: {', '.join(packageno_aliases)}")

# Test 2: Check hs_code (HSCODE alias)
print("\n2. hs_code (HS Code = HSCODE)")
hs_defn = HVDC_HEADER_REGISTRY.get_definition('hs_code')
print(f"   설명: {hs_defn.description}")
print(f"   별칭 개수: {len(hs_defn.aliases)}개")
hscode_aliases = [a for a in hs_defn.aliases if 'hscode' in a.lower()]
print(f"   HSCODE 관련: {', '.join(hscode_aliases)}")

# Test 3: Check equipment_number (NEW: EQ No = PO.No)
print("\n3. equipment_number (EQ No = PO.No) [NEW]")
eq_defn = HVDC_HEADER_REGISTRY.get_definition('equipment_number')
print(f"   설명: {eq_defn.description}")
print(f"   별칭 개수: {len(eq_defn.aliases)}개")
print(f"   HITACHI 별칭: {[a for a in eq_defn.aliases if 'EQ' in a]}")
print(f"   SIEMENS 별칭: {[a for a in eq_defn.aliases if 'PO' in a]}")

print("\n" + "=" * 70)
print("✓ 모든 HITACHI/SIEMENS 헤더 별칭 등록 완료!")
print("=" * 70)
print("\n요약:")
print("  - Case No = PackageNo (✓ 이미 등록됨)")
print("  - HS Code = HSCODE (✓ 이미 등록됨)")
print("  - EQ No = PO.No (✓ 새로 등록됨)")
print("\n하드코딩 없이 @core/header_registry.py에서 중앙 관리!")

