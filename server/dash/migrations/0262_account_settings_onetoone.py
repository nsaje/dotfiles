# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-04 09:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0261_submissionfilter_created_dt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='settings',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='latest_for_entity', to='dash.AccountSettings'),
        ),
    ]
