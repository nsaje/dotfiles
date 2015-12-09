# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0096_auto_20151209_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='allowed_sources',
            field=models.ManyToManyField(to='dash.Source'),
        ),
    ]
