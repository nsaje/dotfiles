# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_uploadbatch_num_errors'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='state',
            field=models.IntegerField(default=1, null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
            preserve_default=True,
        ),
    ]
