from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import EmailLoginForm, PortfolioProjectForm, ProfileForm, RegistrationForm, ResumeForm
from .models import PortfolioAttachment, PortfolioProject, Resume
from .validators import validate_portfolio_file


def home(request):
    return render(request, "index.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Акаунт створено. Вітаємо!")
        return redirect("profile")
    return render(request, "auth.html", {"form": form, "mode": "register"})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = EmailLoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        messages.success(request, "Ви успішно увійшли.")
        return redirect("profile")
    return render(request, "auth.html", {"form": form, "mode": "login"})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Ви вийшли з акаунта.")
    return redirect("home")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профіль оновлено.")
        return redirect("profile")
    return render(request, "profile.html", {
        "form": form,
        "resumes": request.user.resumes.order_by("-updated_at"),
    })


@login_required
def resume_create(request):
    legacy_id = request.GET.get("resume_id")
    if legacy_id:
        return redirect("resume_edit", resume_id=legacy_id)
    template_id = request.GET.get("template", "minimal")
    allowed_templates = dict(Resume.TEMPLATE_CHOICES)
    if template_id not in allowed_templates:
        raise Http404("Шаблон не найден")
    form = ResumeForm(request.POST or None, initial={"template": template_id})
    if request.method == "POST" and form.is_valid():
        resume = form.save(commit=False)
        resume.user = request.user
        resume.save()
        return redirect("resume_preview", resume_id=resume.pk)
    return render(request, "resume_form.html", {
        "form": form, "resume": None,
        "template_name": allowed_templates[template_id],
        "projects": (),
    })


@login_required
def resume_edit(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
    form = ResumeForm(request.POST or None, instance=resume)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Резюме оновлено.")
        return redirect("resume_preview", resume_id=resume.pk)
    return render(request, "resume_form.html", {
        "form": form, "resume": resume,
        "template_name": resume.get_template_display(),
        "projects": resume.projects.prefetch_related("attachments"),
    })


@login_required
def resume_preview(request, resume_id):
    resume = get_object_or_404(
        Resume.objects.prefetch_related("projects__attachments"),
        pk=resume_id,
        user=request.user,
    )
    themes = {
        "classic": "resumes/themes/classic.html",
        "modern": "resumes/themes/modern.html",
        "minimal": "resumes/themes/minimal.html",
        "developer": "resumes/themes/developer.html",
    }
    theme_template = themes.get(resume.template)
    if not theme_template:
        raise Http404("Шаблон резюме не знайдено")
    return render(request, "resume_preview.html", {
        "resume": resume,
        "theme_template": theme_template,
    })


@login_required
def project_add(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
    form = PortfolioProjectForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploads = form.cleaned_data.get("files", [])
        if len(uploads) > 5:
            form.add_error("files", "Можна додати не більше 5 файлів за раз.")
        else:
            try:
                for upload in uploads:
                    validate_portfolio_file(upload)
            except ValidationError as error:
                form.add_error("files", error)
            else:
                with transaction.atomic():
                    project = form.save(commit=False)
                    project.resume = resume
                    project.save()
                    for upload in uploads:
                        PortfolioAttachment.objects.create(
                            project=project,
                            file=upload,
                            original_name=Path(upload.name).name,
                        )
                messages.success(request, "Проєкт додано до резюме.")
                return redirect("resume_edit", resume_id=resume.pk)
    return render(request, "portfolio_project_form.html", {"form": form, "resume": resume})


@login_required
@require_POST
def project_delete(request, project_id):
    project = get_object_or_404(
        PortfolioProject.objects.filter(resume__user=request.user), pk=project_id
    )
    resume_id = project.resume_id
    for attachment in project.attachments.all():
        attachment.file.delete(save=False)
    project.delete()
    return redirect("resume_edit", resume_id=resume_id)


@login_required
@require_POST
def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(
        PortfolioAttachment.objects.filter(project__resume__user=request.user),
        pk=attachment_id,
    )
    resume_id = attachment.project.resume_id
    attachment.file.delete(save=False)
    attachment.delete()
    return redirect("resume_edit", resume_id=resume_id)


@login_required
@require_POST
def attachment_replace(request, attachment_id):
    attachment = get_object_or_404(
        PortfolioAttachment.objects.filter(project__resume__user=request.user),
        pk=attachment_id,
    )
    replacement = request.FILES.get("file")
    if not replacement:
        messages.error(request, "Оберіть файл для заміни.")
        return redirect("resume_edit", resume_id=attachment.project.resume_id)
    try:
        validate_portfolio_file(replacement)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect("resume_edit", resume_id=attachment.project.resume_id)
    resume_id = attachment.project.resume_id
    attachment.file.delete(save=False)
    attachment.file = replacement
    attachment.original_name = Path(replacement.name).name
    attachment.save(update_fields=["file", "original_name"])
    return redirect("resume_edit", resume_id=resume_id)


@login_required
def attachment_download(request, attachment_id):
    attachment = get_object_or_404(
        PortfolioAttachment.objects.filter(project__resume__user=request.user),
        pk=attachment_id,
    )
    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=Path(attachment.original_name).name,
    )
