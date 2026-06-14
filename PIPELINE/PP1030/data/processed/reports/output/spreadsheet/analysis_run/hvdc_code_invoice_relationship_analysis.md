# HVDC CODE invoice relationship analysis

- Workbook: `C:\HVDC_WORK\PIPELINE\PP1030\output\spreadsheet\HVDC_WAREHOUSE_INVOICE_all_billing_months_formatted.xlsx`
- Sheet: `invoice_all_months`
- Data rows: 608
- Columns: 32

## Header groups
- Code group: HVDC CODE, HVDC CODE 1, HVDC CODE 2, HVDC CODE 3, HVDC CODE 4
- Month/date group: Operation Month, Billing month, Start, Finish
- Quantity/measure group: 20DC, 20FR, 40DC, 40FR, CNTR Unstuffing Q'TY, CNTR Stuffing Q'TY, pkg, Weight (kg), CBM, Handling In freight ton, Handling out Freight Ton, Sqm
- Charge group: Amount, Handling In, Handling out, Unstuffing, Stuffing, folk lift, crane, TOTAL

## Code classification
- hvdc_adopt: 400 rows, TOTAL=4,305,517.13
- service_or_location_label: 68 rows, TOTAL=7,222,504.32
- hvdc_dsv: 62 rows, TOTAL=219,278.45
- non_hvdc_text: 39 rows, TOTAL=2,567,312.72
- hvdc_other: 30 rows, TOTAL=191,646.75
- blank_after_na_removal: 9 rows, TOTAL=69,671.85

## Split patterns
- ('Y', 'Y', 'Y', 'Y', 'Y'): 390
- ('Y', '-', '-', '-', '-'): 143
- ('Y', 'Y', '-', '-', '-'): 53
- ('Y', 'Y', 'Y', '-', '-'): 13
- ('-', '-', '-', '-', '-'): 9

- Split mismatches: 132
- Valid HVDC-like rows with blank split columns: 104

### Blank split sample
- Row 467: HVDC-DSV-HE-MOSB-263 -> expected ['HVDC', 'DSV', 'HE', 'MOSB-263'], billing=2025-11, TOTAL=7,982.50
- Row 468: HVDC-ADOPT-HE-0300 -> expected ['HVDC', 'ADOPT', 'HE', 300], billing=2025-11, TOTAL=14.71
- Row 469: HVDC-DSV-MOSB-260 -> expected ['HVDC', 'DSV', 'MOSB', 260], billing=2025-11, TOTAL=213.34
- Row 471: HVDC-DSV-MOSB-264 -> expected ['HVDC', 'DSV', 'MOSB', 264], billing=2025-11, TOTAL=6,700.00
- Row 472: HVDC-DSV-MOSB-264 -> expected ['HVDC', 'DSV', 'MOSB', 264], billing=2025-11, TOTAL=4,700.00
- Row 473: HVDC-DSV-HE-MOSB-267 -> expected ['HVDC', 'DSV', 'HE', 'MOSB-267'], billing=2025-11, TOTAL=2,005.00
- Row 474: HVDC-ADOPT-SCT-0128 -> expected ['HVDC', 'ADOPT', 'SCT', 128], billing=2025-11, TOTAL=9,121.50
- Row 475: HVDC-DSV-HE-MOSB-268 -> expected ['HVDC', 'DSV', 'HE', 'MOSB-268'], billing=2025-11, TOTAL=6,828.00
- Row 476: HVDC-DSV-HE-MOSB-268 -> expected ['HVDC', 'DSV', 'HE', 'MOSB-268'], billing=2025-11, TOTAL=7,980.00
- Row 478: HVDC-DSV-HE-MOSB-269 -> expected ['HVDC', 'DSV', 'HE', 'MOSB-269'], billing=2025-11, TOTAL=8,612.20

## Vendor/code family totals
- HE: 195 rows, TOTAL=2,608,138.26
- SCT: 130 rows, TOTAL=987,843.41
- SIM: 103 rows, TOTAL=837,682.73
- ALS: 23 rows, TOTAL=171,940.21
- MOSB: 11 rows, TOTAL=29,665.08
- ADOPT_PARSE_FAIL: 9 rows, TOTAL=13,563.59
- SEI: 7 rows, TOTAL=33,448.41
- SAS: 4 rows, TOTAL=8,084.33
- SKM: 2 rows, TOTAL=921.00
- PPL: 1 rows, TOTAL=2,570.15
- NIE: 1 rows, TOTAL=4,111.60
- ALM: 1 rows, TOTAL=9,389.93
- ELS: 1 rows, TOTAL=128.00
- HE/SCHENCKER: 1 rows, TOTAL=230.50
- CAM: 1 rows, TOTAL=42.26
- RE: 1 rows, TOTAL=7,725.00
- SCT/SIM: 1 rows, TOTAL=957.87

