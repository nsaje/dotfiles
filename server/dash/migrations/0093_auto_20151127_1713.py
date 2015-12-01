# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0092_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exportreport',
            name='filtered_sources',
            field=models.ManyToManyField(to='dash.Source', blank=True),
        ),
        migrations.AlterField(
            model_name='scheduledexportreport',
            name='state',
            field=models.IntegerField(default=1, choices=[(2, b'Paused'), (1, b'Enabled'), (3, b'Removed')]),
        ),
    ]
