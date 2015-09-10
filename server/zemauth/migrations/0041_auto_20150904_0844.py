# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0040_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': (('campaign_settings_view', "Can view campaign's settings tab."), ('campaign_agency_view', "Can view campaign's agency tab."), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('help_view', 'Can view help popovers.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('campaign_sources_view', 'Can view campaign sources view.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('all_new_sidebar', 'Can see new sidebar.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('view_archived_entities', 'Can view archived entities.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('set_ad_group_source_settings', 'Can set per-source settings.'), ('see_current_ad_group_source_state', 'Can see current per-source state.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('new_content_ads_tab', 'Can view new content ads tab.'), ('filter_sources', 'Can filter sources'), ('upload_content_ads', 'Can upload new content ads.'), ('set_content_ad_status', 'Can set status of content ads.'), ('get_content_ad_csv', 'Can download bulk content ad csv.'), ('content_ads_bulk_actions', 'Can view and use bulk content ads actions.'), ('can_toggle_ga_performance_tracking', 'Can toggle Google Analytics performance tracking.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_dma_targeting', 'Can set DMA targeting'), ('manage_conversion_pixels', 'Can manage conversion pixels'))},
        ),
    ]
