# Generated by Django 2.1.11 on 2020-01-22 10:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0230_auto_20191212_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sspd_sources_markets',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
