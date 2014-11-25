# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0056_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='state',
            field=models.IntegerField(null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
    ]
