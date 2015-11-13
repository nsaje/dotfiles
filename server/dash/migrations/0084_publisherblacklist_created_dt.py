# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0083_publisherblacklist_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='publisherblacklist',
            name='created_dt',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 6, 15, 17, 31, 659069), verbose_name=b'Created at', auto_now_add=True),
            preserve_default=False,
        ),
    ]
