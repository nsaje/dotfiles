# Generated by Django 2.1.11 on 2020-08-18 13:34

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dash", "0473_auto_20200814_0839")]

    operations = [
        migrations.AddField(
            model_name="adgroupsettings",
            name="exclusion_target_browsers",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, null=True, verbose_name="Excluded Browsers"
            ),
        )
    ]
