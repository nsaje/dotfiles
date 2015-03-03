# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0021_auto_20150227_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='image_height',
            field=models.PositiveIntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contentad',
            name='image_width',
            field=models.PositiveIntegerField(null=True),
            preserve_default=True,
        ),
    ]
