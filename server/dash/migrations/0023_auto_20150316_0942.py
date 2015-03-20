# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0022_auto_20150303_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='deprecated',
            field=models.BooleanField(default=False),
            preserve_default=True,
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
        migrations.AlterField(
            model_name='contentadsource',
            name='submission_status',
            field=models.IntegerField(default=1, choices=[(1, b'Pending'), (4, b'Limit reached'), (2, b'Approved'), (3, b'Rejected')]),
        ),
    ]
