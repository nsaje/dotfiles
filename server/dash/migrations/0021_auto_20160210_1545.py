# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20160201_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='autopilot_state',
            field=models.IntegerField(default=2, null=True, blank=True, choices=[(2, b'Disabled'), (1, b'Optimize Bid CPCs and Daily Budgets'), (3, b'Optimize Bid CPCs')]),
        ),
    ]
