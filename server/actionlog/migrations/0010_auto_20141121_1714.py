# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0009_auto_20141117_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action',
            field=models.CharField(db_index=True, max_length=100, choices=[(b'get_reports', b'Get reports'), (b'set_campaign_state', b'Set campaign state'), (b'set_property', b'Set property'), (b'create_campaign', b'Create campaign'), (b'get_campaign_status', b'Get campaign status')]),
        ),
    ]
