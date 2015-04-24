# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0033_auto_20150420_0953'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourcetype',
            name='can_delete_traffic_metrics',
        ),
        migrations.AlterField(
            model_name='sourcetype',
            name='delete_traffic_metrics_threshold',
            field=models.IntegerField(default=0, help_text=b"When we receive an empty report, we don't override existing data but we mark report aggregation as failed. But for smaller changes (as defined by this parameter), we do override existing data since they are not material. Zero value means no reports will get deleted.", verbose_name=b'Max clicks allowed to delete per daily report'),
        ),
    ]
