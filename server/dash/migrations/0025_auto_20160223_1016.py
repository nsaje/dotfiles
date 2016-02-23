# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0024_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadbatch',
            name='status',
            field=models.IntegerField(default=3, choices=[(2, b'Failed'), (1, b'Done'), (4, b'Cancelled'), (3, b'In progress')]),
        ),
    ]
