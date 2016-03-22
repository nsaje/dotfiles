# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0037_auto_20160321_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='system_user',
            field=models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, b'Campaign Stop')]),
        ),
    ]
