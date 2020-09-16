# Generated by Django 2.1.11 on 2020-09-14 08:53

import django.contrib.postgres.fields
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0481_auto_20200913_1804")]

    operations = [
        migrations.AddField(
            model_name="adgroupsettings",
            name="target_connection_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=24),
                blank=True,
                null=True,
                size=None,
                verbose_name="Connection Type",
            ),
        )
    ]
