#!/usr/bin/env python3
"""DEC 2024 데이터 최종 확인"""

import pandas as pd

df = pd.read_excel('out/masterdata_all_months_20251016_133706.xlsx')
dec_data = df[df['Source_File'] == 'DEC 2024']

print('DEC 2024 데이터:')
print(f'총 행 수: {len(dec_data)}')
print(f'RATE SOURCE 데이터 있음: {dec_data["RATE SOURCE"].notna().sum()} / {len(dec_data)} ({dec_data["RATE SOURCE"].notna().sum()/len(dec_data)*100:.1f}%)')

print(f'\n샘플:')
print(dec_data[['Source_File', 'DESCRIPTION', 'RATE SOURCE', 'RATE']].head(5).to_string(index=False))

print(f'\nRATE SOURCE 값 분포:')
print(dec_data['RATE SOURCE'].value_counts(dropna=False))

