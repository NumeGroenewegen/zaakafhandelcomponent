# Generated by Django 2.2.16 on 2020-09-23 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_auto_20200917_0831"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessrequest",
            name="end_date",
            field=models.DateField(blank=True, null=True, verbose_name="end date"),
        ),
        migrations.AddField(
            model_name="accessrequest",
            name="start_date",
            field=models.DateField(blank=True, null=True, verbose_name="start date"),
        ),
    ]
