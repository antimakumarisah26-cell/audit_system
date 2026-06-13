"""
app/services/email_service.py
──────────────────────────────
Gmail SMTP alert service.
Credentials come from environment variables only — never hardcoded.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.config import config
from app.utils.logger import logger


class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = config.GMAIL_EMAIL
        self.password = config.GMAIL_APP_PASSWORD

    def is_configured(self) -> bool:
        return bool(self.email and self.password and "@" in self.email)

    def send(self, to: str | List[str], subject: str, body_html: str) -> bool:
        if not self.is_configured():
            logger.warning("Email not configured — skipping send.")
            return False

        recipients = [to] if isinstance(to, str) else to
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.email, self.password)
                server.sendmail(self.email, recipients, msg.as_string())

            logger.info(f"Email sent to {recipients}: {subject}")
            return True
        except Exception as exc:
            logger.error(f"Email send failed: {exc}")
            return False

    def send_high_risk_alert(self, to: str, branch_name: str, risk_score: float, reason: str) -> bool:
        level = "🔴 CRITICAL" if risk_score >= config.RISK_CRITICAL_THRESHOLD else "🟠 HIGH"
        subject = f"{level} Risk Alert — {branch_name}"
        body = f"""
        <html><body style="font-family:Arial,sans-serif;padding:20px;">
          <h2 style="color:#d32f2f;">⚠️ High Risk Account Detected</h2>
          <table style="border-collapse:collapse;width:100%">
            <tr><td style="padding:8px;font-weight:bold;">Branch</td><td>{branch_name}</td></tr>
            <tr style="background:#f5f5f5;"><td style="padding:8px;font-weight:bold;">Risk Score</td><td>{risk_score:.1f} / 100</td></tr>
            <tr><td style="padding:8px;font-weight:bold;">Level</td><td>{level}</td></tr>
            <tr style="background:#f5f5f5;"><td style="padding:8px;font-weight:bold;">Reason</td><td>{reason}</td></tr>
          </table>
          <p style="margin-top:20px;">Please log in to the <strong>AI Audit Management System</strong> to review this account immediately.</p>
          <p style="color:#999;font-size:12px;">This is an automated alert. Do not reply to this email.</p>
        </body></html>
        """
        return self.send(to, subject, body)


email_service = EmailService()