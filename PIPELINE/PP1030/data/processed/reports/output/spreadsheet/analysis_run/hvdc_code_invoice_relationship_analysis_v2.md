# HVDC CODE invoice relationship analysis v2

- Workbook: `C:\HVDC_WORK\PIPELINE\PP1030\output\spreadsheet\HVDC_WAREHOUSE_INVOICE_all_billing_months_formatted.xlsx`
- Sheet: `invoice_all_months`
- Data rows: 608
- Inferred split rule: For HVDC-like values, populate HVDC CODE 1..4 from the first four hyphen-separated tokens. If token 4 is purely numeric, Excel-style numeric value is acceptable. Do not overwrite service/location label rows or blank-after-N/A rows.

## Classification
- hvdc_adopt: 400 rows, TOTAL=4,305,517.13
- service_or_location_label: 68 rows, TOTAL=7,222,504.32
- hvdc_dsv: 62 rows, TOTAL=219,278.45
- non_hvdc_text: 39 rows, TOTAL=2,567,312.72
- hvdc_other: 30 rows, TOTAL=191,646.75
- blank_after_na_removal: 9 rows, TOTAL=69,671.85

## Source range relationship
- base_rows_2_466: rows=465, TOTAL=11,539,636.89, classes={'hvdc_adopt': 378, 'blank_after_na_removal': 9, 'service_or_location_label': 68, 'hvdc_dsv': 7, 'hvdc_other': 3}
- appended_rows_467_609: rows=143, TOTAL=3,036,294.32, classes={'hvdc_dsv': 55, 'hvdc_adopt': 22, 'non_hvdc_text': 39, 'hvdc_other': 27}

## Split state
- ('Y', 'Y', 'Y', 'Y', 'Y'): 390
- ('Y', '-', '-', '-', '-'): 143
- ('Y', 'Y', '-', '-', '-'): 53
- ('Y', 'Y', 'Y', '-', '-'): 13
- ('-', '-', '-', '-', '-'): 9
- Split mismatches under first-4-token rule: 110
- HVDC-like rows with blank split columns: 104
  - Row 467: HVDC-DSV-HE-MOSB-263 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=7,982.50
  - Row 468: HVDC-ADOPT-HE-0300 -> ['HVDC', 'ADOPT', 'HE', 300] | month=2025-11 category=Outdoor TOTAL=14.71
  - Row 469: HVDC-DSV-MOSB-260 -> ['HVDC', 'DSV', 'MOSB', 260] | month=2025-11 category=Outdoor TOTAL=213.34
  - Row 471: HVDC-DSV-MOSB-264 -> ['HVDC', 'DSV', 'MOSB', 264] | month=2025-11 category=Outdoor TOTAL=6,700.00
  - Row 472: HVDC-DSV-MOSB-264 -> ['HVDC', 'DSV', 'MOSB', 264] | month=2025-11 category=Outdoor TOTAL=4,700.00
  - Row 473: HVDC-DSV-HE-MOSB-267 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=2,005.00
  - Row 474: HVDC-ADOPT-SCT-0128 -> ['HVDC', 'ADOPT', 'SCT', 128] | month=2025-11 category=Outdoor TOTAL=9,121.50
  - Row 475: HVDC-DSV-HE-MOSB-268 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=6,828.00
  - Row 476: HVDC-DSV-HE-MOSB-268 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=7,980.00
  - Row 478: HVDC-DSV-HE-MOSB-269 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=8,612.20
  - Row 479: HVDC-DSV-HE-MOSB-269 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=6,612.20
  - Row 480: HVDC-DSV-HE-MOSB-271 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=867.50
  - Row 481: HVDC-ADOPT-SCT-0086 (Outbound to SHU) -> ['HVDC', 'ADOPT', 'SCT', '0086 (Outbound to SHU)'] | month=2025-11 category=Outdoor TOTAL=78.03
  - Row 482: HVDC-ADOPT-SCT-0086 (Outbound to MIR) -> ['HVDC', 'ADOPT', 'SCT', '0086 (Outbound to MIR)'] | month=2025-11 category=Outdoor TOTAL=26.01
  - Row 483: HVDC-ADOPT-SCT-0132 -> ['HVDC', 'ADOPT', 'SCT', 132] | month=2025-11 category=Outdoor TOTAL=2,285.00
  - Row 484: HVDC-DSV-HE-MOSB-276 -> ['HVDC', 'DSV', 'HE', 'MOSB'] | month=2025-11 category=Outdoor TOTAL=82.50
  - Row 485: HVDC-ADOPT-SCT-0135 -> ['HVDC', 'ADOPT', 'SCT', 135] | month=2025-11 category=Outdoor TOTAL=4,500.00
  - Row 486: HVDC-AGI-ALS-338 -> ['HVDC', 'AGI', 'ALS', 338] | month=2025-11 category=Outdoor TOTAL=6,238.11
  - Row 487: HVDC-AGI-ALS-338 -> ['HVDC', 'AGI', 'ALS', 338] | month=2025-11 category=Outdoor TOTAL=4,238.11
  - Row 488: HVDC-AGI-ALS-338 -> ['HVDC', 'AGI', 'ALS', 338] | month=2025-11 category=Outdoor TOTAL=4,238.11

