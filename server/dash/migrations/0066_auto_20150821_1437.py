# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_auto_20150820_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignsettings',
            name='campaign_goal',
            field=models.IntegerField(default=3, choices=[(5, b'pages per session'), (2, b'% bounce rate'), (3, b'new unique visitors'), (1, b'CPA'), (4, b'seconds time on site')]),
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='goal_quantity',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2),
        ),
    ]
