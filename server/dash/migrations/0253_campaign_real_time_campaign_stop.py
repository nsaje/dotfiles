# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-27 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0252_auto_20171116_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='real_time_campaign_stop',
            field=models.BooleanField(default=False),
        ),
    ]
