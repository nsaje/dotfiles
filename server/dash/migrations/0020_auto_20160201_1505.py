# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0019_auto_20160201_1044'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='autopilot_daily_budget',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10, blank=True, null=True, verbose_name=b"Auto-Pilot's Daily Budget"),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='autopilot_state',
            field=models.IntegerField(default=2, null=True, blank=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
