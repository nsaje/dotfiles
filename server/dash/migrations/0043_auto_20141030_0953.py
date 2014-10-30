# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0042_auto_20141023_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroup',
            options={'ordering': ('name',)},
        ),
    ]