## Billing month totals
- 2024-01: 9 rows, TOTAL=154,706.13, classes={'hvdc_adopt': 9}
- 2024-02: 17 rows, TOTAL=426,744.51, classes={'hvdc_adopt': 17}
- 2024-03: 27 rows, TOTAL=429,265.72, classes={'hvdc_adopt': 27}
- 2024-04: 16 rows, TOTAL=374,939.24, classes={'hvdc_adopt': 11, 'blank_after_na_removal': 5}
- 2024-05: 11 rows, TOTAL=267,762.66, classes={'hvdc_adopt': 7, 'blank_after_na_removal': 4}
- 2024-06: 14 rows, TOTAL=658,275.22, classes={'hvdc_adopt': 8, 'service_or_location_label': 6}
- 2024-07: 32 rows, TOTAL=836,914.60, classes={'hvdc_adopt': 28, 'service_or_location_label': 4}
- 2024-08: 37 rows, TOTAL=988,859.14, classes={'hvdc_adopt': 33, 'service_or_location_label': 4}
- 2024-09: 23 rows, TOTAL=865,693.30, classes={'hvdc_adopt': 15, 'hvdc_dsv': 3, 'service_or_location_label': 5}
- 2024-10: 21 rows, TOTAL=791,792.15, classes={'hvdc_adopt': 15, 'service_or_location_label': 6}
- 2024-11: 41 rows, TOTAL=915,417.03, classes={'hvdc_adopt': 32, 'hvdc_dsv': 1, 'service_or_location_label': 8}
- 2024-12: 30 rows, TOTAL=905,842.81, classes={'hvdc_adopt': 19, 'service_or_location_label': 9, 'hvdc_other': 2}
- 2025-01: 47 rows, TOTAL=1,022,125.80, classes={'hvdc_adopt': 41, 'service_or_location_label': 5, 'hvdc_dsv': 1}
- 2025-02: 50 rows, TOTAL=971,324.17, classes={'hvdc_adopt': 44, 'service_or_location_label': 5, 'hvdc_other': 1}
- 2025-03: 35 rows, TOTAL=883,890.99, classes={'hvdc_adopt': 24, 'service_or_location_label': 11}
- 2025-04: 55 rows, TOTAL=1,046,083.42, classes={'hvdc_adopt': 48, 'service_or_location_label': 5, 'hvdc_dsv': 2}
- 2025-11: 56 rows, TOTAL=998,951.42, classes={'hvdc_dsv': 25, 'hvdc_adopt': 10, 'non_hvdc_text': 14, 'hvdc_other': 7}
- 2025-12: 28 rows, TOTAL=808,189.88, classes={'hvdc_dsv': 10, 'non_hvdc_text': 10, 'hvdc_other': 3, 'hvdc_adopt': 5}
- 2026-01: 29 rows, TOTAL=634,390.20, classes={'hvdc_adopt': 5, 'hvdc_other': 9, 'hvdc_dsv': 8, 'non_hvdc_text': 7}
- 2026-02: 30 rows, TOTAL=594,762.82, classes={'hvdc_dsv': 12, 'hvdc_adopt': 2, 'hvdc_other': 8, 'non_hvdc_text': 8}

## Category totals
- DSV Outdoor: 312 rows, TOTAL=5,296,042.57, classes={'hvdc_adopt': 278, 'service_or_location_label': 28, 'hvdc_dsv': 5, 'hvdc_other': 1}
- DSV Indoor: 127 rows, TOTAL=5,973,382.73, classes={'hvdc_adopt': 94, 'service_or_location_label': 29, 'hvdc_dsv': 2, 'hvdc_other': 2}
- Outdoor: 85 rows, TOTAL=1,492,744.03, classes={'hvdc_dsv': 31, 'hvdc_adopt': 19, 'non_hvdc_text': 16, 'hvdc_other': 19}
- Warehouse: 58 rows, TOTAL=1,543,550.29, classes={'hvdc_dsv': 24, 'hvdc_other': 8, 'non_hvdc_text': 23, 'hvdc_adopt': 3}
- DSV MZP: 9 rows, TOTAL=69,671.85, classes={'blank_after_na_removal': 9}
- DSV Al Markaz: 6 rows, TOTAL=8,188.00, classes={'hvdc_adopt': 4, 'service_or_location_label': 2}
- AAA  Storage: 5 rows, TOTAL=54,701.14, classes={'service_or_location_label': 5}
- (blank): 4 rows, TOTAL=1,264.10, classes={'hvdc_adopt': 2, 'service_or_location_label': 2}
- Shifting: 2 rows, TOTAL=136,386.50, classes={'service_or_location_label': 2}

