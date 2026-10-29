from django.db import migrations


def map_old_templates(apps, schema_editor):
    Resume = apps.get_model("accounts", "Resume")
    Resume.objects.filter(template="creative").update(template="modern")
    Resume.objects.filter(template="professional").update(template="classic")


def restore_old_templates(apps, schema_editor):
    Resume = apps.get_model("accounts", "Resume")
    Resume.objects.filter(template="modern").update(template="creative")
    Resume.objects.filter(template="classic").update(template="professional")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_alter_resume_template_portfolioproject_and_more")]
    operations = [migrations.RunPython(map_old_templates, restore_old_templates)]
