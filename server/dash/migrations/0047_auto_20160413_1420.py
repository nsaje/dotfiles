# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0046_sourcecredentials_sync_reports'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourcecredentials',
            name='sync_reports',
            field=models.BooleanField(default=True),
        ),
    ]
