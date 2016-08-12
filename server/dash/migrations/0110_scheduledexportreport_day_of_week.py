# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-12 08:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0109_time_period_data_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledexportreport',
            name='day_of_week',
            field=models.IntegerField(choices=[(1, b'Monday'), (2, b'Tuesday'), (5, b'Friday'), (3, b'Wednesday'), (4, b'Thursday'), (7, b'Sunday'), (6, b'Saturday')], default=1),
        ),
    ]