## Billing months
- 2024-01: rows=9, TOTAL=154,706.13, classes={'hvdc_adopt': 9}
- 2024-02: rows=17, TOTAL=426,744.51, classes={'hvdc_adopt': 17}
- 2024-03: rows=27, TOTAL=429,265.72, classes={'hvdc_adopt': 27}
- 2024-04: rows=16, TOTAL=374,939.24, classes={'hvdc_adopt': 11, 'blank_after_na_removal': 5}
- 2024-05: rows=11, TOTAL=267,762.66, classes={'hvdc_adopt': 7, 'blank_after_na_removal': 4}
- 2024-06: rows=14, TOTAL=658,275.22, classes={'hvdc_adopt': 8, 'service_or_location_label': 6}
- 2024-07: rows=32, TOTAL=836,914.60, classes={'hvdc_adopt': 28, 'service_or_location_label': 4}
- 2024-08: rows=37, TOTAL=988,859.14, classes={'hvdc_adopt': 33, 'service_or_location_label': 4}
- 2024-09: rows=23, TOTAL=865,693.30, classes={'hvdc_adopt': 15, 'hvdc_dsv': 3, 'service_or_location_label': 5}
- 2024-10: rows=21, TOTAL=791,792.15, classes={'hvdc_adopt': 15, 'service_or_location_label': 6}
- 2024-11: rows=41, TOTAL=915,417.03, classes={'hvdc_adopt': 32, 'hvdc_dsv': 1, 'service_or_location_label': 8}
- 2024-12: rows=30, TOTAL=905,842.81, classes={'hvdc_adopt': 19, 'service_or_location_label': 9, 'hvdc_other': 2}
- 2025-01: rows=47, TOTAL=1,022,125.80, classes={'hvdc_adopt': 41, 'service_or_location_label': 5, 'hvdc_dsv': 1}
- 2025-02: rows=50, TOTAL=971,324.17, classes={'hvdc_adopt': 44, 'service_or_location_label': 5, 'hvdc_other': 1}
- 2025-03: rows=35, TOTAL=883,890.99, classes={'hvdc_adopt': 24, 'service_or_location_label': 11}
- 2025-04: rows=55, TOTAL=1,046,083.42, classes={'hvdc_adopt': 48, 'service_or_location_label': 5, 'hvdc_dsv': 2}
- 2025-11: rows=56, TOTAL=998,951.42, classes={'hvdc_dsv': 25, 'hvdc_adopt': 10, 'non_hvdc_text': 14, 'hvdc_other': 7}
- 2025-12: rows=28, TOTAL=808,189.88, classes={'hvdc_dsv': 10, 'non_hvdc_text': 10, 'hvdc_other': 3, 'hvdc_adopt': 5}
- 2026-01: rows=29, TOTAL=634,390.20, classes={'hvdc_adopt': 5, 'hvdc_other': 9, 'hvdc_dsv': 8, 'non_hvdc_text': 7}
- 2026-02: rows=30, TOTAL=594,762.82, classes={'hvdc_dsv': 12, 'hvdc_adopt': 2, 'hvdc_other': 8, 'non_hvdc_text': 8}

## Categories
- DSV Outdoor: rows=312, TOTAL=5,296,042.57, classes={'hvdc_adopt': 278, 'service_or_location_label': 28, 'hvdc_dsv': 5, 'hvdc_other': 1}
- DSV Indoor: rows=127, TOTAL=5,973,382.73, classes={'hvdc_adopt': 94, 'service_or_location_label': 29, 'hvdc_dsv': 2, 'hvdc_other': 2}
- Outdoor: rows=85, TOTAL=1,492,744.03, classes={'hvdc_dsv': 31, 'hvdc_adopt': 19, 'non_hvdc_text': 16, 'hvdc_other': 19}
- Warehouse: rows=58, TOTAL=1,543,550.29, classes={'hvdc_dsv': 24, 'hvdc_other': 8, 'non_hvdc_text': 23, 'hvdc_adopt': 3}
- DSV MZP: rows=9, TOTAL=69,671.85, classes={'blank_after_na_removal': 9}
- DSV Al Markaz: rows=6, TOTAL=8,188.00, classes={'hvdc_adopt': 4, 'service_or_location_label': 2}
- AAA  Storage: rows=5, TOTAL=54,701.14, classes={'service_or_location_label': 5}
- (blank): rows=4, TOTAL=1,264.10, classes={'hvdc_adopt': 2, 'service_or_location_label': 2}
- Shifting: rows=2, TOTAL=136,386.50, classes={'service_or_location_label': 2}

