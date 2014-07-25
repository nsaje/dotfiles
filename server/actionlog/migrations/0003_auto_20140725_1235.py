# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0002_auto_20140716_2233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action',
            field=models.CharField(db_index=True, max_length=100, choices=[(b'get_reports', b'Get reports'), (b'set_campaign_state', b'Stop campaign'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')]),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='action_type',
            field=models.IntegerField(db_index=True, choices=[(1, b'Automatic'), (2, b'Manual')]),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='state',
            field=models.IntegerField(default=1, db_index=True, choices=[(-1, b'Failed'), (2, b'Success'), (3, b'Aborted'), (1, b'Waiting')]),
        ),
    ]
