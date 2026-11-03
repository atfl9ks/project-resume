from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from django.views.static import serve as serve_media
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from accounts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("healthz/", views.healthz, name="healthz"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("help/", views.help_page, name="help"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="password_reset_form.html", email_template_name="emails/password_reset.txt", subject_template_name="emails/password_reset_subject.txt", success_url=reverse_lazy("password_reset_done")), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html", success_url=reverse_lazy("password_reset_complete")), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name="password_reset_complete"),
    path("verify-email/", views.verify_pending, name="verify_pending"),
    path("verify-email/resend/", views.resend_verification, name="resend_verification"),
    path("verify-email/change/", views.change_pending_email, name="change_pending_email"),
    path("verify-email/<str:token>/", views.verify_email, name="verify_email"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/avatar/", views.avatar_update, name="avatar_update"),
    path("resumes/new/", views.resume_create, name="resume_create"),
    path("resumes/<int:resume_id>/", views.resume_preview, name="resume_preview"),
    path("resumes/<int:resume_id>/edit/", views.resume_edit, name="resume_edit"),
    path("resumes/<int:resume_id>/projects/new/", views.project_add, name="project_add"),
    path("projects/<int:project_id>/delete/", views.project_delete, name="project_delete"),
    path("attachments/<int:attachment_id>/delete/", views.attachment_delete, name="attachment_delete"),
    path("attachments/<int:attachment_id>/replace/", views.attachment_replace, name="attachment_replace"),
    path("attachments/<int:attachment_id>/download/", views.attachment_download, name="attachment_download"),
]

# User avatars are validated raster images and intentionally public.
# Portfolio attachments are excluded and remain available only through
# their ownership-checked download view.
urlpatterns.append(re_path(r"^media/avatars/(?P<path>.+)$", serve_media, {"document_root": settings.MEDIA_ROOT / "avatars"}))
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
