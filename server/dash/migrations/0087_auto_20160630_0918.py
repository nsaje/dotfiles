# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-30 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0086_auto_20160630_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='autopilot_state',
            field=models.IntegerField(blank=True, choices=[(2, b'Disabled'), (1, b'Optimize Bids and Daily Budgets'), (3, b'Optimize Bids')], default=2, null=True),
        ),
    ]
