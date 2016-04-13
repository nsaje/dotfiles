# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0006_auto_20160325_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='autopilotlog',
            name='goal_value',
            field=models.DecimalField(null=True, verbose_name=b"Goal's value", max_digits=10, decimal_places=4, blank=True),
        ),
    ]
