# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_adgroupsettings'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adgroupsettings',
            old_name='budget_day_cc',
            new_name='daily_budget_cc',
        ),
        migrations.RenameField(
            model_name='adgroupnetworksettings',
            old_name='budget_day_cc',
            new_name='daily_budget_cc',
        ),
    ]
