# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-21 07:55
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0285_merge_20180320_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='additional_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contentadcandidate',
            name='additional_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
