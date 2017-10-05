# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-04 15:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0242_auto_20170918_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='new_accounts_use_bcm_v2',
            field=models.BooleanField(default=False, help_text=b"New accounts created by this agency's users will have license fee and margin included into all costs.", verbose_name=b'Margins v2'),
        ),
        migrations.AlterField(
            model_name='account',
            name='uses_bcm_v2',
            field=models.BooleanField(default=False, help_text=b'This account will have license fee and margin included into all costs.', verbose_name=b'Margins v2'),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Account'),
        ),
    ]
