# Shipment warehouse cost summary

## Scope
- Invoice source: `C:\HVDC_WORK\PIPELINE\PP1030\output\spreadsheet\HVDC_WAREHOUSE_INVOICE_all_billing_months_formatted_hvdc_code_applied_may_oct2025.xlsx`
- Warehouse source: `C:\HVDC_WORK\PIPELINE\PP1030\output\WAREHOUSE_HITACHI,SIMENSE.xlsx`
- Output workbook: `C:\HVDC_WORK\PIPELINE\PP1030\output\spreadsheet\analysis_run\shipment_warehouse_cost_summary.xlsx`
- Rule: single HVDC shipment rows are summed directly. Multi-code invoice rows are not allocated to a shipment and remain in `multi_code_review`.
- Rule: `DSV MZP` is treated as Mina Zayed Port yard and excluded from DSV handling candidate package count, per user instruction.

## Reconciliation
- All invoice TOTAL: 21,325,810.86
- Single-code shipment summary TOTAL: 5,798,678.62
- Multi-code review TOTAL: 263,692.65
- Non-HVDC review TOTAL: 15,263,439.59
- Reconciled TOTAL: 21,325,810.86
- Reconciliation pass: True

## User examples
### HVDC-ADOPT-HE-0383
- Invoice S No.: 667, 668
- Operation month: 2025-07 / Billing month: 2025-08
- Invoice TOTAL: 17,710.05
- Warehouse total pkg: 22
- DSV handling candidate pkg excluding MZP: 0
- Site-direct/no-DSV pkg: 22
- Warehouse route note: site route found with no DSV warehouse handling location
- Interpretation: the user month appears to be the operation month 2025-07; the invoice billing month in the combined sheet is 2025-08.

### HVDC-ADOPT-HE-0178
- Invoice S No.: 168, 169
- Operation month: 2024-08 / Billing month: 2024-09
- Invoice TOTAL: 32,900.00
- Warehouse total pkg: 118
- DSV Indoor pkg: 5
- DSV Outdoor pkg: 103
- DSV MZP pkg excluded: 5
- DSV handling candidate pkg excluding MZP: 108
- Warehouse route note: DSV warehouse/yard handling location found; MZP port yard found; excluded from DSV handling by user rule
- Interpretation: the directly attributable invoice total is 32,900.00. S No. 439 contains HE-0178 inside a multi-code row and is left unallocated for review.

## Review handling
- Multi-code rows needing manual allocation/review: 60
- Non-HVDC/service rows kept outside shipment grouping: 179
- Suggested next step: review `multi_code_review` for rows that should be split across several shipments before using shipment totals as final billing allocation.
