# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_auto_20150219_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentadsource',
            name='source_state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
            preserve_default=True,
        ),
    ]
