# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0019_auto_20160126_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='autopilot_state',
            field=models.IntegerField(default=2, null=True, blank=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
