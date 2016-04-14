# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0045_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adgroupsourcesettings',
            name='autopilot_state',
        ),
    ]
