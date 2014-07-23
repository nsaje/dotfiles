# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0002_auto_20140716_2233'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroupsettings',
            options={'ordering': (b'-created_dt',), 'permissions': ((b'settings_view', b'Can view settings in dashboard.'),)},
        ),
    ]
