# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0008_auto_20150909_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='autopilotadgroupsourcebidcpclog',
            name='yesterdays_clicks',
            field=models.IntegerField(null=True),
        ),
    ]
