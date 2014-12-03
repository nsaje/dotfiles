# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0059_sourcetype_min_cpc'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='min_daily_budget',
            field=models.DecimalField(null=True, verbose_name=b'Minimum Daily Budget', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
    ]
