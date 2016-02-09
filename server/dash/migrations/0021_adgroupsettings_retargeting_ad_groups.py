# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20160201_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='retargeting_ad_groups',
            field=jsonfield.fields.JSONField(default=[], blank=True),
        ),
    ]
