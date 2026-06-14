"""
Workflow Automator Module
==========================

RPA 및 알림 자동화

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import yaml
from pathlib import Path


class WorkflowAutomator:
    """
    RPA 및 알림 자동화

    Features:
    - Telegram/Slack 알림 발송
    - DO Validity 만료 체크 (Demurrage Risk)
    - 자동 경고 시스템
    - 불일치 항목 자동 플래그
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: config.yaml 파일 경로
        """
        self.logger = self._setup_logger()

        # 설정 로드
        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()

        # 알림 설정
        self.telegram_enabled = (
            self.config.get("notifications", {})
            .get("telegram", {})
            .get("enabled", False)
        )
        self.telegram_token = (
            self.config.get("notifications", {})
            .get("telegram", {})
            .get("bot_token", "")
        )
        self.telegram_channel = (
            self.config.get("notifications", {})
            .get("telegram", {})
            .get("channel_id", "")
        )

        self.slack_enabled = (
            self.config.get("notifications", {}).get("slack", {}).get("enabled", False)
        )
        self.slack_webhook = (
            self.config.get("notifications", {}).get("slack", {}).get("webhook_url", "")
        )

        # Demurrage 설정
        self.demurrage_config = self.config.get("demurrage", {})
        self.warning_days = self.demurrage_config.get("warning_days_before_expiry", 3)
        self.cost_per_day = self.demurrage_config.get("cost_estimates", {}).get(
            "per_day_usd", 75
        )

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("WorkflowAutomator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _default_config(self) -> Dict:
        """기본 설정"""
        return {
            "notifications": {
                "telegram": {"enabled": False},
                "slack": {"enabled": False},
            },
            "demurrage": {
                "enabled": True,
                "warning_days_before_expiry": 3,
                "cost_estimates": {"per_day_usd": 75},
            },
        }

    def trigger_alert(
        self, issue: Dict, channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        불일치 발견 시 즉시 알림 발송

        Args:
            issue: 이슈 딕셔너리
            channels: 알림 채널 리스트 ['telegram', 'slack', 'email']

        Returns:
            채널별 발송 성공 여부
        """
        if channels is None:
            channels = []
            if self.telegram_enabled:
                channels.append("telegram")
            if self.slack_enabled:
                channels.append("slack")

        results = {}

        # 메시지 생성
        message = self._format_alert_message(issue)

        # Telegram
        if "telegram" in channels and self.telegram_enabled:
            results["telegram"] = self._send_telegram(message)

        # Slack
        if "slack" in channels and self.slack_enabled:
            results["slack"] = self._send_slack(message)

        self.logger.info(f"Alert sent for {issue.get('type', 'UNKNOWN')}: {results}")
        return results

    def _format_alert_message(self, issue: Dict) -> str:
        """알림 메시지 포맷팅"""
        severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

        emoji = severity_emoji.get(issue.get("severity", "LOW"), "⚪")

        message = f"""
{emoji} **HVDC Invoice Validation Alert**

**Type**: {issue.get('type', 'UNKNOWN')}
**Severity**: {issue.get('severity', 'UNKNOWN')}
**Item Code**: {issue.get('item_code', 'N/A')}

**Details**:
{issue.get('details', 'No details provided')}

**Action Required**:
{issue.get('action', 'Manual review needed before approval')}

**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        return message

    def _send_telegram(self, message: str) -> bool:
        """Telegram 메시지 발송"""
        if not self.telegram_token or not self.telegram_channel:
            self.logger.warning("Telegram not configured")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_channel,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                self.logger.info("Telegram message sent successfully")
                return True
            else:
                self.logger.error(
                    f"Telegram send failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Telegram error: {e}")
            return False

    def _send_slack(self, message: str) -> bool:
        """Slack 메시지 발송"""
        if not self.slack_webhook:
            self.logger.warning("Slack not configured")
            return False

        payload = {"text": message, "mrkdwn": True}

        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)

            if response.status_code == 200:
                self.logger.info("Slack message sent successfully")
                return True
            else:
                self.logger.error(
                    f"Slack send failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Slack error: {e}")
            return False

    def check_demurrage_risk(self, do_data: Dict) -> Optional[Dict]:
        """
        DO Validity 만료 체크 및 자동 알림

        Args:
            do_data: Delivery Order 데이터

        Returns:
            Demurrage Risk 정보 (없으면 None)
        """
        if not self.demurrage_config.get("enabled", True):
            return None

        validity_date_str = do_data.get("delivery_valid_until")

        if not validity_date_str:
            return None

        # 날짜 파싱
        validity_date = self._parse_date(validity_date_str)

        if not validity_date:
            self.logger.warning(f"Cannot parse DO validity date: {validity_date_str}")
            return None

        # 현재 날짜와 비교
        now = datetime.now()
        days_remaining = (validity_date - now).days

        # 리스크 평가
        if days_remaining < 0:
            # 이미 만료됨
            risk_level = "CRITICAL"
            days_overdue = abs(days_remaining)
            estimated_cost = (
                days_overdue * self.cost_per_day * do_data.get("quantity", 1)
            )

            risk_info = {
                "risk_level": risk_level,
                "status": "EXPIRED",
                "days_overdue": days_overdue,
                "estimated_cost_usd": estimated_cost,
                "do_number": do_data.get("do_number"),
                "validity_date": validity_date.isoformat(),
                "containers": do_data.get("containers", []),
            }

            # 알림 발송
            self.trigger_alert(
                {
                    "type": "DEMURRAGE_EXPIRED",
                    "severity": "CRITICAL",
                    "item_code": do_data.get("item_code", "UNKNOWN"),
                    "details": f"DO {do_data.get('do_number')} expired {days_overdue} days ago. "
                    f"Estimated demurrage cost: ${estimated_cost:.2f}",
                    "action": "Immediate container return required to avoid additional charges",
                }
            )

            return risk_info

        elif days_remaining <= self.warning_days:
            # 경고 기간
            risk_level = "HIGH" if days_remaining <= 1 else "MEDIUM"

            risk_info = {
                "risk_level": risk_level,
                "status": "WARNING",
                "days_remaining": days_remaining,
                "potential_cost_usd": self.cost_per_day * do_data.get("quantity", 1),
                "do_number": do_data.get("do_number"),
                "validity_date": validity_date.isoformat(),
                "containers": do_data.get("containers", []),
            }

            # 알림 발송
            self.trigger_alert(
                {
                    "type": "DEMURRAGE_RISK",
                    "severity": risk_level,
                    "item_code": do_data.get("item_code", "UNKNOWN"),
                    "details": f"DO {do_data.get('do_number')} expires in {days_remaining} day(s). "
                    f"Potential demurrage cost: ${risk_info['potential_cost_usd']:.2f}/day",
                    "action": f"Arrange container return within {days_remaining} day(s)",
                }
            )

            return risk_info

        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d/%b/%Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None

    def auto_flag_inconsistencies(self, validation_report: Dict) -> Dict:
        """
        불일치 항목 자동 플래그 및 알림

        Args:
            validation_report: CrossDocValidator 검증 보고서

        Returns:
            처리 결과
        """
        item_code = validation_report.get("item_code", "UNKNOWN")
        issues = validation_report.get("all_issues", [])
        overall_status = validation_report.get("overall_status", "PASS")

        flagged_count = 0
        notified_count = 0

        # 트리거 설정
        triggers = self.config.get("notifications", {}).get("triggers", {})

        for issue in issues:
            issue_type = issue.get("type")
            severity = issue.get("severity", "LOW")

            # 자동 플래그 조건
            should_flag = False
            should_notify = False

            if severity in ["CRITICAL", "HIGH"]:
                should_flag = True
                should_notify = True

            # 특정 이슈 타입별 트리거
            if issue_type == "MBL_MISMATCH" and triggers.get("on_mbl_mismatch", True):
                should_flag = True
                should_notify = True

            # 플래그 설정
            if should_flag:
                issue["flagged"] = True
                issue["flagged_at"] = datetime.now().isoformat()
                flagged_count += 1

            # 알림 발송
            if should_notify:
                issue["item_code"] = item_code
                self.trigger_alert(issue)
                notified_count += 1

        # 전체 FAIL 상태 알림
        if overall_status == "FAIL" and triggers.get("on_validation_fail", True):
            self.trigger_alert(
                {
                    "type": "VALIDATION_FAILED",
                    "severity": "HIGH",
                    "item_code": item_code,
                    "details": f"Validation failed with {len(issues)} issue(s). "
                    f"HIGH: {validation_report['severity_breakdown']['HIGH']}, "
                    f"MEDIUM: {validation_report['severity_breakdown']['MEDIUM']}",
                    "action": "Review all issues before invoice approval",
                }
            )
            notified_count += 1

        result = {
            "item_code": item_code,
            "overall_status": overall_status,
            "total_issues": len(issues),
            "flagged_count": flagged_count,
            "notified_count": notified_count,
            "processed_at": datetime.now().isoformat(),
        }

        self.logger.info(
            f"Auto-flagged {flagged_count} issues, sent {notified_count} notifications for {item_code}"
        )
        return result

    def batch_check_demurrage(self, do_list: List[Dict]) -> List[Dict]:
        """
        여러 DO의 Demurrage Risk 배치 체크

        Args:
            do_list: DO 데이터 리스트

        Returns:
            리스크 정보 리스트
        """
        risks = []

        for do_data in do_list:
            risk = self.check_demurrage_risk(do_data)
            if risk:
                risks.append(risk)

        self.logger.info(
            f"Batch demurrage check: {len(risks)} risks found out of {len(do_list)} DOs"
        )
        return risks

    def generate_daily_summary(self, validation_reports: List[Dict]) -> Dict:
        """
        일일 요약 보고서 생성 및 발송

        Args:
            validation_reports: 일일 검증 보고서 리스트

        Returns:
            요약 보고서
        """
        total_items = len(validation_reports)

        status_counts = {"PASS": 0, "WARNING": 0, "FAIL": 0}
        total_issues = 0
        severity_totals = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for report in validation_reports:
            status = report.get("overall_status", "PASS")
            status_counts[status] = status_counts.get(status, 0) + 1

            total_issues += report.get("total_issues", 0)

            severity_breakdown = report.get("severity_breakdown", {})
            for severity, count in severity_breakdown.items():
                severity_totals[severity] = severity_totals.get(severity, 0) + count

        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_items_processed": total_items,
            "status_breakdown": status_counts,
            "total_issues": total_issues,
            "severity_totals": severity_totals,
            "pass_rate": (
                round(status_counts["PASS"] / total_items * 100, 1)
                if total_items > 0
                else 0
            ),
        }

        # 요약 메시지
        message = f"""
