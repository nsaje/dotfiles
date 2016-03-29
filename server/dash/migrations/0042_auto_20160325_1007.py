# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0041_auto_20160323_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsourcesettings',
            name='system_user',
            field=models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, b'Campaign Stop')]),
        ),
        migrations.AlterField(
            model_name='campaigngoal',
            name='type',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'time on site in seconds'), (4, b'$CPA'), (5, b'$CPC'), (3, b'pages per session'), (2, b'max bounce rate %'), (7, b'new visitors %')]),
        ),
    ]
