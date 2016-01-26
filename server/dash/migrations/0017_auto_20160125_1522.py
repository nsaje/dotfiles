# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0016_auto_20160125_1355'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='autopilot_daily_budget_cc',
            field=models.DecimalField(default=0, verbose_name=b'Auto-Pilots Daily Budget', max_digits=10, decimal_places=4),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='autopilot_state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