## Service/location labels
- DSV Open Yard | CODE1=DSV Outdoor | Category=DSV Outdoor: 11
- M44 Warehouse | CODE1=DSV Indoor | Category=DSV Indoor: 11
- Al Markaz Warehouse | CODE1=DSV Al Markaz | Category=DSV Indoor: 11
- Mina Zayed Open Yard | CODE1=DSV MZP | Category=DSV Outdoor: 10
- Shifting from M44 to Al Markaz | CODE1=Shifting from M44 to Al Markaz | Category=Shifting: 2
- Additional Manpower - M44 WH | CODE1=Additional Manpower | Category=DSV Indoor: 2
- Additional Manpower - Al Markaz WH | CODE1=Additional Manpower | Category=DSV Al Markaz: 2
- Additional Manpower - Open Yard | CODE1=Additional Manpower | Category=DSV Outdoor: 2
- Port charge Man Masket to Gate pass | CODE1=Port charge Man Masket to Gate pass | Category=DSV Outdoor: 1
- HE-0192/195/189/193/197/191 | CODE1=HE | Category=DSV Indoor: 1
- HE-0192/195/189/193/197/191 | CODE1=HE | Category=DSV Outdoor: 1
- 10 Ton Forklift (M44 Warehouse) | CODE1=10 Ton Forklift (M44 Warehouse) | Category=DSV Indoor: 1
- Valve Capacitor Replacement | CODE1=Valve Capacitor Replacement | Category=DSV Indoor: 1
- HVDCADOPT-SIM-0005-2 | CODE1=HVDC | Category=DSV Outdoor: 1
- EQ-211-HE_LOCAL-JAN24 - LV Panel - DAS Pole | CODE1=EQ | Category=DSV Indoor: 1
- Warehouse Outbound | CODE1=DSV Outdoor | Category=DSV Indoor: 1
- Daily gate pass for operators | CODE1=Daily gate pass for operators | Category=(blank): 1
- Daily gate pass for trailers | CODE1=Daily gate pass for trailers | Category=(blank): 1
- Mina Zayed open yard | CODE1=DSV MZP | Category=DSV Outdoor: 1
- Dg Warehouse- November 2024 | CODE1=AAA  Storage | Category=AAA  Storage: 1
- Dg Warehouse- December 2024 | CODE1=AAA  Storage | Category=AAA  Storage: 1
- Dg Warehouse- January 2025 | CODE1=AAA  Storage | Category=AAA  Storage: 1
- Dg Warehouse- February 2025 | CODE1=AAA  Storage | Category=AAA  Storage: 1
- Dg Warehouse- March 2025 | CODE1=AAA  Storage | Category=AAA  Storage: 1
- Outbound to Al Masaood #1 | CODE1=Outbound to Al Masaood #1 | Category=DSV Outdoor: 1

