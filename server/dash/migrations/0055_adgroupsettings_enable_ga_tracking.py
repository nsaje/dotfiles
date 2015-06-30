# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0054_contentad_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='enable_ga_tracking',
            field=models.BooleanField(default=True),
        ),
    ]
