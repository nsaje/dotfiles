# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': (('campaign_settings_view', "Can view campaign's settings tab."), ('campaign_agency_view', "Can view campaign's agency tab."), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_budget_view', "Can view campaign's budget tab."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('account_credit_view', "Can view accounts's credit tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('campaign_sources_view', 'Can view campaign sources view.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('all_new_sidebar', 'Can see new sidebar.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('view_archived_entities', 'Can view archived entities.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('set_ad_group_source_settings', 'Can set per-source settings.'), ('see_current_ad_group_source_state', 'Can see current per-source state.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('new_content_ads_tab', 'Can view new content ads tab.'), ('filter_sources', 'Can filter sources'), ('upload_content_ads', 'Can upload new content ads.'), ('set_content_ad_status', 'Can set status of content ads.'), ('get_content_ad_csv', 'Can download bulk content ad csv.'), ('content_ads_bulk_actions', 'Can view and use bulk content ads actions.'), ('can_toggle_ga_performance_tracking', 'Can toggle Google Analytics performance tracking.'), ('can_toggle_adobe_performance_tracking', 'Can toggle Adobe Analytics performance tracking.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_subdivision_targeting', 'Can set subdivision targeting'), ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'), ('manage_conversion_pixels', 'Can manage conversion pixels'), ('add_media_sources_automatically', 'Automatically add media sources on ad group creation'), ('has_intercom', 'Can see intercom widget'), ('can_see_publishers', 'Can see publishers'), ('manage_conversion_goals', 'Can manage conversion goals on campaign level'), ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'), ('group_campaign_stop_on_budget_depleted', 'Automatic campaign stop on depleted budget applies to campaigns in this group'), ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'), ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'), ('conversion_reports', 'Can see conversions and goals in reports'), ('exports_plus', 'Can download reports using new export facilities'), ('can_modify_allowed_sources', 'Can modify allowed sources on account level'), ('settings_defaults_on_campaign_level', 'Can view ad group settings defaults on campaign level'), ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'), ('can_access_campaign_account_publisher_blacklist_status', 'Can view or modify account and campaign publishers blacklist status'), ('can_see_all_available_sources', 'Can see all available media sources in account settings'), ('can_see_infobox', 'Can see info box'), ('account_account_view', "Can view account's Account tab."), ('can_view_effective_costs', 'Can view effective costs'), ('can_view_actual_costs', 'Can view actual costs'))},
        ),
    ]
