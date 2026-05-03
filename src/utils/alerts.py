"""Slack and email alerting utilities."""
import json
import logging
import smtplib
from email.mime.text import MIMEText

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import config

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def send_slack_alert(message: str, level: str = "warning") -> bool:
    """Post a message to the configured Slack webhook."""
    if not config.slack_webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured — skipping Slack alert.")
        return False

    color_map = {"info": "#36a64f", "warning": "#ff9900", "error": "#d00000"}
    payload = {
        "attachments": [
            {
                "color": color_map.get(level, "#ff9900"),
                "text": message,
                "footer": f"Data Quality Framework [{config.env}]",
            }
        ]
    }
    resp = requests.post(
        config.slack_webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    return True


def send_email_alert(subject: str, body: str, to: str | None = None) -> bool:
    """Send a plain-text email alert (uses localhost SMTP by default)."""
    recipient = to or config.alert_email
    if not recipient:
        logger.warning("ALERT_EMAIL not configured — skipping email alert.")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "dq-framework@noreply.local"
    msg["To"] = recipient

    try:
        with smtplib.SMTP("localhost", 25) as smtp:
            smtp.sendmail(msg["From"], [recipient], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Email alert failed: %s", exc)
        return False


def alert(message: str, subject: str = "DQ Alert", level: str = "warning") -> None:
    """Send both Slack and email alerts."""
    send_slack_alert(message, level=level)
    send_email_alert(subject, message)
