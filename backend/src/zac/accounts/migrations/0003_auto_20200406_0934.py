# Generated by Django 2.2.5 on 2020-04-06 09:34

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_auto_20200406_0932"),
    ]

    operations = [
        migrations.AlterField(
            model_name="permissionset",
            name="permissions",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=list,
                size=None,
                verbose_name="permissions",
            ),
        ),
        migrations.AlterField(
            model_name="permissionset",
            name="zaaktype",
            field=models.URLField(
                blank=True,
                help_text="All permissions selected are scoped to this zaaktype. If left empty, this applies to all zaaktypen.",
                verbose_name="zaaktype",
            ),
        ),
    ]