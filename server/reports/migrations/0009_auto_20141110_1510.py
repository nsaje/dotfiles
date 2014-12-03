# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20141001_1501'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlestats',
            options={'permissions': (('yesterday_spend_view', 'Can view yesterday spend column.'), ('per_day_sheet_source_export', 'Has Per-Day Report sheet in Excel source export.'))},
        ),
    ]
