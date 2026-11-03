from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_map_legacy_resume_templates")]

    operations = [
        migrations.AlterField(
            model_name="resume",
            name="template",
            field=models.CharField(
                choices=[
                    ("classic", "Classic"),
                    ("modern", "Modern"),
                    ("minimal", "Minimal"),
                    ("creative", "Creative"),
                    ("professional", "Professional"),
                    ("executive", "Executive"),
                    ("developer", "Developer"),
                ],
                max_length=30,
            ),
        ),
    ]
