# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_auto_20150220_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='status',
            field=models.IntegerField(default=3, choices=[(2, b'Failed'), (1, b'Done'), (3, b'In progress')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='contentadsource',
            name='source_state',
            field=models.IntegerField(default=2, choices=[(1, b'Running'), (2, b'Paused')]),
        ),
        migrations.AlterField(
            model_name='contentadsource',
            name='state',
            field=models.IntegerField(default=2, choices=[(1, b'Running'), (2, b'Paused')]),
        ),
    ]
