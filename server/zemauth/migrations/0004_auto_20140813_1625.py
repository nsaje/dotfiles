# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0003_auto_20140813_1623'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': ((b'campaign_settings_view', b'Can view campaign settings in dashboard.'), (b'campaign_settings_account_manager', b'Can be chosen as account manager.'), (b'campaign_settings_sales_rep', b'Can be chosen as sales representative.'))},
        ),
    ]
