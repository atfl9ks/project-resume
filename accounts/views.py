from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.db import transaction
from django.db import models
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import hashlib
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import EmailLoginForm, PendingEmailChangeForm, PortfolioProjectForm, ProfileForm, RegistrationForm, ResumeForm
from .models import EmailVerification, PortfolioAttachment, PortfolioProject, Resume
from .email_verification import send_verification
from .validators import validate_avatar, validate_portfolio_file


def home(request):
    return render(request, "index.html")


def privacy_policy(request):
    return render(request, "privacy.html")


def help_page(request):
    faq = [
        ("Початок роботи", "Як зареєструватися на сайті?", "Натисніть «Створити резюме», заповніть ім’я, email і пароль та надішліть форму."),
        ("Початок роботи", "Як підтвердити електронну пошту?", "Відкрийте лист і натисніть посилання підтвердження. Воно дійсне 24 години. Перевірте папку «Спам» або повторно надішліть лист."),
        ("Початок роботи", "Як увійти в особистий кабінет?", "Натисніть «Увійти» та введіть зареєстровані email і пароль. Спершу потрібно підтвердити адресу."),
        ("Початок роботи", "Як відновити пароль?", "Автоматичне відновлення наразі недоступне. Зверніться до підтримки з адреси, прив’язаної до акаунта."),
        ("Створення резюме", "Як створити нове резюме?", "На головній оберіть шаблон і натисніть «Створити з цим шаблоном». Увійдіть або зареєструйтеся, якщо з’явиться запит."),
        ("Створення резюме", "Як правильно заповнити інформацію?", "Укажіть актуальні контакти, бажану посаду та короткий профіль. Опишіть завдання, власні дії й результати. Необов’язкові поля можна пропустити."),
        ("Створення резюме", "Як додати освіту?", "У блоці «Освіта» додайте запис із рівнем, закладом, спеціальністю, роками та статусом."),
        ("Створення резюме", "Як додати досвід роботи?", "Додайте окремий запис на кожне місце роботи: посаду, роботодавця, період і результати."),
        ("Створення резюме", "Як додати навички та мови?", "Додайте навички з категоріями й рівнями. Для кожної мови вкажіть рівень володіння."),
        ("Створення резюме", "Як додати проєкти та портфоліо?", "Після збереження відкрийте резюме та додайте проєкт, опис, посилання на демо або репозиторій і файли."),
        ("Шаблони", "Чим відрізняються чотири шаблони?", "Classic послідовно показує кар’єру; Modern має дві колонки; Minimal зосереджений на змісті; Creative виділяє проєкти й індивідуальність."),
        ("Шаблони", "Як вибрати шаблон?", "Classic пасує консервативним компаніям, Modern — IT і бізнесу, Minimal — лаконічній подачі, Creative — творчим ролям."),
        ("Шаблони", "Як подивитися попередній варіант?", "На картці шаблону натисніть «Переглянути»."),
        ("Шаблони", "Як перемикатися між шаблонами?", "Відредагуйте резюме та змініть поле шаблону. Дані збережуться, зміниться їхнє оформлення."),
        ("Збереження та експорт", "Як зберегти резюме?", "У формі натисніть кнопку збереження та дочекайтеся сторінки перегляду."),
        ("Збереження та експорт", "Як завантажити PDF?", "На сторінці перегляду натисніть «Друк / PDF» і виберіть «Зберегти як PDF»."),
        ("Збереження та експорт", "Чому PDF виглядає некоректно?", "У вікні друку виберіть A4, стандартні поля та дочекайтеся завантаження шрифтів. Спробуйте інший браузер."),
        ("Збереження та експорт", "Як змінити створене резюме?", "В особистому кабінеті знайдіть резюме, натисніть «Редагувати» та збережіть зміни."),
        ("Профіль", "Як змінити аватар?", "У кабінеті натисніть «Завантажити аватар», виберіть фото, налаштуйте обрізання та збережіть. Підтримуються JPG, PNG, WEBP до 5 МБ."),
        ("Профіль", "Як змінити особисту інформацію?", "Відредагуйте поля профілю в кабінеті й натисніть «Зберегти зміни»."),
        ("Профіль", "Як змінити email?", "Змініть адресу в профілі. Нова адреса стане основною після підтвердження листом."),
        ("Вирішення проблем", "Не приходить лист підтвердження", "Перевірте адресу та папку «Спам», зачекайте кілька хвилин і повторно надішліть лист. Якщо не допоможе — зверніться до підтримки."),
        ("Вирішення проблем", "Не виходить увійти", "Перевірте email, пароль і підтвердження адреси. Відновлення пароля наразі недоступне — напишіть підтримці."),
        ("Вирішення проблем", "Не працює збереження", "Перевірте інтернет і обов’язкові поля, натисніть зберегти ще раз і дочекайтеся результату."),
        ("Вирішення проблем", "Не завантажується фотографія", "Використайте JPG, PNG або WEBP до 5 МБ. Спробуйте зменшити файл і завантажити його повторно."),
        ("Вирішення проблем", "Не відкривається PDF", "Завантажте документ через діалог друку або спробуйте інший PDF-переглядач."),
        ("Вирішення проблем", "Не зберігаються зміни", "Перевірте обов’язкові поля, підключення й акаунт. Повторно відкрийте редагування та збережіть форму."),
        ("Вирішення проблем", "Сайт некоректно відображається на телефоні", "Оновіть сторінку, встановіть масштаб 100%, спробуйте вертикальну орієнтацію або сучасний браузер."),
    ]
    return render(request, "help.html", {"faq": faq})


