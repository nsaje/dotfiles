# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0015_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': ((b'campaign_settings_view', b'Can view campaign settings in dashboard.'), (b'campaign_settings_account_manager', b'Can be chosen as account manager.'), (b'campaign_settings_sales_rep', b'Can be chosen as sales representative.'), (b'help_view', b'Can view help popovers.'), (b'supply_dash_link_view', b'Can view supply dash link.'), (b'ad_group_agency_tab_view', b"Can view ad group's agency tab."), (b'all_accounts_accounts_view', b"Can view all accounts's accounts tab."), (b'accounts_campaigns_view', b"Can view accounts's campaigns tab."), (b'accounts_agency_view', b"Can view accounts's agency tab."))},
        ),
    ]
