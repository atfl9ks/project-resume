from django import forms
import json
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import PortfolioProject, Resume

User = get_user_model()


class RegistrationForm(UserCreationForm):
    username = forms.CharField(label="Ім’я користувача", max_length=150)
    display_name = forms.CharField(label="Ваше ім’я", max_length=120)
    email = forms.EmailField(label="Електронна пошта")

    class Meta:
        model = User
        fields = ("username", "display_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({
            "data-password-input": "",
            "autocomplete": "new-password",
            "aria-describedby": "passwordStrengthHint passwordRequirements",
        })
        self.fields["password2"].widget.attrs.update({
            "data-password-confirm": "",
            "autocomplete": "new-password",
            "aria-describedby": "passwordMatchFeedback",
        })
        self.fields["password2"].label = "Повторіть пароль"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        self.pending_user = User.objects.filter(email__iexact=email, is_active=False).first()
        if User.objects.filter(email__iexact=email, is_active=True, email_verified=True).exists():
            raise forms.ValidationError("Ця електронна пошта вже зареєстрована.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        pending = User.objects.filter(email__iexact=self.data.get("email", "").strip(), is_active=False).first()
        if User.objects.filter(username__iexact=username).exclude(pk=pending.pk if pending else None).exists():
            raise forms.ValidationError("Це ім’я користувача вже зайняте.")
        return username

    def clean(self):
        cleaned = super().clean()
        # ModelForm's post-clean uniqueness check must validate against the
        # pending row itself, otherwise email(unique=True) rejects its retry.
        pending_user = getattr(self, "pending_user", None)
        if pending_user is not None:
            self.instance = pending_user
        return cleaned

    def save(self, commit=True):
        pending_user = getattr(self, "pending_user", None)
        if not pending_user:
            return super().save(commit=commit)
        pending_user.username = self.cleaned_data["username"]
        pending_user.display_name = self.cleaned_data["display_name"]
        pending_user.email = self.cleaned_data["email"]
        pending_user.set_password(self.cleaned_data["password1"])
        pending_user.is_active = False
        pending_user.email_verified = False
        if commit:
            pending_user.save()
        return pending_user


class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Електронна пошта")
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data.get("email") and data.get("password"):
            user = User.objects.filter(email__iexact=data["email"].strip()).first()
            self.unverified_user = None
            if user and user.check_password(data["password"]) and not user.email_verified:
                self.unverified_user = user
                return data
            self.user = authenticate(self.request, username=user.username if user else data["email"], password=data["password"])
            if self.user is None:
                raise forms.ValidationError("Перевірте електронну пошту та пароль.")
        return data


class PendingEmailChangeForm(forms.Form):
    email = forms.EmailField(label="Нова електронна пошта")
    password = forms.CharField(label="Поточний пароль", widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Ця адреса вже використовується.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Перевірте поточний пароль.")
        return password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("display_name", "username", "email", "first_name", "last_name")
        labels = {"display_name": "Ім’я для профілю", "username": "Ім’я користувача", "email": "Електронна пошта", "first_name": "Ім’я", "last_name": "Прізвище"}


class ResumeForm(forms.ModelForm):
    template = forms.ChoiceField(label="Шаблон резюме", choices=Resume.TEMPLATE_CHOICES, required=True)
    education_level = forms.ChoiceField(label="Рівень освіти", choices=[("", "Оберіть рівень"), *Resume.EDUCATION_CHOICES], required=False)
    experience_level = forms.ChoiceField(label="Досвід роботи", choices=[("", "Не вказувати"), *Resume.EXPERIENCE_CHOICES], required=False)
    work_format = forms.ChoiceField(label="Бажаний формат роботи", choices=[("", "Не вказувати"), *Resume.WORK_FORMAT_CHOICES], required=False)
    employment_type = forms.ChoiceField(label="Тип зайнятості", choices=[("", "Не вказувати"), *Resume.EMPLOYMENT_CHOICES], required=False)
    seniority = forms.ChoiceField(label="Бажаний рівень посади", choices=[("", "Не вказувати"), *Resume.LEVEL_CHOICES], required=False)
    salary_expectation = forms.CharField(label="Бажаний рівень оплати (необов’язково)", required=False)
    travel_ready = forms.BooleanField(label="Готовий/готова до відряджень", required=False)
    relocation_ready = forms.BooleanField(label="Готовий/готова до переїзду", required=False)
    driving_license = forms.BooleanField(label="Маю водійське посвідчення", required=False)
    education_records = forms.CharField(required=False, widget=forms.HiddenInput)
    experience_records = forms.CharField(required=False, widget=forms.HiddenInput)
    language_records = forms.CharField(required=False, widget=forms.HiddenInput)
    skill_records = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Resume
        fields = ["template", "full_name", "email", "phone", "location", "position", "summary", "experience", "education", "skills"]
        labels = {"full_name": "Ім’я та прізвище", "email": "Електронна пошта", "phone": "Телефон", "location": "Місто", "position": "Бажана посада", "summary": "Професійний профіль — кілька речень про ваш досвід і цілі"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        details = (self.instance.resume_details or {}) if self.instance and self.instance.pk else {}
        for key in ("experience_level", "work_format", "employment_type", "seniority", "salary_expectation", "travel_ready", "relocation_ready", "driving_license"):
            self.fields[key].initial = details.get(key, False if key in {"travel_ready", "relocation_ready", "driving_license"} else "")
        self.fields["education_level"].initial = details.get("education_level", "")
        records = {"education_records": details.get("education_records", []), "experience_records": self.instance.experience_records or [] if self.instance and self.instance.pk else [], "language_records": details.get("language_records", []), "skill_records": details.get("skill_records", [])}
        for key, value in records.items(): self.fields[key].initial = json.dumps(value, ensure_ascii=False)

    def clean(self):
        data = super().clean()
        record_fields = {
            "education_records": ("level", "school", "major", "years", "status"),
            "experience_records": ("position", "company", "years", "description"),
            "language_records": ("language", "level"),
            "skill_records": ("category", "skill", "level"),
        }
        for key, columns in record_fields.items():
            raw = self.data.get(key) or "[]"
            try:
                rows = json.loads(raw)
            except (TypeError, ValueError):
                # Accept the older one-record-per-line text format as well as
                # the JSON used by the structured editor.
                rows = []
                for line in str(raw).splitlines():
                    values = [part.strip() for part in line.split("|")]
                    if any(values):
                        rows.append({column: value for column, value in zip(columns, values) if value})
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise forms.ValidationError("Формат записів резюме некоректен.")
            data[key] = rows
        return data

    def save(self, commit=True):
        resume = super().save(commit=False)
        details = {}
        for key in ("education_level", "experience_level", "work_format", "employment_type", "seniority", "salary_expectation", "travel_ready", "relocation_ready", "driving_license"):
            details[key] = self.cleaned_data.get(key)
        for key in ("education_records", "language_records", "skill_records"): details[key] = self.cleaned_data.get(key, [])
        resume.experience_records = self.cleaned_data.get("experience_records", [])
        resume.resume_details = details
        if commit: resume.save()
        return resume


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [forms.FileField.clean(self, item, initial) for item in files]


class PortfolioProjectForm(forms.ModelForm):
    files = MultipleFileField(required=False, label="Файли проєкту")

    class Meta:
        model = PortfolioProject
        fields = ["title", "description", "technologies", "repository_url", "demo_url"]
