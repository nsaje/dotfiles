# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_auto_20150225_1353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='bidder_slug',
            field=models.CharField(max_length=50, unique=True, null=True, verbose_name=b'B1 Slug', blank=True),
        ),
    ]
