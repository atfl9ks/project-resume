import tempfile
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.core import mail
from django.utils import timezone
from django.urls import reverse
from PIL import Image

from .models import PortfolioAttachment, PortfolioProject, Resume
from .forms import ResumeForm


class AccountFlowTests(TestCase):
    def test_help_page_and_footer_links(self):
        from django.urls import reverse
        home = self.client.get(reverse("home"))
        self.assertContains(home, reverse("help"))
        self.assertContains(home, "mail.google.com/mail/?view=cm")
        help_response = self.client.get(reverse("help"))
        self.assertEqual(help_response.status_code, 200)
        self.assertContains(help_response, "Пошук за запитаннями")
        self.assertContains(help_response, "Як підтвердити електронну пошту?")
        self.assertContains(help_response, "Вирішення проблем")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_registration_requires_one_time_email_confirmation(self):
        response = self.client.post(reverse("register"), {
            "username": "verify-me", "display_name": "Test Person", "email": "verify@example.com",
            "password1": "Safe-pass-482!", "password2": "Safe-pass-482!",
        })
        self.assertRedirects(response, reverse("verify_pending"))
        user = get_user_model().objects.get(username="verify-me")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("text/html", mail.outbox[0].alternatives[0][1])
        import re
        token = re.search(r"/verify-email/([^/]+)/", mail.outbox[0].body).group(1)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 302)
        self.client.get(reverse("verify_email", args=[token]))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertEqual(self.client.get(reverse("verify_email", args=[token])).context["state"], "invalid")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_unverified_email_can_restart_registration(self):
        payload = {"username": "pending-a", "display_name": "First", "email": "retry@example.com", "password1": "Safe-pass-482!", "password2": "Safe-pass-482!"}
        self.client.post(reverse("register"), payload)
        first_token = __import__("re").search(r"/verify-email/([^/]+)/", mail.outbox[-1].body).group(1)
        payload.update(username="pending-b", display_name="Second")
        response = self.client.post(reverse("register"), payload)
        self.assertRedirects(response, reverse("verify_pending"))
        self.assertEqual(get_user_model().objects.filter(email="retry@example.com").count(), 1)
        user = get_user_model().objects.get(email="retry@example.com")
        self.assertEqual(user.username, "pending-b")
        self.assertFalse(user.is_active)
        self.assertEqual(self.client.get(reverse("verify_email", args=[first_token])).context["state"], "invalid")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_login_of_unverified_user_redirects_to_resend_page(self):
        user = get_user_model().objects.create_user(username="pending", email="pending@example.com", display_name="Pending", password="Safe-pass-482!", is_active=False, email_verified=False)
        response = self.client.post(reverse("login"), {"email": user.email, "password": "Safe-pass-482!"})
        self.assertRedirects(response, reverse("verify_pending"))
        self.assertEqual(self.client.get(reverse("verify_pending")).context["user"], user)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_expired_confirmation_is_reported(self):
        from .models import EmailVerification
        import hashlib
        import secrets
        user = get_user_model().objects.create_user(username="expired", email="expired@example.com", display_name="Expired", password="Safe-pass-482!", is_active=False, email_verified=False)
        raw = secrets.token_urlsafe(32)
        verification = EmailVerification.objects.create(user=user, email=user.email, token_hash=hashlib.sha256(raw.encode()).hexdigest(), expires_at=timezone.now() - timezone.timedelta(seconds=1))
        self.assertEqual(self.client.get(reverse("verify_email", args=[raw])).context["state"], "expired")
        self.assertFalse(verification.user.is_active)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_profile_email_change_waits_for_new_address_confirmation(self):
        import re
        user = get_user_model().objects.create_user(username="change-email", email="old@example.com", display_name="Account", password="Safe-pass-482!", email_verified=True)
        self.client.force_login(user)
        response = self.client.post(reverse("profile"), {"username": user.username, "display_name": user.display_name, "email": "new@example.com", "first_name": "", "last_name": ""})
        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual(user.email, "old@example.com")
        self.assertEqual(user.pending_email, "new@example.com")
        token = re.search(r"/verify-email/([^/]+)/", mail.outbox[-1].body).group(1)
        self.client.get(reverse("verify_email", args=[token]))
        user.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.email_verified)

    def test_registration_form_includes_live_password_meter_and_confirmation(self):
        registration_page = self.client.get(reverse("register"))
        self.assertContains(registration_page, "data-password-meter")
        self.assertContains(registration_page, "data-password-confirm")
        self.assertContains(registration_page, "data-registration-submit")
        home = self.client.get(reverse("home"))
        self.assertContains(home, "signupPasswordTools")

    def test_weak_or_predictable_passwords_are_rejected_on_the_server(self):
        for index, password in enumerate(("Password123!", "Abcdefg1!")):
            response = self.client.post(reverse("register"), {
                "username": f"weak{index}", "display_name": "Test Person",
                "email": f"weak{index}@example.com", "password1": password, "password2": password,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(get_user_model().objects.filter(username=f"weak{index}").exists())
            self.assertTrue(response.context["form"].errors.get("password1") or response.context["form"].errors.get("password2"))

    def test_password_categories_and_match_are_enforced_server_side(self):
        from .forms import RegistrationForm

        missing_category = RegistrationForm(data={
            "username": "needs-upper", "display_name": "Test Person", "email": "upper@example.com",
            "password1": "lowercase123!", "password2": "lowercase123!",
        })
        self.assertFalse(missing_category.is_valid())
        self.assertTrue(missing_category.errors.get("password1") or missing_category.errors.get("password2"))

        mismatch = RegistrationForm(data={
            "username": "mismatch", "display_name": "Test Person", "email": "mismatch@example.com",
            "password1": "Cobalt%River8Hawk", "password2": "Cobalt%River8Hawk2",
        })
        self.assertFalse(mismatch.is_valid())
        self.assertTrue(mismatch.errors.get("password2"))

    def test_privacy_policy_has_a_working_route_and_homepage_link(self):
        home = self.client.get(reverse("home"))
        self.assertContains(home, reverse("privacy_policy"))
        policy = self.client.get(reverse("privacy_policy"))
        self.assertEqual(policy.status_code, 200)
        self.assertContains(policy, "Політика конфіденційності")
        self.assertContains(policy, "hello@rezume.ua")
        self.assertContains(policy, "Законі України")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", PUBLIC_BASE_URL="http://testserver")
    def test_registration_creates_inactive_user_until_confirmation(self):
        response = self.client.post(reverse("register"), {
            "username": "olena", "display_name": "Olena Koval", "email": "olena@example.com",
            "password1": "Safe-pass-482!", "password2": "Safe-pass-482!",
        })
        self.assertRedirects(response, reverse("verify_pending"))
        user = get_user_model().objects.get(email="olena@example.com")
        self.assertTrue(user.check_password("Safe-pass-482!"))
        self.assertFalse(user.is_active)
        import re
        token = re.search(r"/verify-email/([^/]+)/", mail.outbox[-1].body).group(1)
        self.client.get(reverse("verify_email", args=[token]))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)

    def test_duplicate_email_and_username_are_rejected(self):
        User = get_user_model()
        User.objects.create_user(username="existing", email="taken@example.com", display_name="Existing", password="Safe-pass-482!", email_verified=True)
        duplicate_email = self.client.post(reverse("register"), {
            "username": "another", "display_name": "Another", "email": "taken@example.com",
            "password1": "Safe-pass-482!", "password2": "Safe-pass-482!",
        })
        self.assertContains(duplicate_email, "вже зареєстрована")
        duplicate_username = self.client.post(reverse("register"), {
            "username": "existing", "display_name": "Another", "email": "new@example.com",
            "password1": "Safe-pass-482!", "password2": "Safe-pass-482!",
        })
        self.assertContains(duplicate_username, "вже зайняте")

    def test_login_wrong_password_and_logout(self):
        User = get_user_model()
        User.objects.create_user(username="olena", email="olena@example.com", display_name="Olena", password="Safe-pass-482!", email_verified=True)
        bad = self.client.post(reverse("login"), {"email": "olena@example.com", "password": "wrong"})
        self.assertContains(bad, "Перевірте електронну пошту та пароль")
        good = self.client.post(reverse("login"), {"email": "olena@example.com", "password": "Safe-pass-482!"})
        self.assertRedirects(good, reverse("profile"))
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))

    def test_profile_requires_login_and_can_be_updated(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")
        user = get_user_model().objects.create_user(username="olena", email="olena@example.com", display_name="Olena", password="Safe-pass-482!")
        self.client.force_login(user)
        updated = self.client.post(reverse("profile"), {
            "username": "olena", "email": "olena@example.com", "display_name": "Olena New",
            "first_name": "Olena", "last_name": "Koval",
        })
        self.assertRedirects(updated, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual(user.display_name, "Olena New")


class AvatarTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=Path(self.media.name))
        self.settings_override.enable()
        User = get_user_model()
        self.user = User.objects.create_user(username="avatar-one", email="avatar-one@example.com", display_name="Olena", password="Safe-pass-482!")
        self.other = User.objects.create_user(username="avatar-two", email="avatar-two@example.com", display_name="Maksym", password="Safe-pass-482!")
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media.cleanup()

    def image_upload(self, color=(20, 120, 210)):
        output = BytesIO()
        Image.new("RGB", (80, 60), color).save(output, format="PNG")
        return SimpleUploadedFile("profile.png", output.getvalue(), content_type="image/png")

    def test_avatar_upload_survives_profile_reload_and_login(self):
        response = self.client.post(reverse("avatar_update"), {"avatar": self.image_upload()})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        saved_name = self.user.avatar.name
        self.assertTrue(Path(self.user.avatar.path).exists())
        self.client.logout()
        self.client.login(username="avatar-one", password="Safe-pass-482!")
        profile = self.client.get(reverse("profile"))
        self.assertContains(profile, saved_name)
        self.assertContains(profile, "data-avatar-image")

    def test_replacement_removes_previous_file_and_delete_restores_fallback(self):
        self.client.post(reverse("avatar_update"), {"avatar": self.image_upload()})
        self.user.refresh_from_db()
        previous_path = Path(self.user.avatar.path)
        response = self.client.post(reverse("avatar_update"), {"avatar": self.image_upload((190, 60, 100))})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(previous_path.exists())
        self.user.refresh_from_db()
        current_path = Path(self.user.avatar.path)
        self.assertTrue(current_path.exists())
        deleted = self.client.post(reverse("avatar_update"), {"action": "delete"})
        self.assertEqual(deleted.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)
        self.assertFalse(current_path.exists())

    def test_invalid_content_and_oversized_files_are_rejected(self):
        spoofed = SimpleUploadedFile("photo.png", b"this is not an image", content_type="image/png")
        self.assertEqual(self.client.post(reverse("avatar_update"), {"avatar": spoofed}).status_code, 400)
        oversized = SimpleUploadedFile("large.png", b"x" * (5 * 1024 * 1024 + 1), content_type="image/png")
        self.assertEqual(self.client.post(reverse("avatar_update"), {"avatar": oversized}).status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_each_account_can_only_change_its_own_avatar(self):
        self.client.post(reverse("avatar_update"), {"avatar": self.image_upload()})
        self.user.refresh_from_db()
        own_avatar = self.user.avatar.name
        self.client.force_login(self.other)
        self.client.post(reverse("avatar_update"), {"avatar": self.image_upload((190, 60, 100))})
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.avatar.name, own_avatar)
        self.assertNotEqual(self.user.avatar.name, self.other.avatar.name)


class ResumeAndPortfolioTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=Path(self.media.name))
        self.settings_override.enable()
        self.user = get_user_model().objects.create_user(
            username="resume-owner", email="owner@example.com",
            display_name="Resume Owner", password="Safe-pass-482!",
        )
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media.cleanup()

    def resume_data(self, **overrides):
        data = {
            "template": "modern",
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "+380000000000",
            "location": "Kyiv",
            "position": "Python Developer",
            "summary": "Backend developer",
            "experience": "Engineer, Example Co.",
            "education": "Computer Science",
            "skills": "Python, Django, SQL",
        }
        data.update(overrides)
        return data

    def test_selected_template_is_saved_and_preview_uses_its_layout(self):
        response = self.client.post(
            reverse("resume_create") + "?template=modern",
            self.resume_data(),
        )
        resume = Resume.objects.get(user=self.user)
        self.assertRedirects(response, reverse("resume_preview", args=[resume.pk]))
        preview = self.client.get(reverse("resume_preview", args=[resume.pk]))
        self.assertContains(preview, "resume-theme-modern")
        self.assertContains(preview, "modern-contact")
        self.assertContains(preview, "Python, Django, SQL")

    def test_all_saved_templates_render_their_own_layout(self):
        expected_classes = {
            "classic": ("cv-classic", "classic-header"),
            "modern": ("cv-modern", "modern-rail"),
            "minimal": ("cv-minimal", "minimal-section"),
            "creative": ("cv-creative", "creative-header"),
        }
        for slug, (layout_class, structure_marker) in expected_classes.items():
            with self.subTest(template=slug):
                resume = Resume.objects.create(
                    user=self.user,
                    **self.resume_data(template=slug),
                )
                response = self.client.get(reverse("resume_preview", args=[resume.pk]))
                self.assertContains(response, layout_class)
                self.assertContains(response, structure_marker)

    def test_every_theme_renders_the_shared_resume_content_and_hides_blank_sections(self):
        themes = [slug for slug, _label in Resume.TEMPLATE_CHOICES]
        optional_section_markers = {
            "classic": "classic-row",
            "modern": "modern-feature",
            "minimal": "minimal-section",
        }
        for slug in themes:
            with self.subTest(template=slug):
                resume = Resume.objects.create(
                    user=self.user,
                    **self.resume_data(
                        template=slug,
                        summary="Thoughtful product builder",
                        experience="Lead designer, Northstar",
                        education="MSc, Human Computer Interaction",
                        skills="Research, Prototyping, Figma",
                    ),
                )
                PortfolioProject.objects.create(
                    resume=resume,
                    title="Northstar dashboard",
                    description="A data product for small teams.",
                    technologies="Django, Figma",
                )
                response = self.client.get(reverse("resume_preview", args=[resume.pk]))
                for content in (
                    "Thoughtful product builder",
                    "Lead designer, Northstar",
                    "MSc, Human Computer Interaction",
                    "Research, Prototyping, Figma",
                    "Northstar dashboard",
                ):
                    self.assertContains(response, content)

        for slug in themes:
            with self.subTest(empty_template=slug):
                empty_resume = Resume.objects.create(
                    user=self.user,
                    **self.resume_data(
                        template=slug, summary="", experience="", education="", skills="",
                    ),
                )
                empty_preview = self.client.get(reverse("resume_preview", args=[empty_resume.pk]))
                self.assertNotContains(empty_preview, {"classic":"classic-row", "modern":"modern-feature", "minimal":"minimal-section", "creative":"creative-block"}[slug])
                self.assertNotContains(empty_preview, "cv-projects")

    def test_edit_keeps_resume_id_and_saves_template_switch(self):
        resume = Resume.objects.create(user=self.user, **self.resume_data())
        response = self.client.post(
            reverse("resume_edit", args=[resume.pk]),
            self.resume_data(template="modern", full_name="Ada Updated"),
        )
        self.assertRedirects(response, reverse("resume_preview", args=[resume.pk]))
        resume.refresh_from_db()
        self.assertEqual(resume.full_name, "Ada Updated")
        self.assertEqual(resume.template, "modern")

    def test_structured_resume_choices_persist_and_compare_is_screen_only(self):
        data = self.resume_data(template="creative")
        data.update({
            "education_level": "Магистратура", "experience_level": "3–5 лет",
            "work_format": "Удалённо", "employment_type": "Полная занятость",
            "seniority": "Senior", "salary_expectation": "5000 USD",
            "travel_ready": "on", "education_records": "Магистратура | КНУ | Информатика | 2020–2022 | Завершено",
            "language_records": "Английский | B2", "skill_records": "Программирование | Python | C1",
        })
        form = ResumeForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        resume = form.save(commit=False)
        resume.user = self.user
        resume.save()
        resume.refresh_from_db()
        self.assertEqual(resume.resume_details["education_records"][0]["school"], "КНУ")
        self.assertEqual(resume.resume_details["language_records"][0]["level"], "B2")
        preview = self.client.get(reverse("resume_preview", args=[resume.pk]) + "?compare=1")
        self.assertContains(preview, "compare-mode")
        self.assertContains(preview, "event.key.toLowerCase()")
        self.assertContains(preview, "5000 USD")

    def test_project_upload_and_private_download(self):
        resume = Resume.objects.create(user=self.user, **self.resume_data())
        upload = SimpleUploadedFile("notes.md", b"# Portfolio project\n", content_type="text/plain")
        image = SimpleUploadedFile("preview.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, content_type="image/png")
        response = self.client.post(
            reverse("project_add", args=[resume.pk]),
            {
                "title": "Open source tool",
                "description": "A useful project",
                "technologies": "Python, Django",
                "repository_url": "https://github.com/example/tool",
                "demo_url": "https://example.com/demo",
                "files": [upload, image],
            },
        )
        self.assertRedirects(response, reverse("resume_edit", args=[resume.pk]))
        project = PortfolioProject.objects.get(resume=resume)
        self.assertEqual(project.attachments.count(), 2)
        attachment = project.attachments.get(original_name="notes.md")
        preview = self.client.get(reverse("resume_preview", args=[resume.pk]))
        self.assertContains(preview, "Open source tool")
        self.assertContains(preview, "Python, Django")
        self.assertContains(preview, "notes.md")
        download = self.client.get(reverse("attachment_download", args=[attachment.pk]))
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.get("Content-Disposition", "").startswith("attachment;"), True)
        download.close()

        other = get_user_model().objects.create_user(
            username="other", email="other@example.com", display_name="Other",
            password="Safe-pass-482!",
        )
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("resume_preview", args=[resume.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("attachment_download", args=[attachment.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("project_delete", args=[project.pk])).status_code, 404)

    def test_executable_upload_is_rejected(self):
        resume = Resume.objects.create(user=self.user, **self.resume_data())
        executable = SimpleUploadedFile("run.exe", b"MZnot-an-allowed-file", content_type="application/octet-stream")
        response = self.client.post(
            reverse("project_add", args=[resume.pk]),
            {"title": "Bad upload", "files": [executable]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PortfolioProject.objects.filter(resume=resume).exists())
        self.assertContains(response, "Дозволені формати")
