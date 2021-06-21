# Generated by Django 2.2.19 on 2021-06-11 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0034_auto_20210604_0826"),
    ]

    operations = [
        migrations.AddField(
            model_name="useratomicpermission",
            name="reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("betrokkene", "betrokkene"),
                    ("toegang verlenen", "toegang verlenen"),
                    ("activiteit", "activiteit"),
                    ("adviseur", "adviseur"),
                    ("accordeur", "accordeur"),
                ],
                help_text="The reason why the permission was granted to the user",
                max_length=50,
                verbose_name="reason",
            ),
        ),
    ]