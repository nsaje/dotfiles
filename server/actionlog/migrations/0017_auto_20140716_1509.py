# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import actionlog.models
import dash.models


def migrate_data(apps, schema_editor):
    action_logs = actionlog.models.ActionLog.objects.all()
    for action_log in action_logs:
        action_log.ad_group_source = dash.models.AdGroupSource.objects.get(id=action_log.ad_group_network.id)
        action_log.save()


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0016_auto_20140716_1507'),
        ('dash', '0021_auto_20140716_1508'),
    ]

    operations = [
        migrations.RunPython(migrate_data)
    ]
