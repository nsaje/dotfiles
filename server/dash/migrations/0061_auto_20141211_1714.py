# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0060_sourcetype_min_daily_budget'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='max_cpc',
            field=models.DecimalField(null=True, verbose_name=b'Maximum CPC', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='max_daily_budget',
            field=models.DecimalField(null=True, verbose_name=b'Maximum Daily Budget', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
    ]
