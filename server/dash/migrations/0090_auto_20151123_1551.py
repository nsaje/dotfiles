# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0089_scheduledexportreportlog_recipient_emails'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduledexportreportlog',
            name='report',
        ),
        migrations.AlterField(
            model_name='scheduledexportreportlog',
            name='state',
            field=models.IntegerField(default=2, choices=[(2, b'Failed'), (1, b'Success')]),
        ),
    ]
