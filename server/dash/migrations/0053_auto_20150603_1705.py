# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0052_auto_20150602_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsource',
            name='last_successful_reports_sync_dt',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='last_successful_status_sync_dt',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
