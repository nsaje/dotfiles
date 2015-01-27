# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0002_auto_20150119_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='tracking_slug',
            field=models.SlugField(unique=True, null=True, verbose_name=b'Tracking slug'),
            preserve_default=True,
        ),
    ]
