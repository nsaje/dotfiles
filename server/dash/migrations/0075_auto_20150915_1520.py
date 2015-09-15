# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0074_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adgroupsourcesettings',
            name='autopilot',
        ),
        migrations.AddField(
            model_name='adgroupsourcesettings',
            name='autopilot_state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
