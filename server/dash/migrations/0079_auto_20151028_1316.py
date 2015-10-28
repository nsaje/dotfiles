# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0078_useractionlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversionpixel',
            name='last_sync_dt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
