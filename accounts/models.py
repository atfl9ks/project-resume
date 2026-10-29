from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from uuid import uuid4

from .validators import validate_portfolio_file


class User(AbstractUser):
    email = models.EmailField("email", unique=True)
    display_name = models.CharField("ім’я", max_length=120)

    def __str__(self):
        return self.email


class Resume(models.Model):
    TEMPLATE_CHOICES = [
        ("classic", "Classic"),
        ("modern", "Modern"),
        ("minimal", "Minimal"),
        ("developer", "Developer"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    template = models.CharField(max_length=30, choices=TEMPLATE_CHOICES)
    full_name = models.CharField("Ім’я та прізвище", max_length=150)
    email = models.EmailField("Електронна пошта")
    phone = models.CharField("Телефон", max_length=40, blank=True)
    location = models.CharField("Місто", max_length=120, blank=True)
    position = models.CharField("Бажана посада", max_length=150, blank=True)
    summary = models.TextField("Про себе", blank=True)
    experience = models.TextField("Досвід роботи", blank=True)
    education = models.TextField("Освіта", blank=True)
    skills = models.TextField("Навички", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} — {self.get_template_display()}"


def portfolio_upload_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    suffix = f".{extension}" if extension else ""
    return f"portfolio/{timezone.now():%Y/%m}/{uuid4().hex}{suffix}"


class PortfolioProject(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField("Назва проєкту", max_length=160)
    description = models.TextField("Опис", blank=True)
    technologies = models.CharField("Технології", max_length=300, blank=True)
    repository_url = models.URLField("GitHub або репозиторій", blank=True)
    demo_url = models.URLField("Демо", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return self.title


class PortfolioAttachment(models.Model):
    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=portfolio_upload_path, validators=[validate_portfolio_file])
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name
