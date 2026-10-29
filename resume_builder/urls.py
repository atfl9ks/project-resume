from django.contrib import admin
from django.urls import path
from accounts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("resumes/new/", views.resume_create, name="resume_create"),
    path("resumes/<int:resume_id>/", views.resume_preview, name="resume_preview"),
    path("resumes/<int:resume_id>/edit/", views.resume_edit, name="resume_edit"),
    path("resumes/<int:resume_id>/projects/new/", views.project_add, name="project_add"),
    path("projects/<int:project_id>/delete/", views.project_delete, name="project_delete"),
    path("attachments/<int:attachment_id>/delete/", views.attachment_delete, name="attachment_delete"),
    path("attachments/<int:attachment_id>/replace/", views.attachment_replace, name="attachment_replace"),
    path("attachments/<int:attachment_id>/download/", views.attachment_download, name="attachment_download"),
]
