# Generated by Django 2.2.12 on 2020-06-09 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("advices", "0002_documentadvice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentadvice",
            name="advice_version",
            field=models.PositiveSmallIntegerField(verbose_name="advice version"),
        ),
    ]