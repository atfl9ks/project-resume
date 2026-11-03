import smtplib
import socket
import ssl

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sends a real test email through the configured email provider."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Email address that will receive the test message")

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND == "accounts.email_backends.BrevoEmailBackend":
            if not settings.DEFAULT_FROM_EMAIL or settings.DEFAULT_FROM_EMAIL == "no-reply@rezume.ua":
                raise CommandError("Укажите подтверждённый адрес отправителя в DEFAULT_FROM_EMAIL.")
            self.stdout.write("Отправляю тестовое письмо через Brevo HTTPS API; API-ключ скрыт.")
            message = EmailMultiAlternatives(
                subject="Тест отправки — Резюме",
                body="Это тестовое письмо. Brevo API принял сообщение.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[options["recipient"]],
            )
            message.attach_alternative("<p>Это тестовое письмо. Brevo API принял сообщение.</p>", "text/html")
            try:
                sent = message.send(fail_silently=False)
            except Exception as exc:
                raise CommandError(f"Brevo не отправил письмо: {exc}") from None
            if sent != 1:
                raise CommandError("Brevo не подтвердил отправку тестового письма.")
            self.stdout.write(self.style.SUCCESS(f"Brevo API принял письмо для {options['recipient']}. Проверьте входящие и папку «Спам»."))
            return

        required = {
            "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
            "EMAIL_HOST_PASSWORD": settings.EMAIL_HOST_PASSWORD,
            "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
        }
        missing = [name for name, value in required.items() if not value or value == "no-reply@rezume.ua"]
        if missing:
            raise CommandError("SMTP настройки отсутствуют: " + ", ".join(missing) + ". Заполните их в .env; письмо не отправлялось.")
        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            raise CommandError(f"Выбран backend {settings.EMAIL_BACKEND}, нужен django.core.mail.backends.smtp.EmailBackend.")
        if settings.EMAIL_HOST != "smtp.gmail.com" or settings.EMAIL_PORT != 587 or not settings.EMAIL_USE_TLS or settings.EMAIL_USE_SSL:
            raise CommandError("Для этой проверки ожидаются Gmail smtp.gmail.com:587, TLS=True и SSL=False.")

        connection = get_connection(fail_silently=False)
        self.stdout.write(f"Подключаюсь к {settings.EMAIL_HOST}:{settings.EMAIL_PORT} с TLS; секреты скрыты.")
        try:
            connection.open()
            self.stdout.write("SMTP-соединение и авторизация успешны.")
            message = EmailMultiAlternatives(
                subject="Тест отправки — Резюме",
                body="Это тестовое письмо. SMTP-сервер подтвердил приём сообщения.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[options["recipient"]],
                connection=connection,
            )
            message.attach_alternative("<p>Это тестовое письмо. SMTP-сервер подтвердил приём сообщения.</p>", "text/html")
            sent = message.send(fail_silently=False)
            if sent != 1:
                raise CommandError("SMTP не подтвердил отправку тестового письма.")
            self.stdout.write(self.style.SUCCESS(f"SMTP принял письмо для {options['recipient']}. Проверьте входящие и папку «Спам»; принятие SMTP не гарантирует доставку в Inbox."))
        except smtplib.SMTPAuthenticationError:
            raise CommandError("Gmail отклонил авторизацию. Проверьте EMAIL_HOST_USER и App Password (16 символов), а также включённую двухэтапную проверку Google.")
        except (ssl.SSLError, smtplib.SMTPNotSupportedError) as exc:
            raise CommandError(f"Ошибка TLS: {type(exc).__name__}. Проверьте TLS=True, SSL=False и порт 587.")
        except (socket.timeout, TimeoutError):
            raise CommandError("Тайм-аут подключения к SMTP. Проверьте сеть, VPN, firewall и EMAIL_TIMEOUT.")
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, OSError) as exc:
            raise CommandError(f"Не удалось подключиться к SMTP: {type(exc).__name__}. Проверьте сеть и доступность smtp.gmail.com:587.")
        except smtplib.SMTPException as exc:
            raise CommandError(f"SMTP отклонил письмо: {type(exc).__name__}. Проверьте адреса отправителя/получателя и лимиты Gmail.")
        finally:
            connection.close()
