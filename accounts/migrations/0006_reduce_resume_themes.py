from django.db import migrations, models


def normalize_removed_templates(apps, schema_editor):
    Resume = apps.get_model("accounts", "Resume")
    Resume.objects.filter(template__in=["developer", "executive"]).update(template="minimal")
    Resume.objects.filter(template="professional").update(template="classic")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_add_resume_themes")]
    operations = [
        migrations.RunPython(normalize_removed_templates, migrations.RunPython.noop),
        migrations.AlterField(model_name="resume", name="template", field=models.CharField(choices=[("classic", "Classic"), ("modern", "Modern"), ("minimal", "Minimal"), ("creative", "Creative")], max_length=30)),
    ]
