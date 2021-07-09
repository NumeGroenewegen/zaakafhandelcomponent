# Generated by Django 2.2.24 on 2021-07-09 13:40

import datetime
import uuid

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("accounts", "0002_auto_20200406_0932"),
        ("accounts", "0003_auto_20200406_0934"),
        ("accounts", "0004_auto_20200406_0943"),
        ("accounts", "0005_auto_20200406_1018"),
        ("accounts", "0006_auto_20200429_0758"),
        ("accounts", "0007_auto_20200429_0759"),
        ("accounts", "0008_auto_20200429_0801"),
        ("accounts", "0009_auto_20200430_1500"),
        ("accounts", "0010_accessrequest"),
        ("accounts", "0011_auto_20200910_1219"),
        ("accounts", "0012_auto_20200917_0831"),
        ("accounts", "0013_auto_20200923_1219"),
        ("accounts", "0014_set_default_access_request_dates"),
        ("accounts", "0015_auto_20200923_1433"),
        ("accounts", "0013_auto_20200925_1038"),
        ("accounts", "0014_auto_20201005_1044"),
        ("accounts", "0016_merge_20201006_1355"),
        ("accounts", "0017_informatieobjecttypepermission"),
        ("accounts", "0018_auto_20201014_1509"),
        ("accounts", "0019_auto_20201016_1525"),
        ("accounts", "0013_auto_20200923_1432"),
        ("accounts", "0014_auto_20200923_1446"),
        ("accounts", "0015_auto_20200924_0907"),
        ("accounts", "0017_merge_20201006_1548"),
        ("accounts", "0018_auto_20201012_0818"),
        ("accounts", "0020_merge_20201021_1310"),
        ("accounts", "0021_auto_20210216_1529"),
        ("accounts", "0022_permissiondefinition"),
        ("accounts", "0023_auto_20210309_1810"),
        ("accounts", "0024_auto_20210317_1100"),
        ("accounts", "0025_migrate_to_permission_definitions"),
        ("accounts", "0026_auto_20210319_1158"),
        ("accounts", "0027_auto_20210325_1633"),
        ("accounts", "0028_migrate_to_blueprint_permission"),
        ("accounts", "0029_auto_20210325_1647"),
        ("accounts", "0030_auto_20210402_1007"),
        ("accounts", "0031_auto_20210603_0825"),
        ("accounts", "0032_auto_20210603_0827"),
        ("accounts", "0033_auto_20210603_0837"),
        ("accounts", "0034_auto_20210604_0826"),
        ("accounts", "0035_useratomicpermission_reason"),
        ("accounts", "0036_initial_permission_reason"),
        ("accounts", "0037_auto_20210625_1005"),
        ("accounts", "0038_migrate_atomic_permission_dates"),
        ("accounts", "0039_auto_20210625_1028"),
        ("accounts", "0040_deduplicate_atomic_permissions"),
        ("accounts", "0041_auto_20210625_1124"),
        ("accounts", "0042_remove_m2m_unique_constraint"),
        ("accounts", "0043_auto_20210701_1528"),
        ("accounts", "0044_deduplicate_blueprint_permissions"),
        ("accounts", "0045_auto_20210702_1240"),
        ("accounts", "0037_auto_20210706_1108"),
        ("accounts", "0046_merge_20210709_0903"),
        ("accounts", "0047_auto_20210709_1335"),
    ]

    dependencies = [
        ("accounts", "0001_initial"),
        ("zgw_consumers", "0012_auto_20210104_1039"),
        ("organisatieonderdelen", "0002_auto_20200923_1400"),
        ("activities", "0002_auto_20200805_1413"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthorizationProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("name", models.CharField(max_length=255, verbose_name="naam")),
            ],
            options={
                "verbose_name": "authorization profile",
                "verbose_name_plural": "authorization profiles",
            },
        ),
        migrations.AddField(
            model_name="user",
            name="auth_profiles",
            field=models.ManyToManyField(
                blank=True,
                through="accounts.UserEntitlement",
                to="accounts.Entitlement",
            ),
        ),
        migrations.CreateModel(
            name="UserAuthorizationProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "start",
                    models.DateTimeField(blank=True, null=True, verbose_name="start"),
                ),
                (
                    "end",
                    models.DateTimeField(blank=True, null=True, verbose_name="end"),
                ),
                (
                    "auth_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.Entitlement",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AccessRequest",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "zaak",
                    models.URLField(
                        help_text="URL reference to the zaak in its API",
                        max_length=1000,
                        verbose_name="zaak",
                    ),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True, max_length=1000, verbose_name="comment"
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        blank=True,
                        choices=[("approve", "approved"), ("reject", "rejected")],
                        max_length=50,
                        verbose_name="result",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="initiated_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "end_date",
                    models.DateField(blank=True, null=True, verbose_name="end date"),
                ),
                (
                    "start_date",
                    models.DateField(blank=True, null=True, verbose_name="start date"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="accessrequest",
            name="handler",
            field=models.ForeignKey(
                blank=True,
                help_text="user who has handled the request",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="handled_requests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="authorizationprofile",
            name="name",
            field=models.CharField(
                help_text="Use an easily recognizable name that maps to the function of users.",
                max_length=255,
                verbose_name="naam",
            ),
        ),
        migrations.AlterField(
            model_name="authorizationprofile",
            name="name",
            field=models.CharField(
                help_text="Use an easily recognizable name that maps to the function of users.",
                max_length=255,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Comment provided by the handler",
                max_length=1000,
                verbose_name="comment",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="end_date",
            field=models.DateField(
                blank=True,
                help_text="End date of the granted access",
                null=True,
                verbose_name="end date",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="result",
            field=models.CharField(
                blank=True,
                choices=[("approve", "approved"), ("reject", "rejected")],
                help_text="Result of the access request",
                max_length=50,
                verbose_name="result",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="start_date",
            field=models.DateField(
                blank=True,
                help_text="Start date of the granted access",
                null=True,
                verbose_name="start date",
            ),
        ),
        migrations.CreateModel(
            name="PermissionDefinition",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "object_type",
                    models.CharField(
                        choices=[("zaak", "zaak"), ("document", "document")],
                        help_text="Type of the objects this permission applies to",
                        max_length=50,
                        verbose_name="object type",
                    ),
                ),
                (
                    "permission",
                    models.CharField(
                        help_text="Name of the permission",
                        max_length=255,
                        verbose_name="Permission",
                    ),
                ),
                (
                    "object_url",
                    models.CharField(
                        blank=True,
                        help_text="URL of the object in one of ZGW APIs this permission applies to",
                        max_length=1000,
                        verbose_name="object URL",
                    ),
                ),
            ],
            options={
                "verbose_name": "permission definition",
                "verbose_name_plural": "permission definitions",
            },
        ),
        migrations.AddField(
            model_name="user",
            name="permission_definitions",
            field=models.ManyToManyField(
                limit_choices_to={"policy": {}},
                related_name="users",
                to="accounts.PermissionDefinition",
                verbose_name="permission definitions",
            ),
        ),
        migrations.CreateModel(
            name="BlueprintPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "object_type",
                    models.CharField(
                        choices=[("zaak", "zaak"), ("document", "document")],
                        help_text="Type of the objects this permission applies to",
                        max_length=50,
                        verbose_name="object type",
                    ),
                ),
                (
                    "permission",
                    models.CharField(
                        help_text="Name of the permission",
                        max_length=255,
                        verbose_name="Permission",
                    ),
                ),
                (
                    "policy",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        help_text="Blueprint permission definitions, used to check the access to objects based on their properties i.e. zaaktype, informatieobjecttype",
                        verbose_name="policy",
                    ),
                ),
            ],
            options={
                "verbose_name": "blueprint definition",
                "verbose_name_plural": "blueprint definitions",
            },
        ),
        migrations.AddField(
            model_name="authorizationprofile",
            name="blueprint_permissions",
            field=models.ManyToManyField(
                related_name="auth_profiles",
                to="accounts.BlueprintPermission",
                verbose_name="blueprint permissions",
            ),
        ),
        migrations.AlterField(
            model_name="permissiondefinition",
            name="object_url",
            field=models.CharField(
                help_text="URL of the object in one of ZGW APIs this permission applies to",
                max_length=1000,
                verbose_name="object URL",
            ),
        ),
        migrations.RenameModel(
            old_name="PermissionDefinition",
            new_name="AtomicPermission",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="permission_definitions",
            new_name="atomic_permissions",
        ),
        migrations.AlterField(
            model_name="user",
            name="atomic_permissions",
            field=models.ManyToManyField(
                related_name="users",
                to="accounts.AtomicPermission",
                verbose_name="atomic permissions",
            ),
        ),
        migrations.AlterModelOptions(
            name="atomicpermission",
            options={
                "verbose_name": "atomic permission",
                "verbose_name_plural": "atomic permissions",
            },
        ),
        migrations.AlterField(
            model_name="atomicpermission",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("zaak", "zaak"),
                    ("document", "document"),
                    ("report", "report"),
                ],
                help_text="Type of the objects this permission applies to",
                max_length=50,
                verbose_name="object type",
            ),
        ),
        migrations.AlterField(
            model_name="blueprintpermission",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("zaak", "zaak"),
                    ("document", "document"),
                    ("report", "report"),
                ],
                help_text="Type of the objects this permission applies to",
                max_length=50,
                verbose_name="object type",
            ),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="UserAtomicPermission",
                    fields=[
                        (
                            "id",
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "atomicpermission",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="accounts.AtomicPermission",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "accounts_user_atomic_permissions",
                    },
                ),
                migrations.AlterField(
                    model_name="user",
                    name="atomic_permissions",
                    field=models.ManyToManyField(
                        related_name="users",
                        through="accounts.UserAtomicPermission",
                        to="accounts.AtomicPermission",
                        verbose_name="atomic permissions",
                    ),
                ),
                migrations.AddField(
                    model_name="useratomicpermission",
                    name="user",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RenameField(
            model_name="useratomicpermission",
            old_name="atomicpermission",
            new_name="atomic_permission",
        ),
        migrations.AddField(
            model_name="accessrequest",
            name="user_atomic_permission",
            field=models.OneToOneField(
                blank=True,
                help_text="Permission created if the access request is approved",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="accounts.UserAtomicPermission",
            ),
        ),
        migrations.AddField(
            model_name="useratomicpermission",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Comment provided by the granter of the permission",
                max_length=1000,
                verbose_name="comment",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Comment provided by the requester",
                max_length=1000,
                verbose_name="comment",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="atomic_permissions",
            field=models.ManyToManyField(
                blank=True,
                related_name="users",
                through="accounts.UserAtomicPermission",
                to="accounts.AtomicPermission",
                verbose_name="atomic permissions",
            ),
        ),
        migrations.RenameField(
            model_name="accessrequest",
            old_name="start_date",
            new_name="requested_date",
        ),
        migrations.RenameField(
            model_name="accessrequest",
            old_name="end_date",
            new_name="handled_date",
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="handled_date",
            field=models.DateField(
                blank=True,
                help_text="Date when the access request was handled",
                null=True,
                verbose_name="end date",
            ),
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="requested_date",
            field=models.DateField(
                default=datetime.date.today,
                help_text="Date when the access request was created",
                verbose_name="requested date",
            ),
        ),
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
        migrations.AlterModelOptions(
            name="blueprintpermission",
            options={
                "ordering": ("policy__zaaktype_omschrijving", "permission"),
                "verbose_name": "blueprint definition",
                "verbose_name_plural": "blueprint definitions",
            },
        ),
        migrations.AddField(
            model_name="useratomicpermission",
            name="end_date",
            field=models.DateTimeField(
                blank=True,
                help_text="End date of the permission",
                null=True,
                verbose_name="end date",
            ),
        ),
        migrations.AddField(
            model_name="useratomicpermission",
            name="start_date",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text="Start date of the permission",
                verbose_name="start date",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="atomicpermission",
            unique_together={("permission", "object_url")},
        ),
        migrations.AlterModelOptions(
            name="blueprintpermission",
            options={
                "ordering": ("policy__zaaktype_omschrijving", "permission"),
                "verbose_name": "blueprint permission",
                "verbose_name_plural": "blueprint permissions",
            },
        ),
        migrations.AlterField(
            model_name="userauthorizationprofile",
            name="start",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="start"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="blueprintpermission",
            unique_together={("permission", "policy")},
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(_negated=True, email=""),
                fields=("email",),
                name="filled_email_unique",
            ),
        ),
        migrations.AlterField(
            model_name="atomicpermission",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("zaak", "zaak"),
                    ("document", "document"),
                    ("search_report", "search report"),
                ],
                help_text="Type of the objects this permission applies to",
                max_length=50,
                verbose_name="object type",
            ),
        ),
        migrations.AlterField(
            model_name="blueprintpermission",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("zaak", "zaak"),
                    ("document", "document"),
                    ("search_report", "search report"),
                ],
                help_text="Type of the objects this permission applies to",
                max_length=50,
                verbose_name="object type",
            ),
        ),
    ]
