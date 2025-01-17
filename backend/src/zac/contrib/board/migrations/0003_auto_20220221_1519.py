# Generated by Django 2.2.25 on 2022-02-21 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("board", "0002_auto_20210825_1537"),
    ]

    operations = [
        migrations.AlterField(
            model_name="boarditem",
            name="object",
            field=models.URLField(
                db_index=True,
                help_text="URL-reference of the OBJECT in one of ZGW APIs this board item relates to",
                verbose_name="object",
            ),
        ),
    ]
