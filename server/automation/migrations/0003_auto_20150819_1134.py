# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0002_auto_20150819_1127'),
    ]

    operations = [
        migrations.RenameField(
            model_name='CampaignBudgetDepletionNotifaction',
            old_name='yesterdays_spendt',
            new_name='yesterdays_spend',
        ),
    ]
