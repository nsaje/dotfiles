# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0012_auto_20150323_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupstats',
            name='data_cost_cc',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='data_cost_cc',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
