# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0004_auto_20150127_0952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='tracking_slug',
            field=models.CharField(unique=True, max_length=50, verbose_name=b'Tracking slug'),
        ),
    ]
