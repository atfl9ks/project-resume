from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PortfolioAttachment, PortfolioProject, Resume, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Профіль", {"fields": ("display_name",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Контактні дані", {"fields": ("email", "display_name")}),)
    list_display = ("username", "email", "display_name", "is_staff")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "template", "updated_at")
    list_filter = ("template", "created_at")
    search_fields = ("full_name", "email", "user__email")


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "resume", "created_at")
    search_fields = ("title", "resume__full_name")


@admin.register(PortfolioAttachment)
class PortfolioAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "project", "uploaded_at")
    search_fields = ("original_name", "project__title")


