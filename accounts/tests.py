import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PortfolioAttachment, PortfolioProject, Resume


class AccountFlowTests(TestCase):
    def test_registration_creates_user_and_starts_session(self):
        response = self.client.post(reverse("register"), {
            "username": "olena", "display_name": "Olena Koval", "email": "olena@example.com",
            "password1": "Safe-pass-482!", "password2": "Safe-pass-482!",
        })
        self.assertRedirects(response, reverse("profile"))
        user = get_user_model().objects.get(email="olena@example.com")
        self.assertTrue(user.check_password("Safe-pass-482!"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_and_username_are_rejected(self):
        User = get_user_model()
        User.objects.create_user(username="existing", email="taken@example.com", display_name="Existing", password="Safe-pass-482!")
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
        User.objects.create_user(username="olena", email="olena@example.com", display_name="Olena", password="Safe-pass-482!")
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
            "template": "developer",
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
            reverse("resume_create") + "?template=developer",
            self.resume_data(),
        )
        resume = Resume.objects.get(user=self.user)
        self.assertRedirects(response, reverse("resume_preview", args=[resume.pk]))
        preview = self.client.get(reverse("resume_preview", args=[resume.pk]))
        self.assertContains(preview, "resume-theme-developer")
        self.assertContains(preview, "TECH STACK")
        self.assertContains(preview, "Python, Django, SQL")

    def test_all_four_saved_templates_render_their_own_layout(self):
        expected_classes = {
            "classic": "cv-classic",
            "modern": "cv-modern",
            "minimal": "cv-minimal",
            "developer": "cv-developer",
        }
        for slug, layout_class in expected_classes.items():
            with self.subTest(template=slug):
                resume = Resume.objects.create(
                    user=self.user,
                    **self.resume_data(template=slug),
                )
                response = self.client.get(reverse("resume_preview", args=[resume.pk]))
                self.assertContains(response, layout_class)

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
