# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0001_squashed_0061_auto_20141211_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
