# DOMESTIC September 2025 Invoice Audit - Final Report

**Generated**: 2025-10-13 01:49:45  
**System**: DOMESTIC Invoice Audit v1.0  
**Status**: ✅ Completed

---

## Executive Summary

### 📊 Overall Statistics

- **Total Items**: 44개
- **Total Amount**: $20,932.65 USD
- **Processing Time**: 0.49초
- **System**: Inland Transportation (Domestic Delivery)

### ✅ Validation Results

| Status | Count | Percentage |
|--------|-------|-----------|
| ✅ **PASS** | 27 | 61.4% |
| ⚠️ **WARN** | 0 | 0.0% |
| 🔶 **HIGH** | 1 | 2.3% |
| 🔴 **CRITICAL** | 16 | 36.4% |

### 🎯 Decision Summary

| Decision | Count | Percentage |
|----------|-------|-----------|
| PASS | 14 | 31.8% |
| PENDING_REVIEW | 20 | 45.5% |
| FAIL | 1 | 2.3% |

---

## COST-GUARD Band Analysis

```
PASS (≤2%):      █████████████ 27
WARN (2-5%):      0
HIGH (5-10%):     1
CRITICAL (>10%): ████████ 16
```

---

## Flags Analysis

| Flag | Count |
|------|-------|
| MIN_FARE_APPLIED | 14 |
| LOW_SIMILARITY | 10 |
| UNDER_CHARGE_REVIEW | 6 |
| AUTO_FAIL | 4 |


---

## Top Issues (HIGH/CRITICAL)

| Shipment | Origin → Destination | Rate | Ref | Δ% | Band |
|----------|---------------------|------|-----|-----|------|
| HVDC-DSV-HE-SHU-199 | HAULER DUBAI → SHUWEIHAT Site | $1307.01 | $287.50 | +354.6% | CRITICAL |
| HVDC-DSV-HAU-SHU-231 | HAULER DUBAI → SHUWEIHAT Site | $1307.01 | $287.50 | +354.6% | CRITICAL |
| HVDC-ADOPT-SCT-0123-0124 | DSV Mussafah Yard → MIRFA PMO SAMSUNG + SHUWEIHAT POWER STATION | $810.00 | $200.00 | +305.0% | CRITICAL |
| HVDC-DSV-HE-MIR-TEC-224 | SAMSUNG MOSB YARD → MIRFA SITE | $714.00 | $200.00 | +257.0% | CRITICAL |
| HVDC-DSV-SHU-SKM-226 | SHUWEIHAT Site → Surti Industries LLC (JEBEL ALI) | $410.00 | $150.00 | +173.3% | CRITICAL |
| HVDC-ADOPT-HE-0499 | Al Masaood (MOSB) → SHUWEIHAT Site | $1524.85 | $600.00 | +154.1% | CRITICAL |
| HVDC-MIR-DSV-221 | MIRFA SITE → DSV M44 WAREHOUSE | $420.00 | $200.00 | +110.0% | CRITICAL |
| HVDC-DSV-PRE-MIR/SHU/DAS/AGI-213 | DSV Mussafah Yard → MIRFA SITE | $210.00 | $420.00 | -50.0% | CRITICAL |
| HVDC-DSV-PRE-MDAS-232 (PEI_SCT-19LT-PJC-LPO-1450) | SAMSUNG MOSB YARD → SHUWEIHAT Site | $210.00 | $150.00 | +40.0% | CRITICAL |
| HVDC-DSV-MOSB-SHU-216 | SAMSUNG MOSB YARD → SHUWEIHAT Site | $210.00 | $150.00 | +40.0% | CRITICAL |


---

## Similarity Join Analysis

- **Exact Matches**: 12
- **Similarity Joins (≥0.60)**: 16
- **Low Similarity (<0.60)**: 16
- **REF_MISSING**: 0

---

## Configuration

**FX Rate**: 1 USD = 3.6725 AED (Fixed)

**COST-GUARD Bands**:
- PASS: ≤2.00%
- WARN: 2.01-5.00%
- HIGH: 5.01-10.00%
- CRITICAL: >10.00%


**Similarity Weights**:
- Origin: 0.35
- Destination: 0.35
- Vehicle: 0.10
- Distance: 0.10 (≤15km decay)
- Rate: 0.10 (±30% decay)

**Threshold**: 0.60

---

## File Outputs

### JSON
```
Results/Sept_2025/JSON/domestic_sept_2025_result_20251013_014944.json
```

### CSV
```
Results/Sept_2025/CSV/domestic_sept_2025_result_20251013_014944.csv
```

### Proof Artifact
**SHA256**: `0992ffddc64d9e4831a26cce3cac38506f1700c48533577cf1cf23c7ed010e76`

---

## PRISM Recap Card

```
N/A
```

---

**Report Generated**: 2025-10-13 01:49:45  
**Processing Time**: 0.49초  
**Status**: ✅ Complete

