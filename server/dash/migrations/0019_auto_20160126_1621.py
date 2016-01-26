# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='autopilot_daily_budget_cc',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10, blank=True, null=True, verbose_name=b"Auto-Pilot's Daily Budget"),
        ),
    ]
