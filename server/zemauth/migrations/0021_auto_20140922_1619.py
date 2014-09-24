# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0020_auto_20140916_0832'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': (('campaign_settings_view', 'Can view campaign settings in dashboard.'), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('help_view', 'Can view help popovers.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('postclick_metrics', 'Can view postclick metrics.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'))},
        ),
    ]
