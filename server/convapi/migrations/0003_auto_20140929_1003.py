# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0002_auto_20140915_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rawgoalconversionstats',
            name='device_type',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='rawpostclickstats',
            name='device_type',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