📊 **HVDC Daily Validation Summary**

**Date**: {summary['date']}
**Items Processed**: {total_items}

**Status Breakdown**:
- ✅ PASS: {status_counts['PASS']} ({summary['pass_rate']}%)
- ⚠️ WARNING: {status_counts['WARNING']}
- ❌ FAIL: {status_counts['FAIL']}

**Total Issues**: {total_issues}
- 🔴 HIGH: {severity_totals['HIGH']}
- 🟡 MEDIUM: {severity_totals['MEDIUM']}
- 🟢 LOW: {severity_totals['LOW']}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        # 알림 발송
        if total_items > 0:
            self._send_telegram(message)
            self._send_slack(message)

        self.logger.info(
            f"Daily summary generated: {total_items} items, {summary['pass_rate']}% pass rate"
        )
        return summary


# 사용 예시
if __name__ == "__main__":
    automator = WorkflowAutomator()

    # 테스트 1: 일반 알림
    test_issue = {
        "type": "MBL_MISMATCH",
        "severity": "HIGH",
        "item_code": "HVDC-ADOPT-SCT-0126",
        "details": "MBL numbers do not match between BOE and DO",
        "action": "Verify MBL number with shipping line",
    }

    # automator.trigger_alert(test_issue)

    # 테스트 2: Demurrage Risk 체크
    test_do = {
        "do_number": "DOCHP00042642",
        "delivery_valid_until": "15/10/2025",  # 3일 후
        "quantity": 3,
        "item_code": "HVDC-ADOPT-SCT-0126",
        "containers": ["CMAU2623154", "TGHU8788690", "TCNU4356762"],
    }

    risk = automator.check_demurrage_risk(test_do)

    if risk:
        print("Demurrage Risk Detected:")
        print(f"  Level: {risk['risk_level']}")
        print(f"  Status: {risk['status']}")
        print(f"  Days: {risk.get('days_remaining', 'N/A')}")
