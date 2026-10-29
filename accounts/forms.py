from django import forms
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

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ця електронна пошта вже зареєстрована.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Це ім’я користувача вже зайняте.")
        return username


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
            self.user = authenticate(self.request, username=user.username if user else data["email"], password=data["password"])
            if self.user is None:
                raise forms.ValidationError("Перевірте електронну пошту та пароль.")
        return data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("display_name", "username", "email", "first_name", "last_name")
        labels = {"display_name": "Ім’я для профілю", "username": "Ім’я користувача", "email": "Електронна пошта", "first_name": "Ім’я", "last_name": "Прізвище"}


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["template", "full_name", "email", "phone", "location", "position", "summary", "experience", "education", "skills"]


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
