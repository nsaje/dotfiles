# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0069_auto_20150908_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversionpixel',
            name='last_sync_dt',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
