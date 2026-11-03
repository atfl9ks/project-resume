"""HTTPS transactional email backend for providers usable on Railway Hobby."""
import base64
import json
import os
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.mail.backends.base import BaseEmailBackend


class BrevoEmailBackend(BaseEmailBackend):
    """Send Django EmailMessage instances through Brevo's HTTPS API."""

    endpoint = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, *args, api_key=None, timeout=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key or os.getenv("BREVO_API_KEY", "")
        self.timeout = timeout or int(os.getenv("EMAIL_TIMEOUT", "15"))

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            raise RuntimeError("BREVO_API_KEY не задан в Variables Railway.")
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                self._send_one(message)
            except Exception:
                if not self.fail_silently:
                    raise
            else:
                sent += 1
        return sent

    def _send_one(self, message):
        sender_name, sender_email = parseaddr(message.from_email or "")
        payload = {
            "sender": {"email": sender_email, **({"name": sender_name} if sender_name else {})},
            "to": [{"email": address} for address in message.to],
            "subject": message.subject,
        }
        if message.cc:
            payload["cc"] = [{"email": address} for address in message.cc]
        if message.bcc:
            payload["bcc"] = [{"email": address} for address in message.bcc]
        if message.reply_to:
            payload["replyTo"] = {"email": message.reply_to[0]}

        html_body = next((content for content, mimetype in getattr(message, "alternatives", []) if mimetype == "text/html"), None)
        if html_body:
            payload["htmlContent"] = html_body
        if message.body and (not message.content_subtype == "html" or not html_body):
            payload["textContent"] = message.body
        elif not html_body:
            payload["textContent"] = " "

        attachments = []
        for attachment in message.attachments:
            if isinstance(attachment, tuple):
                filename, content, mimetype = attachment
                if isinstance(content, str):
                    content = content.encode()
                attachments.append({"name": filename, "content": base64.b64encode(content).decode("ascii")})
        if attachments:
            payload["attachment"] = attachments

        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"api-key": self.api_key, "accept": "application/json", "content-type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"Brevo API ответил HTTP {response.status}.")
                response.read()
        except HTTPError as exc:
            detail = exc.read(1200).decode("utf-8", "replace")
            raise RuntimeError(f"Brevo API отклонил письмо (HTTP {exc.code}): {detail}") from None
        except URLError as exc:
            reason = getattr(exc, "reason", exc).__class__.__name__
            raise RuntimeError(f"Не удалось подключиться к Brevo API по HTTPS: {reason}.") from None
