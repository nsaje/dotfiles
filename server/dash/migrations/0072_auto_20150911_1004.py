# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0071_remove_batch_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conversionpixel',
            name='last_verified_dt',
        ),
        migrations.RemoveField(
            model_name='conversionpixel',
            name='status',
        ),
    ]