def help_page(request):
    faq = [
        ("Початок роботи", "Як зареєструватися на сайті?", "Натисніть «Створити резюме», заповніть ім’я, адресу електронної пошти та пароль, після чого надішліть форму."),
        ("Початок роботи", "Як підтвердити електронну пошту?", "Відкрийте лист від сервісу та натисніть посилання підтвердження. Воно дійсне 24 години. Якщо листа немає, перевірте «Спам» або повторно надішліть його зі сторінки підтвердження."),
        ("Початок роботи", "Як увійти в особистий кабінет?", "Перейдіть за кнопкою «Увійти» та вкажіть зареєстровану електронну пошту й пароль. Спочатку потрібно підтвердити email."),
        ("Початок роботи", "Як відновити пароль?", "Функція відновлення пароля поки недоступна. Зверніться до підтримки з адреси, пов’язаної з акаунтом, щоб отримати допомогу."),
        ("Створення резюме", "Як створити нове резюме?", "На головній оберіть шаблон і натисніть «Створити з цим шаблоном». Увійдіть або зареєструйтеся, якщо система попросить."),
        ("Створення резюме", "Як правильно заповнити інформацію?", "Укажіть актуальні контакти, бажану посаду та короткий профіль. Описуйте досвід конкретно: завдання, ваші дії й результати. Необов’язкові поля можна залишити порожніми."),
        ("Створення резюме", "Як додати освіту?", "У формі резюме знайдіть блок «Освіта», додайте запис і вкажіть рівень, заклад, спеціальність, роки та статус."),
        ("Створення резюме", "Як додати досвід роботи?", "У блоці досвіду додайте окремий запис для кожного місця роботи: посада, роботодавець, період і опис ваших результатів."),
        ("Створення резюме", "Як додати навички та мови?", "Додайте потрібні навички з категоріями й рівнями володіння. Для мов укажіть мову та рівень. Можна додати кілька записів."),
        ("Створення резюме", "Як додати проєкти та портфоліо?", "Збережіть резюме, відкрийте його перегляд і скористайтеся дією додавання проєкту. Додайте опис, посилання на демо чи репозиторій та файли."),
        ("Шаблони", "Чим відрізняються чотири шаблони?", "Classic подає послідовну професійну історію; Modern використовує дві колонки; Minimal зосереджений на змісті; Creative висуває на перший план проєкти й індивідуальність."),
        ("Шаблони", "Як вибрати підходящий шаблон?", "Для консервативних роботодавців оберіть Classic, для технологічних і бізнес-команд — Modern, для лаконічної подачі — Minimal, для творчих ролей — Creative."),
        ("Шаблони", "Як подивитися попередній варіант?", "На головній натисніть «Переглянути» на картці шаблону. На сторінці готового резюме відкрийте його перегляд."),
        ("Шаблони", "Як перемикатися між шаблонами?", "Відкрийте редагування резюме та виберіть інший шаблон. Дані резюме спільні, змінюється їхнє оформлення."),
        ("Збереження та експорт", "Як зберегти резюме?", "У формі натисніть кнопку збереження/перегляду. Після успішного збереження відкриється сторінка документа."),
        ("Збереження та експорт", "Як завантажити резюме у PDF?", "На сторінці перегляду натисніть «Друк / PDF», а в системному вікні друку виберіть «Зберегти як PDF»."),
        ("Збереження та експорт", "Чому PDF може відображатися некоректно?", "Перевірте документ у масштабі 100%, дочекайтеся завантаження шрифтів і виберіть формат A4 та стандартні поля у вікні друку. Спробуйте інший браузер, якщо макет усе ще зламаний."),
        ("Збереження та експорт", "Як змінити вже створене резюме?", "Відкрийте особистий кабінет, знайдіть резюме й натисніть «Редагувати». Збережіть зміни після редагування."),
        ("Профіль", "Як змінити аватар?", "В особистому кабінеті натисніть «Завантажити аватар», оберіть фото, налаштуйте кадрування та збережіть його. Підтримуються JPG, PNG і WEBP до 5 МБ."),
        ("Профіль", "Як змінити особисту інформацію?", "У кабінеті відкрийте блок профілю, відредагуйте поля й натисніть «Зберегти зміни»."),
        ("Профіль", "Як змінити електронну пошту?", "Відредагуйте email у профілі та збережіть. Нова адреса стане основною після переходу за листом підтвердження."),
        ("Вирішення проблем", "Не приходить лист підтвердження", "Перевірте адресу та папку «Спам», зачекайте кілька хвилин і скористайтеся повторним надсиланням. Якщо повідомлення не надходить, напишіть підтримці."),
        ("Вирішення проблем", "Не виходить увійти", "Переконайтеся, що email і пароль введено без зайвих пробілів, а пошту підтверджено. Відновлення пароля поки недоступне — у разі проблем зверніться до підтримки."),
        ("Вирішення проблем", "Не працює збереження", "Перевірте підключення до інтернету та обов’язкові поля, потім спробуйте ще раз. Не закривайте сторінку до повідомлення про результат."),
        ("Вирішення проблем", "Не завантажується фотографія", "Використайте JPG, PNG або WEBP розміром до 5 МБ. Спробуйте зменшити файл або вибрати його ще раз."),
        ("Вирішення проблем", "Не відкривається PDF", "Завантажте PDF через системний діалог друку. Якщо файл уже збережено, відкрийте його іншим PDF-переглядачем або завантажте повторно."),
        ("Вирішення проблем", "Не зберігаються зміни", "Перевірте обов’язкові поля, підключення та чи ви увійшли в потрібний акаунт. Повторно відкрийте редагування й збережіть форму."),
        ("Вирішення проблем", "Сайт некоректно виглядає на телефоні", "Оновіть сторінку, поверніть масштаб браузера до 100% та спробуйте вертикальну орієнтацію. Також можна відкрити сайт у сучасному браузері."),
    ]
    return render(request, "help.html", {"faq": faq})


