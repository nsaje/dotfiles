# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0042_auto_20160325_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='landing_mode',
            field=models.BooleanField(default=False),
        ),
    ]
