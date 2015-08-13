# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_auto_20150812_1526'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contentadgoalconversionstats',
            old_name='goal_conversions',
            new_name='conversions',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='bounced_visits',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='goal_value',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='new_visits',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='pageviews',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='total_time_on_site',
        ),
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='visits',
        ),
    ]
