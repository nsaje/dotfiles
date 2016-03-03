# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import timezone_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0026_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='budgets_tz',
            field=timezone_field.fields.TimeZoneField(default=b'America/New_York'),
        ),
    ]
