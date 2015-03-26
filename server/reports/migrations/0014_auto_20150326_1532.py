# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_auto_20150326_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupstats',
            name='data_cost_cc',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='data_cost_cc',
            field=models.IntegerField(default=0),
        ),
    ]
