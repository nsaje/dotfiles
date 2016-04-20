# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-20 09:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0026_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('campaign_settings_view', "Can view campaign's settings tab."), ('campaign_agency_view', "Can view campaign's agency tab."), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_budget_view', "Can view campaign's budget tab."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('account_credit_view', "Can view accounts's credit tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('campaign_sources_view', 'Can view campaign sources view.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('all_new_sidebar', 'Can see new sidebar.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('view_archived_entities', 'Can view archived entities.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('set_ad_group_source_settings', 'Can set per-source settings.'), ('see_current_ad_group_source_state', 'Can see current per-source state.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('view_pubs_conversion_goals', 'Can view publishers conversion goals.'), ('view_pubs_postclick_acquisition', 'Can view publishers postclick acq. metrics.'), ('view_pubs_postclick_engagement', 'Can view publishers postclick eng. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('filter_sources', 'Can filter sources'), ('upload_content_ads', 'Can upload new content ads.'), ('set_content_ad_status', 'Can set status of content ads.'), ('get_content_ad_csv', 'Can download bulk content ad csv.'), ('content_ads_bulk_actions', 'Can view and use bulk content ads actions.'), ('can_toggle_ga_performance_tracking', 'Can toggle Google Analytics performance tracking.'), ('can_toggle_adobe_performance_tracking', 'Can toggle Adobe Analytics performance tracking.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_subdivision_targeting', 'Can set subdivision targeting'), ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'), ('manage_conversion_pixels', 'Can manage conversion pixels'), ('add_media_sources_automatically', 'Automatically add media sources on ad group creation'), ('has_intercom', 'Can see intercom widget'), ('can_see_publishers', 'Can see publishers'), ('manage_conversion_goals', 'Can manage conversion goals on campaign level'), ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'), ('group_campaign_stop_on_budget_depleted', 'Automatic campaign stop on depleted budget applies to campaigns in this group'), ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'), ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'), ('conversion_reports', 'Can see conversions and goals in reports'), ('can_modify_allowed_sources', 'Can modify allowed sources on account level'), ('settings_defaults_on_campaign_level', 'Can view ad group settings defaults on campaign level'), ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'), ('can_access_campaign_account_publisher_blacklist_status', 'Can view or modify account and campaign publishers blacklist status'), ('can_see_all_available_sources', 'Can see all available media sources in account settings'), ('can_see_infobox', 'Can see info box'), ('account_account_view', "Can view account's Account tab."), ('can_view_effective_costs', 'Can view effective costs'), ('can_view_actual_costs', 'Can view actual costs'), ('can_modify_outbrain_account_publisher_blacklist_status', 'Can modify Outbrain account publisher blacklist status'), ('can_set_adgroup_to_auto_pilot', 'Can set Ad Group to Auto-Pilot (budget and CPC automation)'), ('can_set_ad_group_max_cpc', 'Can set ad group max cpc'), ('can_view_retargeting_settings', 'Can view retargeting settings'), ('can_view_flat_fees', 'Can view flat fees in All accounts/accounts table'), ('can_control_ad_group_state_in_table', 'Can control ad group state in Campaign / Ad Groups table'), ('can_see_campaign_goals', 'Can see and manage campaign goals'), ('can_see_projections', 'Can see projections'), ('can_see_managers_in_accounts_table', 'Can see Account Manager and Sales Representative in accounts table.'), ('can_see_managers_in_campaigns_table', 'Can see Campaign Manager in campaigns table.'), ('can_hide_chart', 'Can show or hide chart'), ('can_access_ad_group_infobox', 'Can access info box on adgroup level'), ('can_access_campaign_infobox', 'Can access info box on campaign level'), ('can_access_account_infobox', 'Can access info box on account level'), ('can_access_all_accounts_infobox', 'Can access info box on all accounts level'), ('campaign_goal_optimization', 'Can view aggregate campaign goal optimisation metrics'), ('campaign_goal_performance', 'Can view goal performance information'), ('can_include_model_ids_in_reports', 'Can include model ids in reports'), ('has_supporthero', 'Has Supporthero snippet'), ('can_filter_sources_through_table', 'Can filter sources through sources table')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
