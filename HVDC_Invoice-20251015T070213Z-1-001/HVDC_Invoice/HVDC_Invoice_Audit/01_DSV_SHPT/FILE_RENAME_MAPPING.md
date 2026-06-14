# File Rename Mapping Reference

**Date**: 2025-10-17  
**Purpose**: Quick reference for old to new file name mappings

---

## Quick Reference

### Code Files

```
OLD NAME                          NEW NAME
================================================================================
invoice_consolidator_v2.py     -> engine_individual_sheets.py
multi_month_consolidator.py    -> engine_multi_month.py
month_sheet_consolidator.py    -> engine_monthly_summary.py
consolidate_all_months.py      -> run_individual_consolidation.py
consolidate_month_sheets.py    -> run_monthly_consolidation.py
```

### Guide Documents

```
OLD NAME                              NEW NAME
================================================================================
MONTH_SUMMARY_SHEETS_GUIDE.md      -> GUIDE_Monthly_Summary.md
INDIVIDUAL_INVOICE_SHEETS_GUIDE.md -> GUIDE_Individual_Invoices.md
```

### Report Documents

```
OLD NAME                                         NEW NAME
================================================================================
INVOICE_VERIFICATION_FINAL_REPORT.md          -> REPORT_Individual_Verification.md
MONTH_SHEETS_CONSOLIDATION_COMPLETE_REPORT.md -> REPORT_Monthly_Consolidation.md
FINAL_MONTH_SHEETS_INTEGRATION_REPORT.md      -> REPORT_Monthly_Integration.md
ROBUST_HEADER_PATCH_FINAL_REPORT.md           -> REPORT_Header_Detection.md
RATE_SOURCE_FIX_COMPLETE_REPORT.md            -> REPORT_RateSource_Fix.md
MONTH_SHEETS_FINAL_VERIFICATION.md            -> REPORT_Monthly_Verification.md
FEBRUARY_2025_REV2_STRUCTURE_REPORT.md        -> REPORT_Feb2025_Structure.md
TOTAL_USD_DATA_LOSS_FIX_REPORT.md             -> REPORT_TotalUSD_Fix.md
```

### Summary Documents

```
OLD NAME                           NEW NAME
================================================================================
WORK_COMPLETION_FINAL_SUMMARY.md-> SUMMARY_Project_Complete.md
GUIDE_DOCUMENTATION_COMPLETE.md  -> SUMMARY_Guide_Documentation.md
```

### Index

```
OLD NAME                         NEW NAME
================================================================================
00_DOCUMENTATION_INDEX.md     -> INDEX.md
```

---

## Import Statement Migration

### Python Code

If you have custom scripts importing old modules:

```python
# OLD (NO LONGER WORKS)
from invoice_consolidator_v2 import InvoiceConsolidatorV2
from multi_month_consolidator import MultiMonthConsolidator
from month_sheet_consolidator import MonthSheetConsolidator

# NEW (USE THIS)
from engine_individual_sheets import InvoiceConsolidatorV2
from engine_multi_month import MultiMonthConsolidator
from engine_monthly_summary import MonthSheetConsolidator
```

### Bash/Command Line

If you have scripts or documentation referencing old commands:

```bash
# OLD (NO LONGER WORKS)
python consolidate_all_months.py
python consolidate_month_sheets.py

# NEW (USE THIS)
python run_individual_consolidation.py
python run_monthly_consolidation.py
```

---

## Documentation Link Migration

### Markdown Links

If you have documents linking to old files:

```markdown
<!-- OLD (BROKEN LINKS) -->
[Individual Guide](INDIVIDUAL_INVOICE_SHEETS_GUIDE.md)
[Monthly Guide](MONTH_SUMMARY_SHEETS_GUIDE.md)
[Verification Report](INVOICE_VERIFICATION_FINAL_REPORT.md)

<!-- NEW (USE THIS) -->
[Individual Guide](GUIDE_Individual_Invoices.md)
[Monthly Guide](GUIDE_Monthly_Summary.md)
[Verification Report](REPORT_Individual_Verification.md)
```

---

## File Purpose Quick Lookup

### By Category

**Engines** (Core logic):
- `engine_individual_sheets.py` - Extract data from individual invoice sheets
- `engine_multi_month.py` - Orchestrate multi-month consolidation
- `engine_monthly_summary.py` - Extract data from monthly summary sheets

**Run Scripts** (Executables):
- `run_individual_consolidation.py` - Run individual sheets consolidation (2,166 rows)
- `run_monthly_consolidation.py` - Run monthly summary consolidation (406 rows)

**Guides** (User documentation):
- `GUIDE_Monthly_Summary.md` - How to use monthly summary sheets
- `GUIDE_Individual_Invoices.md` - How to use individual invoice sheets

**Reports** (Technical reports):
- `REPORT_Individual_Verification.md` - Individual sheets verification
- `REPORT_Monthly_Consolidation.md` - Monthly sheets consolidation
- `REPORT_Header_Detection.md` - Header detection improvements
- `REPORT_RateSource_Fix.md` - RATE SOURCE data fix
- ... (6 more)

**Summaries** (Executive summaries):
- `SUMMARY_Project_Complete.md` - Overall project completion
- `SUMMARY_Guide_Documentation.md` - Guide documentation completion

---

## Search and Replace for Bulk Updates

If you need to update multiple files at once:

### Linux/Mac (grep + sed)

```bash
# Find files with old references
grep -r "invoice_consolidator_v2" .

# Replace in all Python files
find . -name "*.py" -exec sed -i 's/invoice_consolidator_v2/engine_individual_sheets/g' {} +
find . -name "*.py" -exec sed -i 's/multi_month_consolidator/engine_multi_month/g' {} +
find . -name "*.py" -exec sed -i 's/month_sheet_consolidator/engine_monthly_summary/g' {} +
```

### Windows (PowerShell)

```powershell
# Find files with old references
Get-ChildItem -Recurse -Include *.py,*.md | Select-String "invoice_consolidator_v2"

# Replace in all files (example for one pattern)
Get-ChildItem -Recurse -Include *.py | ForEach-Object {
    (Get-Content $_) -replace 'invoice_consolidator_v2', 'engine_individual_sheets' | Set-Content $_
}
```

---

## Backward Compatibility

### BREAKING CHANGES

The following will NO LONGER WORK:

1. Old import statements
2. Old command line scripts
3. Links to old file names in external documentation

### Migration Required

If you have:
- Custom scripts importing old modules
- Documentation referencing old files
- Scheduled jobs running old scripts
- External tools/IDE configurations

You MUST update them using this mapping reference.

---

## FAQ

**Q: Do I need to update my IDE bookmarks?**  
A: Yes, update any file path references in your IDE.

**Q: Will old git history still be accessible?**  
A: Yes, git tracks file renames. Use `git log --follow filename` to see history.

**Q: Can I use both old and new names?**  
A: No, old files no longer exist. Use new names only.

**Q: What if I forget the new name?**  
A: Refer to this document or use file search by content/purpose.

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**Maintained By**: HVDC Invoice Audit Team