def register(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.is_active = False
        user.email_verified = False
        user.save(update_fields=["is_active", "email_verified"])
        request.session["pending_verification_user_id"] = user.pk
        request.session["verification_sent_at"] = int(timezone.now().timestamp())
        request.session["verification_email_sent"] = False
        try:
            send_verification(user)
            request.session["verification_email_sent"] = True
            cache.set(f"verify-resend:{user.pk}:{request.META.get('REMOTE_ADDR', '')}", True, timeout=60)
            cache.set(f"verify-hourly:{user.pk}", 1, timeout=3600)
        except Exception:
            messages.error(request, "Акаунт створено, але лист не вдалося надіслати. Перевірте поштові налаштування та повторіть спробу.")
        return redirect("verify_pending")
    return render(request, "auth.html", {"form": form, "mode": "register"})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    form = EmailLoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        unverified = getattr(form, "unverified_user", None)
        if unverified:
            request.session["pending_verification_user_id"] = unverified.pk
            return redirect("verify_pending")
        login(request, form.user)
        messages.success(request, "Ви успішно увійшли.")
        return redirect("profile")
    return render(request, "auth.html", {"form": form, "mode": "login"})


def _pending_user(request):
    user_id = request.session.get("pending_verification_user_id")
    return UserModel.objects.filter(pk=user_id).filter(models.Q(email_verified=False) | ~models.Q(pending_email="")).first() if user_id else None


from django.contrib.auth import get_user_model
UserModel = get_user_model()


def verify_pending(request):
    user = _pending_user(request)
    if not user:
        return redirect("register")
    change_form = PendingEmailChangeForm(request.POST or None, user=user) if request.method == "POST" and request.POST.get("action") == "change_email" else PendingEmailChangeForm(user=user)
    sent_at = request.session.get("verification_sent_at", 0)
    remaining = max(0, 60 - (int(timezone.now().timestamp()) - sent_at)) if sent_at else 0
    return render(request, "verify_pending.html", {"user": user, "change_form": change_form, "resend_seconds": remaining, "email_sent": request.session.get("verification_email_sent", False)})


@require_POST
def resend_verification(request):
    user = _pending_user(request)
    if not user:
        messages.info(request, "Якщо акаунт очікує підтвердження, лист буде надіслано.")
        return redirect("login")
    throttle_key = f"verify-resend:{user.pk}:{request.META.get('REMOTE_ADDR', '')}"
    hourly_key = f"verify-hourly:{user.pk}"
    if not cache.add(throttle_key, True, timeout=60):
        messages.warning(request, "Зачекайте хвилину перед повторним надсиланням.")
        return redirect("verify_pending")
    count = cache.get(hourly_key, 0)
    if count >= 5:
        messages.warning(request, "Досягнуто ліміт надсилань. Спробуйте пізніше.")
        return redirect("verify_pending")
    cache.set(hourly_key, count + 1, timeout=3600)
    try:
        send_verification(user)
        request.session["verification_sent_at"] = int(timezone.now().timestamp())
        request.session["verification_email_sent"] = True
        messages.success(request, "Лист із посиланням надіслано повторно.")
    except Exception:
        messages.error(request, "Не вдалося надіслати лист. Перевірте поштові налаштування.")
        request.session["verification_email_sent"] = False
    return redirect("verify_pending")


def verify_email(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    verification = EmailVerification.objects.select_related("user").filter(token_hash=token_hash).first()
    if not verification:
        return render(request, "verify_result.html", {"state": "invalid"})
    if verification.used_at or verification.expires_at <= timezone.now():
        if not verification.used_at and not verification.user.email_verified:
            request.session["pending_verification_user_id"] = verification.user_id
        return render(request, "verify_result.html", {"state": "expired" if not verification.used_at else "invalid", "user": verification.user})
    with transaction.atomic():
        verification = EmailVerification.objects.select_for_update().select_related("user").get(pk=verification.pk)
        if verification.used_at or verification.expires_at <= timezone.now():
            return render(request, "verify_result.html", {"state": "invalid"})
        user = UserModel.objects.select_for_update().get(pk=verification.user_id)
        user.email = verification.email
        user.pending_email = ""
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email", "pending_email", "email_verified", "is_active"])
        verification.used_at = timezone.now()
        verification.save(update_fields=["used_at"])
        EmailVerification.objects.filter(user=user, used_at__isnull=True).exclude(pk=verification.pk).update(used_at=timezone.now())
    request.session["pending_verification_user_id"] = user.pk
    return render(request, "verify_result.html", {"state": "success", "user": user})


@require_POST
def change_pending_email(request):
    user = _pending_user(request)
    if not user:
        return redirect("login")
    form = PendingEmailChangeForm(request.POST, user=user)
    if form.is_valid():
        cooldown_key = f"verify-resend:{user.pk}:{request.META.get('REMOTE_ADDR', '')}"
        hourly_key = f"verify-hourly:{user.pk}"
        if not cache.add(cooldown_key, True, timeout=60) or cache.get(hourly_key, 0) >= 5:
            messages.warning(request, "Зачекайте перед наступним надсиланням листа.")
            return redirect("verify_pending")
        cache.set(hourly_key, cache.get(hourly_key, 0) + 1, timeout=3600)
        user.pending_email = form.cleaned_data["email"]
        user.save(update_fields=["pending_email"])
        try:
            send_verification(user, user.pending_email)
            messages.success(request, "Надіслали лист на нову адресу.")
        except Exception:
            messages.error(request, "Не вдалося надіслати лист. Перевірте поштові налаштування.")
    else:
        messages.error(request, "Перевірте нову адресу та поточний пароль.")
    return redirect("verify_pending")


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Ви вийшли з акаунта.")
    return redirect("home")


@login_required
def profile(request):
    original_email = request.user.email
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        requested_email = form.cleaned_data["email"].strip().lower()
        email_changed = requested_email != original_email.lower()
        if email_changed:
            form.cleaned_data["email"] = original_email
            form.instance.email = original_email
        form.save()
        if email_changed:
            request.user.pending_email = requested_email
            request.user.save(update_fields=["pending_email"])
            request.session["pending_verification_user_id"] = request.user.pk
            cooldown_key = f"verify-resend:{request.user.pk}:{request.META.get('REMOTE_ADDR', '')}"
            hourly_key = f"verify-hourly:{request.user.pk}"
            if not cache.add(cooldown_key, True, timeout=60) or cache.get(hourly_key, 0) >= 5:
                messages.warning(request, "Зачекайте перед наступним надсиланням листа.")
                return redirect("verify_pending")
            cache.set(hourly_key, cache.get(hourly_key, 0) + 1, timeout=3600)
            try:
                send_verification(request.user, requested_email)
                request.session["verification_sent_at"] = int(timezone.now().timestamp())
                messages.info(request, "Інші зміни збережено. Підтвердіть нову адресу за посиланням у листі.")
            except Exception:
                messages.error(request, "Зміни профілю збережено, але лист не надіслано. Повторіть спробу пізніше.")
            return redirect("profile")
        messages.success(request, "Профіль оновлено.")
        return redirect("profile")
    return render(request, "profile.html", {
        "form": form,
        "resumes": request.user.resumes.order_by("-updated_at"),
    })


def _avatar_initial(user):
    return (user.first_name or user.display_name or user.username or "?")[0].upper()


@login_required
@require_POST
def avatar_update(request):
    """Update only the authenticated user's avatar and return its URL."""
    user = request.user
    previous_name = user.avatar.name if user.avatar else ""
    previous_storage = user.avatar.storage if user.avatar else None
    if request.POST.get("action") == "delete":
        if previous_name:
            previous_storage.delete(previous_name)
            user.avatar = None
            user.save(update_fields=["avatar"])
        return JsonResponse({"ok": True, "avatar_url": "", "initial": _avatar_initial(user)})
    uploaded = request.FILES.get("avatar")
    if not uploaded:
        return JsonResponse({"ok": False, "error": "Оберіть файл зображення."}, status=400)
    try:
        validate_avatar(uploaded)
    except ValidationError as exc:
        return JsonResponse({"ok": False, "error": " ".join(exc.messages)}, status=400)
    user.avatar = uploaded
    user.save(update_fields=["avatar"])
    if previous_name and previous_name != user.avatar.name:
        previous_storage.delete(previous_name)
    return JsonResponse({"ok": True, "avatar_url": user.avatar.url, "initial": _avatar_initial(user)})


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
        "creative": "resumes/themes/creative.html",
    }
    theme_template = themes.get(resume.template)
    if not theme_template:
        raise Http404("Шаблон резюме не знайдено")
    return render(request, "resume_preview.html", {
        "resume": resume,
        "theme_template": theme_template,
        "compare_templates": list(themes.items()) if request.GET.get("compare") == "1" else None,
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
