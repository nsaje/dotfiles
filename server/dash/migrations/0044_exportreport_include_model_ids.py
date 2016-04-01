# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0043_adgroupsettings_landing_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportreport',
            name='include_model_ids',
            field=models.BooleanField(default=False),
        ),
    ]
