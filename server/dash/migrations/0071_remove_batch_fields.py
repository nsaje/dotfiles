# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0070_conversionpixel_last_sync_dt'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uploadbatch',
            name='brand_name',
        ),
        migrations.RemoveField(
            model_name='uploadbatch',
            name='call_to_action',
        ),
        migrations.RemoveField(
            model_name='uploadbatch',
            name='description',
        ),
        migrations.RemoveField(
            model_name='uploadbatch',
            name='display_url',
        ),
    ]
