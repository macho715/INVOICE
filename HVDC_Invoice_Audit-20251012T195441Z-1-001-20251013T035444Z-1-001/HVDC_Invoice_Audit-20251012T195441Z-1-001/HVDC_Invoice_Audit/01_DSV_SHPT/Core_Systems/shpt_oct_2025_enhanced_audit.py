#!/usr/bin/env python3
"""
SHPT Enhanced October 2025 Invoice Audit System

10월 2025 인보이스 감사를 위한 래퍼 스크립트
SHPTEnhancedAuditSystem을 사용하여 10월 데이터 처리
"""

import sys
from pathlib import Path

# 공통 클래스 import
from shpt_sept_2025_enhanced_audit import SHPTEnhancedAuditSystem
import logging


def main():
    """메인 실행 함수 (October 2025용)"""
    print("[SHPT Enhanced] Oct 2025 Invoice Audit System")
    print("=" * 80)

    auditor = SHPTEnhancedAuditSystem(month="Oct", year=2025)
    result = auditor.run_full_enhanced_audit()

    if result:
        logging.info("\n[SUCCESS] Enhanced audit completed successfully.")
        logging.info(f"[SAVED] Results saved to Results/Oct_2025 directory.")

        # Portal Fee 항목 상세 출력
        portal_fee_items = [
            item for item in result["items"] if item["charge_group"] == "PortalFee"
        ]
        if portal_fee_items:
            logging.info(f"\n[PORTAL FEE] {len(portal_fee_items)} items:")
            for pf_item in portal_fee_items[:5]:  # 최대 5개만 출력
                logging.info(f"  - {pf_item['description']}")
                logging.info(f"    Draft: ${pf_item['unit_rate']:.2f}")
                if pf_item.get("doc_aed"):
                    logging.info(f"    Doc AED: {pf_item['doc_aed']}")
                    logging.info(f"    Ref USD: ${pf_item['ref_rate_usd']:.2f}")
                logging.info(f"    Delta: {pf_item['delta_pct']:.2f}%")
                logging.info(f"    Tolerance: +/-{pf_item['tolerance']*100}%")
                logging.info(f"    Status: {pf_item['status']}")
    else:
        logging.error("\n[ERROR] Enhanced audit failed")


if __name__ == "__main__":
    main()

