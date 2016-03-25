# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0005_auto_20160323_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autopilotlog',
            name='campaign_goal',
            field=models.IntegerField(default=None, null=True, blank=True, choices=[(1, b'time on site in seconds'), (4, b'$CPA'), (5, b'$CPC'), (3, b'pages per session'), (2, b'max bounce rate %'), (7, b'new visitors %')]),
        ),
    ]
