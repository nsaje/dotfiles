# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_auto_20140716_2233'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlestats',
            options={'permissions': ((b'yesterday_spend_view', b'Can view yesterday spend column.'),)},
        ),
    ]
