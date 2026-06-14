# Session Summary (2025-10-25 19:05, TZ=Asia/Dubai)

## Last Decisions
- What we changed: v4.0.37 - 동일시각 다창고 전이 중복 집계 제거
- Why (evidence/issue): DSV Indoor 누적 과대(1255), DSV Al Markaz 누적 음수 발생

## 작업 내역 (2025-10-25)

### v4.0.37 패치: 동일시각 전이 중복 집계 제거
- **문제**: 같은 timestamp의 다창고 전이를 체인 전이와 연속 시점 전이에서 각각 집계
- **해결**: final_rows 수집 후 최종 상태만 연속 시점 전이에 사용
- **결과**: DSV Indoor 1803, DSV Al Markaz 177 (음수 해결)
- **파일**: `scripts/core/flow_ledger_v2.py`, 백업 `flow_ledger_v2.py.backup_before_dedup`

## Next Unchecked Test (plan.md)
- [x] p11111.md 패치 적용 완료 (타임존/동일시각/피벗)
- [x] 중복 집계 수정 완료

## Last Outputs (attach or path)
- Stage3 report: data/processed/reports/HVDC_입고로직_종합리포트_20251025_190454_v3.0-corrected.xlsx
- CHANGELOG: v4.0.37 항목 추가 완료

## Risks/Blocks
- 없음

## Owner/Reviewers
- 작업자: MACHO-GPT v3.4-mini
