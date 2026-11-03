from pathlib import PurePath

from django.core.exceptions import ValidationError

MAX_PORTFOLIO_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_PORTFOLIO_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md", ".zip"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_avatar(upload):
    """Validate the image data and decoded format, not only its filename."""
    extension = PurePath(upload.name).suffix.lower()
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError("Оберіть зображення JPG, JPEG, PNG або WEBP.")
    expected_mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}[extension]
    if upload.content_type and upload.content_type.lower() != expected_mime:
        raise ValidationError("Тип файлу не відповідає його розширенню.")
    if upload.size > MAX_AVATAR_SIZE:
        raise ValidationError("Максимальний розмір аватара — 5 МБ.")
    try:
        from PIL import Image, UnidentifiedImageError
        upload.seek(0)
        image = Image.open(upload)
        if image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValidationError("Вміст файлу не відповідає дозволеним форматам зображень.")
        if image.width < 1 or image.height < 1 or image.width * image.height > 40_000_000:
            raise ValidationError("Зображення має некоректний або надмірний розмір.")
        image.verify()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ValidationError("Файл не є коректним зображенням.") from exc
    finally:
        upload.seek(0)


def validate_portfolio_file(upload):
    extension = PurePath(upload.name).suffix.lower()
    if extension not in ALLOWED_PORTFOLIO_EXTENSIONS:
        raise ValidationError("Дозволені формати: PDF, PNG, JPG, WEBP, TXT, MD та ZIP.")
    if upload.size > MAX_PORTFOLIO_FILE_SIZE:
        raise ValidationError("Максимальний розмір одного файлу — 10 МБ.")

    upload.seek(0)
    header = upload.read(16)
    upload.seek(0)
    signatures = {
        ".pdf": header.startswith(b"%PDF-"),
        ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
        ".webp": len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP",
        ".zip": header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
    }
    if extension in signatures and not signatures[extension]:
        raise ValidationError("Вміст файлу не відповідає його розширенню.")
    if extension in {".txt", ".md"}:
        content = upload.read()
        upload.seek(0)
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationError("Текстовий файл має бути у кодуванні UTF-8.") from exc
        if b"\x00" in content:
            raise ValidationError("Текстовий файл містить неприпустимі двійкові дані.")
