# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0002_autopilotlog'),
    ]

    operations = [
        migrations.RenameField(
            model_name='autopilotlog',
            old_name='comments',
            new_name='budget_comments',
        ),
        migrations.RenameField(
            model_name='autopilotlog',
            old_name='new_daily_budget_cc',
            new_name='new_daily_budget',
        ),
        migrations.RenameField(
            model_name='autopilotlog',
            old_name='previous_daily_budget_cc',
            new_name='previous_daily_budget',
        ),
        migrations.AddField(
            model_name='autopilotlog',
            name='autopilot_type',
            field=models.IntegerField(default=2, choices=[(2, b'Disabled'), (1, b'Optimize Bid CPCs and Daily Budgets'), (3, b'Optimize Bid CPCs')]),
        ),
        migrations.AddField(
            model_name='autopilotlog',
            name='cpc_comments',
            field=models.CharField(max_length=1024, null=True, blank=True),
        ),
    ]
