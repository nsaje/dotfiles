# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroupnetworksettings',
            options={'ordering': (b'-created_dt',), 'get_latest_by': b'created_dt'},
        ),
        migrations.AlterModelOptions(
            name='adgroupsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.RemoveField(
            model_name='adgroupnetworksettings',
            name='ad_group',
        ),
        migrations.RemoveField(
            model_name='adgroupnetworksettings',
            name='network',
        ),
    ]
