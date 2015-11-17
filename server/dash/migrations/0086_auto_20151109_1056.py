# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0085_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduledreport',
            name='filtered_sources',
        ),
        migrations.AddField(
            model_name='scheduledreport',
            name='filtered_sources',
            field=models.ManyToManyField(to='dash.Source'),
        ),
    ]
