# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='campaignbudgetsettings',
            options={'ordering': ('-created_dt',), 'get_latest_by': 'created_dt'},
        ),
    ]
