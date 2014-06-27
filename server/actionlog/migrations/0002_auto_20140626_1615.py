# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action',
            field=models.CharField(max_length=100, choices=[(b'get_reports', b'Get reports'), (b'set_campaign_state', b'Stop campaign'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')]),
        ),
    ]
