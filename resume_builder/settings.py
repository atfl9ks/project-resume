from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
for env_line in (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines() if (BASE_DIR / ".env").exists() else []:
    env_line = env_line.strip()
    if env_line and not env_line.startswith("#") and "=" in env_line:
        env_key, env_value = env_line.split("=", 1)
        os.environ.setdefault(env_key.strip(), env_value.strip().strip('"').strip("'"))
def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


DEBUG = env_bool("DEBUG", default=not bool(os.getenv("RAILWAY_ENVIRONMENT_NAME") or os.getenv("RENDER_EXTERNAL_HOSTNAME")))
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("SECRET_KEY must be configured for production.")
    SECRET_KEY = "django-insecure-local-development-only-key"
_platform_hosts = [os.getenv("RAILWAY_PUBLIC_DOMAIN", ""), os.getenv("RENDER_EXTERNAL_HOSTNAME", "")]
_configured_hosts = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS = list(dict.fromkeys(host.strip() for host in [*_configured_hosts, *_platform_hosts] if host.strip()))
_platform_origins = [f"https://{host}" for host in _platform_hosts if host]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(origin.strip() for origin in [*os.getenv("CSRF_TRUSTED_ORIGINS", "").split(","), *_platform_origins] if origin.strip()))

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "accounts",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "resume_builder.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
WSGI_APPLICATION = "resume_builder.wsgi.application"
ASGI_APPLICATION = "resume_builder.asgi.application"
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)}
elif all(os.getenv(key) for key in ("PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE")):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["PGHOST"],
        "PORT": os.environ["PGPORT"],
        "USER": os.environ["PGUSER"],
        "PASSWORD": os.environ["PGPASSWORD"],
        "NAME": os.environ["PGDATABASE"],
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"sslmode": "require"} if not DEBUG else {},
    }}
else:
    # Keep local development on SQLite, but never silently create an ephemeral
    # SQLite database in a production container.
    DATABASES = ({"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
                 if DEBUG else {"default": {"ENGINE": "django.db.backends.dummy"}})
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "accounts.password_validators.PasswordCharacterClassValidator"},
    {"NAME": "accounts.password_validators.ZxcvbnPasswordStrengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles")))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_URL = "/media/"
_media_root = os.getenv("MEDIA_ROOT") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
MEDIA_ROOT = Path(_media_root or BASE_DIR / "media")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
if not DEBUG and EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
    raise RuntimeError("The console email backend is disabled in production. Configure an SMTP backend.")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() in {"1", "true", "yes"}
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "15"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@rezume.ua")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or ("https://" + (os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("RENDER_EXTERNAL_HOSTNAME")) if os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("RENDER_EXTERNAL_HOSTNAME") else "http://127.0.0.1:8000")).rstrip("/")
EMAIL_VERIFICATION_RESEND_SECONDS = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 55 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 5
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
# HSTS preload is a separate opt-in: browsers may retain it for a long time,
# so enable only after confirming every subdomain will always use HTTPS.
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
