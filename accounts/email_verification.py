import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerification


def send_verification(user, email=None):
    email = (email or user.pending_email or user.email).strip().lower()
    raw_token = secrets.token_urlsafe(32)
    EmailVerification.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    EmailVerification.objects.create(
        user=user, email=email,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/verify-email/{raw_token}/"
    context = {"user": user, "verification_url": url}
    message = EmailMultiAlternatives(
        subject="Підтвердіть електронну пошту — Резюме",
        body=render_to_string("emails/verify_email.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(render_to_string("emails/verify_email.html", context), "text/html")
    message.send(fail_silently=False)
