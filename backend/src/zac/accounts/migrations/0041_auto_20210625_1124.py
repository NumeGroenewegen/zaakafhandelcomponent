# Generated by Django 2.2.19 on 2021-06-25 11:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0040_deduplicate_atomic_permissions"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="atomicpermission",
            unique_together={("permission", "object_url")},
        ),
    ]