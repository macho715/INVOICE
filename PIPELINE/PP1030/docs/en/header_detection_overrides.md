# Header Detection Hardening Guide (v4.0.53)

## Summary
- `HeaderDetectionResult` now exposes both confidence scores and warnings for heuristic detection.
- `DataSynchronizerV30` evaluates header candidates in the order: manual override → heuristic → vendor default.
- If the semantic validation for the `case_number` key fails, the loader automatically attempts the next candidate.
- When vendor detection is inconclusive, no default row is forced.

## Manually Pinning Header Rows
```bash
python scripts/stage1_sync_sorted/data_synchronizer_v30.py \
  --master /path/to/master.xlsx \
  --warehouse /path/to/warehouse.xlsx \
  --header-override Warehouse:Sheet1=2 \
  --header-override *=summary=0
```
- Format: `<file_label>:<sheet>=<0-based row index>`
- `*` acts as a wildcard for file label or sheet name.
- Provide the flag multiple times to cover several sheets.

## Operational Notes
- Watch for `LOW_CONFIDENCE` logs and confirm whether vendor or manual fallbacks were applied.
- The new regression tests in `tests/test_header_detection_strategy.py` guard the primary scenarios.
- Downstream pipeline calls automatically benefit from the hardened logic without further changes.
