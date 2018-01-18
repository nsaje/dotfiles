# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-17 13:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0266_account_real_time_campaign_stop'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='currency',
            field=models.CharField(choices=[(b'USD', b'US Dollar'), (b'EUR', b'Euro')], default=b'USD', max_length=3),
        ),
    ]
