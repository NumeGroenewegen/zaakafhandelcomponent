# Generated by Django 3.2.12 on 2022-05-25 07:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("checklists", "0007_auto_20220324_1616"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="checklist",
            name="group_assignee",
        ),
        migrations.RemoveField(
            model_name="checklist",
            name="user_assignee",
        ),
        migrations.AddField(
            model_name="checklistanswer",
            name="group_assignee",
            field=models.ForeignKey(
                blank=True,
                help_text="Group assigned to answer.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="auth.group",
                verbose_name="group assignee",
            ),
        ),
        migrations.AddField(
            model_name="checklistanswer",
            name="user_assignee",
            field=models.ForeignKey(
                blank=True,
                help_text="Person assigned to answer.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user assignee",
            ),
        ),
    ]
