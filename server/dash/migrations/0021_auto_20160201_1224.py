# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20160126_1633'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adgroupsettings',
            old_name='autopilot_daily_budget_cc',
            new_name='autopilot_daily_budget',
        ),
    ]
