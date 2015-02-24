# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0014_source_bidder_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentad',
            name='bidder_id',
        ),
        migrations.AlterField(
            model_name='contentadsource',
            name='source_state',
            field=models.IntegerField(default=2, null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
        migrations.AlterField(
            model_name='contentadsource',
            name='state',
            field=models.IntegerField(default=2, null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
