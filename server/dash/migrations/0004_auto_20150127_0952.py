# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0003_source_tracking_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='tracking_slug',
            field=models.CharField(max_length=50, unique=True, null=True, verbose_name=b'Tracking slug'),
        ),
    ]