## Service/location labels
- DSV Open Yard | DSV Outdoor: 11
- M44 Warehouse | DSV Indoor: 11
- Al Markaz Warehouse | DSV Al Markaz: 11
- Mina Zayed Open Yard | DSV MZP: 10
- Shifting from M44 to Al Markaz | Shifting from M44 to Al Markaz: 2
- HE-0192/195/189/193/197/191 | HE: 2
- Additional Manpower - M44 WH | Additional Manpower: 2
- Additional Manpower - Al Markaz WH | Additional Manpower: 2
- Additional Manpower - Open Yard | Additional Manpower: 2
- Port charge Man Masket to Gate pass | Port charge Man Masket to Gate pass: 1
- 10 Ton Forklift (M44 Warehouse) | 10 Ton Forklift (M44 Warehouse): 1
- Valve Capacitor Replacement | Valve Capacitor Replacement: 1
- HVDCADOPT-SIM-0005-2 | HVDC: 1
- EQ-211-HE_LOCAL-JAN24 - LV Panel - DAS Pole | EQ: 1
- Warehouse Outbound | DSV Outdoor: 1
- Daily gate pass for operators | Daily gate pass for operators: 1
- Daily gate pass for trailers | Daily gate pass for trailers: 1
- Mina Zayed open yard | DSV MZP: 1
- Dg Warehouse- November 2024 | AAA  Storage: 1
- Dg Warehouse- December 2024 | AAA  Storage: 1
- Dg Warehouse- January 2025 | AAA  Storage: 1
- Dg Warehouse- February 2025 | AAA  Storage: 1
- Dg Warehouse- March 2025 | AAA  Storage: 1
- Outbound to Al Masaood #1 | Outbound to Al Masaood #1: 1

## Related numeric columns
- TOTAL: nonzero rows=602, sum=14,575,931.21
- pkg: nonzero rows=498, sum=9,827.00
- CBM: nonzero rows=497, sum=67,452.73
- Weight (kg): nonzero rows=439, sum=14,971,654.65
- Handling In: nonzero rows=305, sum=999,136.24
- Handling In freight ton: nonzero rows=300, sum=45,010.54
- Handling out Freight Ton: nonzero rows=298, sum=40,939.85
- Handling out: nonzero rows=288, sum=965,455.72
- CNTR Unstuffing Q'TY: nonzero rows=206, sum=919.00
- Unstuffing: nonzero rows=158, sum=1,706,000.00
- 40DC: nonzero rows=138, sum=812.00
- Amount: nonzero rows=95, sum=9,879,451.04
- Sqm: nonzero rows=90, sum=829,078.52
- folk lift: nonzero rows=66, sum=379,000.00
- 40FR: nonzero rows=51, sum=51.00
- crane: nonzero rows=45, sum=556,001.33
- 20DC: nonzero rows=40, sum=57.00
- 20FR: nonzero rows=10, sum=31.00
- Stuffing: nonzero rows=5, sum=81,866.50
- CNTR Stuffing Q'TY: nonzero rows=4, sum=75.00

## Charge integrity
- Rows where TOTAL differs from charge component sum by more than 0.005: 12
- Row 38: TOTAL=6,788.35, components=6,788.36, diff=-0.01, code=HVDC-ADOPT-SIM-0001
- Row 118: TOTAL=33,605.55, components=33,605.56, diff=-0.01, code=HVDC-ADOPT-SCT-0005
- Row 119: TOTAL=67,571.25, components=67,571.24, diff=0.01, code=HVDC-ADOPT-HE-0162
- Row 121: TOTAL=5,373.65, components=5,373.66, diff=-0.01, code=HVDC-ADOPT-SCT-0004
- Row 125: TOTAL=5,438.95, components=5,438.96, diff=-0.01, code=HVDC-ADOPT-SCT-0008
- Row 247: TOTAL=3,500.00, components=0.00, diff=3,500.00, code=Additional Manpower - M44 WH
- Row 248: TOTAL=3,500.00, components=0.00, diff=3,500.00, code=Additional Manpower - Al Markaz WH
- Row 249: TOTAL=3,500.00, components=0.00, diff=3,500.00, code=Additional Manpower - Open Yard
- Row 361: TOTAL=3,956.75, components=3,956.76, diff=-0.01, code=HVDC-ADOPT-SCT-0029
- Row 431: TOTAL=3,256.70, components=3,256.69, diff=0.01, code=HVDC-ADOPT-HE-0309-2,0310-2,0311-2,0301-2 

## Remaining date text issues
- Row 516: Finish=2025-11-31, code=DSV OPEN YARD FOR THE NOV-25, billing=2025-11, TOTAL=218,700.00
- Row 517: Finish=2025-11-31, code=M44 WAREHOUSE FOR THE NOV-25, billing=2025-11, TOTAL=254,000.00
- Row 518: Finish=2025-11-31, code=AL MARKAZ WAREHOUSE FOR THE NOV-25 (Minimum), billing=2025-11, TOTAL=135,000.00
- Row 519: Finish=2025-11-31, code=MINA ZAYED OPEN YARD FOR THE NOV-25, billing=2025-11, TOTAL=33,000.00