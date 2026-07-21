import asyncio
from email.message import EmailMessage
import logging
import smtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    async def send_email(self, recipient: str, subject: str, body: str, html: str | None = None) -> None:
        if settings.email_provider == "ses":
            await self._send_via_ses(recipient, subject, body, html)
            return

        if not settings.smtp_host:
            logger.warning("SMTP is not configured. Email delivery is disabled.")
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.mail_from
        message["To"] = recipient
        message.set_content(body)
        if html:
            message.add_alternative(html, subtype="html")

        await asyncio.to_thread(self._send_message, message)

    def _send_message(self, message: EmailMessage) -> None:
        if settings.smtp_port == 465:
            smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        try:
            smtp.ehlo()
            if settings.smtp_port == 587:
                smtp.starttls()
                smtp.ehlo()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        finally:
            smtp.quit()

    async def _send_via_ses(self, recipient: str, subject: str, body: str, html: str | None) -> None:
        try:
            import boto3
        except ImportError:
            logger.error("boto3 is required to send email via Amazon SES.")
            return

        await asyncio.to_thread(self._send_via_ses_sync, recipient, subject, body, html)

    def _send_via_ses_sync(self, recipient: str, subject: str, body: str, html: str | None) -> None:
        import boto3

        client = boto3.client("ses", region_name=settings.effective_ses_region, **settings.aws_credentials_kwargs)
        body_content = {"Text": {"Data": body}}
        if html:
            body_content["Html"] = {"Data": html}

        client.send_email(
            Source=settings.effective_ses_from_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": body_content,
            },
        )

    async def send_verification_email(self, recipient: str, verification_url: str) -> None:
        subject = "Verify your CommerceOS account"
        body = f"Please verify your account by visiting {verification_url}."
        html = f"<p>Please verify your account by clicking <a href=\"{verification_url}\">here</a>.</p>"
        await self.send_email(recipient, subject, body, html)

    async def send_password_reset_email(self, recipient: str, reset_url: str) -> None:
        subject = "Reset your CommerceOS password"
        body = f"You can reset your password by visiting {reset_url}."
        html = f"<p>Reset your password by clicking <a href=\"{reset_url}\">here</a>.</p>"
        await self.send_email(recipient, subject, body, html)
