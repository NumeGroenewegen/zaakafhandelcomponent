# Generated by Django 3.2.12 on 2022-07-10 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kadaster", "0004_auto_20201103_0831"),
    ]

    operations = [
        migrations.AlterField(
            model_name="kadasterconfig",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
