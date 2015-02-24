# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_auto_20150220_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='bidder_slug',
            field=models.CharField(max_length=50, unique=True, null=True, verbose_name=b'B1 Slug'),
            preserve_default=True,
        ),
    ]
