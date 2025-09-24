# Invoice Audit System - TDD Development Plan

## Project Overview
HVDC Project 송장 감사 시스템 - Samsung C&T Logistics & ADNOC·DSV Partnership

## Core Modules
- `audit_runner.py`: 메인 감사 실행 엔진
- `joiners.py`: 데이터 정규화 및 조인 로직
- `rules.py`: FX 환율 및 밴드 규칙 엔진

## Tests

### audit_runner.py Tests
- [ ] test: should_load_invoice_data_from_excel (file: py/test_audit_runner.py, name: test_should_load_invoice_data_from_excel)
- [ ] test: should_validate_invoice_format (file: py/test_audit_runner.py, name: test_should_validate_invoice_format)
- [ ] test: should_calculate_totals_correctly (file: py/test_audit_runner.py, name: test_should_calculate_totals_correctly)
- [ ] test: should_detect_discrepancies (file: py/test_audit_runner.py, name: test_should_detect_discrepancies)
- [ ] test: should_generate_audit_report (file: py/test_audit_runner.py, name: test_should_generate_audit_report)

### joiners.py Tests
- [ ] test: should_normalize_currency_codes (file: py/test_joiners.py, name: test_should_normalize_currency_codes)
- [ ] test: should_join_invoice_with_rates (file: py/test_joiners.py, name: test_should_join_invoice_with_rates)
- [ ] test: should_handle_missing_data (file: py/test_joiners.py, name: test_should_handle_missing_data)
- [ ] test: should_validate_data_types (file: py/test_joiners.py, name: test_should_validate_data_types)

### rules.py Tests
- [ ] test: should_apply_fx_rates (file: py/test_rules.py, name: test_should_apply_fx_rates)
- [ ] test: should_validate_currency_bands (file: py/test_rules.py, name: test_should_validate_currency_bands)
- [ ] test: should_calculate_tolerance_limits (file: py/test_rules.py, name: test_should_calculate_tolerance_limits)
- [ ] test: should_detect_rate_anomalies (file: py/test_rules.py, name: test_should_detect_rate_anomalies)

## Implementation Order
1. Start with audit_runner.py core functionality
2. Implement joiners.py data normalization
3. Add rules.py FX and validation logic
4. Integration testing and optimization

## Quality Gates
- All tests must pass
- Code coverage ≥ 90%
- Performance: Process 1000 invoices in < 5 seconds
- Compliance: FANR/MOIAT validation rules
