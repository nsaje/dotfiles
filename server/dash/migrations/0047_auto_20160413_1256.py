# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-13 12:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0046_sourcecredentials_sync_reports'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaignbudgetsettings',
            name='campaign',
        ),
        migrations.RemoveField(
            model_name='campaignbudgetsettings',
            name='created_by',
        ),
        migrations.AlterField(
            model_name='sourcecredentials',
            name='sync_reports',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='CampaignBudgetSettings',
        ),
    ]
