# Generated by Django 3.2.12 on 2022-08-24 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_coreconfig_zaaktype_attribute_object_type"),
    ]

    operations = [
        migrations.RenameField(
            model_name="coreconfig",
            old_name="zaaktype_attribute_object_type",
            new_name="zaaktype_attribute_objecttype",
        ),
        migrations.AddField(
            model_name="coreconfig",
            name="start_camunda_process_form_objecttype",
            field=models.URLField(
                default="",
                help_text="A URL-reference to the StartCamundaForms OBJECTTYPE. This is used to set the right variables for the camunda process related to the ZAAKTYPE.",
                verbose_name="URL-reference to StartCamundaForms in OBJECTTYPES API.",
            ),
        ),
    ]
