# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0009_autopilotadgroupsourcebidcpclog_yesterdays_clicks'),
    ]

    operations = [
        migrations.AddField(
            model_name='autopilotadgroupsourcebidcpclog',
            name='comments',
            field=models.CharField(max_length=1024, null=True, blank=True),
        ),
    ]
