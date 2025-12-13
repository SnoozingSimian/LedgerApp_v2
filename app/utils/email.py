# app/utils/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using SMTP."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.app_url = os.getenv("APP_URL", "http://localhost:8000")

    def _send_email(self, to_email: str, subject: str, body_html: str) -> bool:
        """Send email via SMTP."""
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(body_html, "html")
            message.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_family_invite(
        self, to_email: str, inviter_name: str, family_name: str, token: str
    ) -> bool:
        """Send family invite email."""
        invite_url = f"{self.app_url}/invite/{token}"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>You're Invited to {family_name}!</h2>
                <p>Hi,</p>
                <p><strong>{inviter_name}</strong> has invited you to join the family <strong>{family_name}</strong> on LedgerApp.</p>
                
                <p>Click the link below to accept the invitation:</p>
                <p><a href="{invite_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Accept Invitation</a></p>
                
                <p>Or copy and paste this link: {invite_url}</p>
                
                <p>This invitation expires in 30 days.</p>
                
                <p>Best regards,<br/>LedgerApp Team</p>
            </body>
        </html>
        """

        subject = f"Join {family_name} on LedgerApp"
        return self._send_email(to_email, subject, html_body)

    def send_family_notification(
        self, to_email: str, user_name: str, family_name: str, role: str
    ) -> bool:
        """Send notification when user is added to family."""
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Welcome to {family_name}!</h2>
                <p>Hi {user_name},</p>
                <p>You have been added to the family <strong>{family_name}</strong> with role: <strong>{role}</strong>.</p>
                
                <p><a href="{self.app_url}/dashboard" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Go to Dashboard</a></p>
                
                <p>Best regards,<br/>LedgerApp Team</p>
            </body>
        </html>
        """

        subject = f"Added to {family_name} on LedgerApp"
        return self._send_email(to_email, subject, html_body)


# Singleton instance
email_service = EmailService()


def send_family_invite(
    to_email: str, inviter_name: str, family_name: str, token: str
) -> bool:
    """Convenience function to send family invite."""
    return email_service.send_family_invite(to_email, inviter_name, family_name, token)


def send_family_notification(
    to_email: str, user_name: str, family_name: str, role: str
) -> bool:
    """Convenience function to send family notification."""
    return email_service.send_family_notification(to_email, user_name, family_name, role)