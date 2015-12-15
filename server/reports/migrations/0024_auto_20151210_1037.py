# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0023_auto_20151207_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentadgoalconversionstats',
            name='goal_type',
            field=models.SlugField(default=b'ga', max_length=15, choices=[(b'ga', b'Google Analytics'), (b'omniture', b'Adobe Analytics')]),
        ),
    ]
