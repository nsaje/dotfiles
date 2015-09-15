# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0071_remove_batch_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='adobe_tracking_param',
            field=models.CharField(default=b'', max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='enable_adobe_tracking',
            field=models.BooleanField(default=False),
        ),
    ]
