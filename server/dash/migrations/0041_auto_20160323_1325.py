# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0040_auto_20160322_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaigngoal',
            name='type',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'time on site in seconds'), (6, b'$CPM'), (4, b'$CPA'), (5, b'$CPC'), (3, b'pages per session'), (2, b'max bounce rate %'), (7, b'new visitors %')]),
        ),
    ]
