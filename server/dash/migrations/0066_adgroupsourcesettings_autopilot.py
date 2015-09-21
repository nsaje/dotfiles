# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_auto_20150909_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsourcesettings',
            name='autopilot',
            field=models.BooleanField(default=False),
        ),
    ]
