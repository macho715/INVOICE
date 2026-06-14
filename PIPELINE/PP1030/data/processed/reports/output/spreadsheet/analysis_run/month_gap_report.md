# Month gap report

- Expected range noted by user: 2025-04, 2025-05, 2025-06, 2025-07, 2025-08, 2025-09
- Missing in final output: 2025-05, 2025-06, 2025-07, 2025-08, 2025-09

## Source coverage
- HVDC WAREHOUSE_INVOICE.xlsx: {'2024-01': 9, '2024-02': 17, '2024-03': 27, '2024-04': 16, '2024-05': 11, '2024-06': 14, '2024-07': 32, '2024-08': 37, '2024-09': 23, '2024-10': 21, '2024-11': 41, '2024-12': 30, '2025-01': 47, '2025-02': 50, '2025-03': 35, '2025-04': 55}
- 복사본 Draft - (SCT)_DSV_Storage Operation Draft for Feb 2026 Rev1.xlsx: {'2024-01': 25, '2024-02': 19, '2024-03': 30, '2024-04': 22, '2024-05': 23, '2024-06': 22, '2024-07': 35, '2024-08': 42, '2024-09': 30, '2024-10': 30, '2025-11': 59, '2025-12': 31, '2026-01': 32, '2026-02': 33}
- HVDC_WAREHOUSE_INVOICE_all_billing_months.xlsx: {'2024-01': 9, '2024-02': 17, '2024-03': 27, '2024-04': 16, '2024-05': 11, '2024-06': 14, '2024-07': 32, '2024-08': 37, '2024-09': 23, '2024-10': 21, '2024-11': 41, '2024-12': 30, '2025-01': 47, '2025-02': 50, '2025-03': 35, '2025-04': 55, '2025-11': 56, '2025-12': 28, '2026-01': 29, '2026-02': 30}
- HVDC_WAREHOUSE_INVOICE_all_billing_months_formatted_hvdc_code_applied.xlsx: {'2024-01': 9, '2024-02': 17, '2024-03': 27, '2024-04': 16, '2024-05': 11, '2024-06': 14, '2024-07': 32, '2024-08': 37, '2024-09': 23, '2024-10': 21, '2024-11': 41, '2024-12': 30, '2025-01': 47, '2025-02': 50, '2025-03': 35, '2025-04': 55, '2025-11': 56, '2025-12': 28, '2026-01': 29, '2026-02': 30}

## Conclusion
- 2025-04 exists in the final output: 55 rows.
- 2025-05 through 2025-09 are not present in the final output.
- 2025-10 is also not present, because the available sources jump from 2025-04 to 2025-11.
- The project root source files found for this invoice are `HVDC WAREHOUSE_INVOICE.xlsx` and the DSV Storage Draft workbook; neither contains 2025-05 through 2025-09 invoice months.