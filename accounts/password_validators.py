"""Local password rules used by Django's standard password validation flow."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
try:
    from zxcvbn import zxcvbn
except ImportError:  # Keep Django's auth checks loadable before optional deps are installed.
    zxcvbn = None


def _fallback_score(password, user_inputs):
    """Conservative local estimate for environments missing the zxcvbn package."""
    value = password.lower()
    if any(word and word.lower() in value for word in ("password", "passw0rd", "qwerty", "letmein", "welcome", "admin", "123456")):
        return 0
    if any(part in value for part in ("0123", "1234", "abcd", "qwer", "asdf")) or re.search(r"(.)\1{2,}", value):
        return 1
    if any(item and item.lower() in value for item in user_inputs):
        return 1
    pool = (26 if re.search(r"[a-z]", password) else 0) + (26 if re.search(r"[A-Z]", password) else 0) + (10 if re.search(r"[0-9]", password) else 0) + (32 if re.search(r"[^A-Za-z0-9\s]", password) else 0)
    entropy = len(password) * (pool.bit_length() - 1 if pool else 0)
    if len(password) < 8 or entropy < 28:
        return 0
    if entropy < 38:
        return 1
    if entropy < 52:
        return 2
    if entropy < 72:
        return 3
    return 4


class PasswordCharacterClassValidator:
    """Require the five character categories shown in the signup meter."""

    def validate(self, password, user=None):
        missing = []
        if len(password) < 8:
            missing.append("щонайменше 8 символів")
        if not re.search(r"[A-Z]", password):
            missing.append("велику латинську літеру")
        if not re.search(r"[a-z]", password):
            missing.append("малу латинську літеру")
        if not re.search(r"[0-9]", password):
            missing.append("цифру")
        if not re.search(r"[^A-Za-z0-9\s]", password):
            missing.append("спеціальний символ")
        if missing:
            raise ValidationError(
                _("Додайте до пароля: %(requirements)s."),
                code="password_missing_categories",
                params={"requirements": ", ".join(missing)},
            )

    def get_help_text(self):
        return _("Використайте щонайменше 8 символів, велику й малу латинські літери, цифру та спеціальний символ.")


class ZxcvbnPasswordStrengthValidator:
    """Reject zxcvbn scores below medium without sending passwords off-site."""

    minimum_score = 2  # zxcvbn's 0..4 scale: 2 is medium.

    def validate(self, password, user=None):
        user_inputs = []
        if user:
            for attribute in ("username", "email", "display_name", "first_name", "last_name"):
                value = getattr(user, attribute, "")
                if value:
                    user_inputs.append(str(value))
        score = zxcvbn(password, user_inputs=user_inputs)["score"] if zxcvbn else _fallback_score(password, user_inputs)
        if score < self.minimum_score:
            raise ValidationError(
                _("Цей пароль легко вгадати. Зробіть його довшим і уникайте поширених слів та послідовностей."),
                code="password_too_weak",
            )

    def get_help_text(self):
        return _("Не використовуйте поширені слова, повтори символів або прості послідовності.")