## Non-HVDC text in HVDC CODE
- DG DUBAI THIRD PARTY WAREHOUSE (ACTUAL + 10%) for NOV-25 (HAULER) | Category=Warehouse: 2
- Lifting Test | Category=Outdoor: 1
- Lifting test | Category=Outdoor: 1
- RETURN / HE-0382 | Category=Warehouse: 1
- CASE NO. 208704 | Category=Warehouse: 1
- CASE NO. 365775 | Category=Warehouse: 1
- PRL-O-058-A DHL EQ101 | Category=Warehouse: 1
- ISO DG CONTAILER STORAGE/HANDLING CHARGE | Category=Outdoor: 1
- DSV OPEN YARD FOR THE NOV-25 | Category=Outdoor: 1
- M44 WAREHOUSE FOR THE NOV-25 | Category=Warehouse: 1
- AL MARKAZ WAREHOUSE FOR THE NOV-25 (Minimum) | Category=Warehouse: 1
- MINA ZAYED OPEN YARD FOR THE NOV-25 | Category=Outdoor: 1
- DSV DG WAREHOUSE FOR THE NOV-25 | Category=Warehouse: 1
- OOG WAREHOUSE (ACTUAL + 10%) FOR NOV-25 | Category=Warehouse: 1
- [HVDC-ADOPT-PPL-0021 & 0022 | Category=Outdoor: 1
- PORT CHARGE FOR CABLE DRUMS IN MINA ZAYED | Category=Outdoor: 1
- ISO DG CONTAILER STORAGE/HANDLING CHARGE DEC-25 | Category=Outdoor: 1
- DSV OPEN YARD FOR THE DEC-25 | Category=Outdoor: 1
- M44 WAREHOUSE FOR THE DEC-25 | Category=Warehouse: 1
- AL MARKAZ WAREHOUSE FOR THE DEC-25 (Minimum) | Category=Warehouse: 1
- MINA ZAYED OPEN YARD FOR THE DEC-25 | Category=Outdoor: 1
- DSV DG WAREHOUSE FOR THE DEC-25 | Category=Warehouse: 1
- OOG WAREHOUSE (ACTUAL + 10%) FOR DEC-25 | Category=Warehouse: 1
- ISO DG CONTAILER STORAGE/HANDLING CHARGE JAN-25 | Category=Outdoor: 1
- DSV OPEN YARD FOR THE JAN-26 | Category=Outdoor: 1
- M44 WAREHOUSE FOR THE JAN-26 | Category=Warehouse: 1
- MINA ZAYED OPEN YARD FOR THE JAN-26 | Category=Outdoor: 1
- DSV DG WAREHOUSE FOR THE JAN-26 | Category=Warehouse: 1
- OOG WAREHOUSE (ACTUAL + 10%) FOR JAN-26 | Category=Warehouse: 1
- DG DUBAI THIRD PARTY WAREHOUSE (ACTUAL + 10%) for JAN-26 (HAULER) | Category=Warehouse: 1
- ISO DG CONTAILER STORAGE/HANDLING CHARGE FEB-25 | Category=Outdoor: 1
- DSV OPEN YARD FOR THE FEB-26 | Category=Outdoor: 1
- M45 Temporary AC warehouse (as per offer) | Category=Warehouse: 1
- M44 WAREHOUSE FOR THE FEB-26 | Category=Warehouse: 1
- MINA ZAYED OPEN YARD FOR THE FEB-26 | Category=Outdoor: 1
- DSV DG WAREHOUSE FOR THE FEB-26 | Category=Warehouse: 1
- OOG WAREHOUSE (ACTUAL + 10%) FOR FEB-26 | Category=Warehouse: 1
- DG DUBAI THIRD PARTY WAREHOUSE (ACTUAL + 10%) for FEB-26 (HAULER) | Category=Warehouse: 1

## Charge component mismatches
- Count: 12
- Row 38: HVDC-ADOPT-SIM-0001 | 2024-03 | DSV Outdoor | TOTAL=6,788.35, component_sum=6,788.36, diff=-0.01
- Row 118: HVDC-ADOPT-SCT-0005 | 2024-07 | DSV Outdoor | TOTAL=33,605.55, component_sum=33,605.56, diff=-0.01
- Row 119: HVDC-ADOPT-HE-0162 | 2024-07 | DSV Indoor | TOTAL=67,571.25, component_sum=67,571.24, diff=0.01
- Row 121: HVDC-ADOPT-SCT-0004 | 2024-07 | DSV Outdoor | TOTAL=5,373.65, component_sum=5,373.66, diff=-0.01
- Row 125: HVDC-ADOPT-SCT-0008 | 2024-07 | DSV Outdoor | TOTAL=5,438.95, component_sum=5,438.96, diff=-0.01
- Row 247: Additional Manpower - M44 WH | 2024-11 | DSV Indoor | TOTAL=3,500.00, component_sum=0.00, diff=3,500.00
- Row 248: Additional Manpower - Al Markaz WH | 2024-11 | DSV Al Markaz | TOTAL=3,500.00, component_sum=0.00, diff=3,500.00
- Row 249: Additional Manpower - Open Yard | 2024-11 | DSV Outdoor | TOTAL=3,500.00, component_sum=0.00, diff=3,500.00
- Row 361: HVDC-ADOPT-SCT-0029 | 2025-02 | DSV Outdoor | TOTAL=3,956.75, component_sum=3,956.76, diff=-0.01
- Row 431: HVDC-ADOPT-HE-0309-2,0310-2,0311-2,0301-2  | 2025-04 | DSV Indoor | TOTAL=3,256.70, component_sum=3,256.69, diff=0.01
- Row 493: HVDC-DSV-HE-MOSB-283 (Warehouse) | 2025-11 | Warehouse | TOTAL=0.00, component_sum=1,125.68, diff=-1,125.68
- Row 497: HVDC-DSV-HE-MOSB-285(Warehouse) | 2025-11 | Warehouse | TOTAL=0.00, component_sum=353.90, diff=-353.90

## Invalid finish date text
- Row 516: Finish=2025-11-31 | DSV OPEN YARD FOR THE NOV-25 | TOTAL=218,700.00
- Row 517: Finish=2025-11-31 | M44 WAREHOUSE FOR THE NOV-25 | TOTAL=254,000.00
- Row 518: Finish=2025-11-31 | AL MARKAZ WAREHOUSE FOR THE NOV-25 (Minimum) | TOTAL=135,000.00
- Row 519: Finish=2025-11-31 | MINA ZAYED OPEN YARD FOR THE NOV-25 | TOTAL=33,000.00