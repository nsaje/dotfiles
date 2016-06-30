# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-30 08:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0014_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autopilotlog',
            name='autopilot_type',
            field=models.IntegerField(choices=[(2, b'Disabled'), (1, b'Optimize Bids and Daily Budgets'), (3, b'Optimize Bids')], default=2),
        ),
    ]
