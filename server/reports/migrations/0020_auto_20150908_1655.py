# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0019_auto_20150826_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='date',
            field=models.DateField(verbose_name=b'Report date'),
        ),
    ]
