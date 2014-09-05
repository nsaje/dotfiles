# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_auto_20140903_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlestats',
            name='has_conversion_metrics',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='goalconversionstats',
            name='has_conversion_metrics',
        ),
    ]
