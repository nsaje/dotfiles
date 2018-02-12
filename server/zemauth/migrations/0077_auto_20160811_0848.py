# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-11 08:48


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0076_auto_20160809_1005'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_credit_view', "Can view accounts's credit tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('view_pubs_postclick_acquisition', 'Can view publishers postclick acq. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_subdivision_targeting', 'Can set subdivision targeting'), ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'), ('add_media_sources_automatically', 'Automatically add media sources on ad group creation'), ('has_intercom', 'Can see intercom widget'), ('can_see_publishers', 'Can see publishers'), ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'), ('group_campaign_stop_on_budget_depleted', 'Automatic campaign stop on depleted budget applies to campaigns in this group'), ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'), ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'), ('can_see_account_type', 'Can see account type'), ('can_modify_account_type', 'Can modify account type'), ('can_modify_allowed_sources', 'Can modify allowed sources on account level'), ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'), ('can_access_campaign_account_publisher_blacklist_status', 'Can view or modify account and campaign publishers blacklist status'), ('can_see_all_available_sources', 'Can see all available media sources in account settings'), ('account_account_view', "Can view account's Account tab."), ('can_view_actual_costs', 'Can view actual costs'), ('can_modify_outbrain_account_publisher_blacklist_status', 'Can modify Outbrain account publisher blacklist status'), ('can_set_adgroup_to_auto_pilot', 'Can set Ad Group to Auto-Pilot (budget and CPC automation)'), ('can_set_ad_group_max_cpc', 'Can set ad group max cpc'), ('can_view_retargeting_settings', 'Can view retargeting settings'), ('can_view_flat_fees', 'Can view flat fees in All accounts/accounts table'), ('can_control_ad_group_state_in_table', 'Can control ad group state in Campaign / Ad Groups table'), ('can_see_campaign_goals', 'Can see and manage campaign goals'), ('can_see_projections', 'Can see projections'), ('can_see_managers_in_accounts_table', 'Can see Account Manager and Sales Representative in accounts table.'), ('can_see_managers_in_campaigns_table', 'Can see Campaign Manager in campaigns table.'), ('can_hide_chart', 'Can show or hide chart'), ('can_access_all_accounts_infobox', 'Can access info box on all accounts level'), ('campaign_goal_optimization', 'Can view aggregate campaign goal optimisation metrics'), ('campaign_goal_performance', 'Can view goal performance information'), ('can_include_model_ids_in_reports', 'Can include model ids in reports'), ('has_supporthero', 'Has Supporthero snippet'), ('can_filter_sources_through_table', 'Can filter sources through sources table'), ('can_view_account_agency_information', 'Can view agency column in tables.'), ('can_set_account_sales_representative', 'Can view and set account sales representative on account settings tab.'), ('can_modify_account_name', 'Can see and modify account name on account settings tab.'), ('can_modify_facebook_page', 'Can see and modify facebook page.'), ('can_modify_account_manager', 'Can view and set account manager on account settings tab.'), ('account_history_view', 'Can view accounts history tab.'), ('hide_old_table_on_all_accounts_account_campaign_level', 'Hide old table on all accounts, account and campaign level.'), ('hide_old_table_on_ad_group_level', 'Hide old table on ad group level.'), ('can_access_table_breakdowns_feature', 'Can access table breakdowns feature on all accounts, account and campaign level.'), ('can_access_table_breakdowns_feature_on_ad_group_level', 'Can access table breakdowns feature on ad group level.'), ('can_view_sidetabs', 'Can view sidetabs.'), ('can_view_campaign_content_insights_side_tab', 'Can view content insights side tab on campaign level.'), ('can_modify_campaign_manager', 'Can view and set campaign manager on campaign settings tab.'), ('can_modify_campaign_iab_category', 'Can view and set campaign IAB category on campaign settings tab.'), ('ad_group_history_view', "Can view ad group's history tab."), ('campaign_history_view', "Can view campaign's history tab."), ('can_view_new_history_backend', 'Can view history from new history models.'), ('can_request_demo_v3', 'Can request demo v3.'), ('can_set_ga_api_tracking', 'Can set GA API tracking.'), ('can_filter_by_agency', 'Can filter by agency'), ('can_filter_by_account_type', 'Can filter by account type'), ('can_access_agency_infobox', 'Can access info box on all accounts agency level'), ('can_manage_agency_margin', 'User can define margin in budget line item.'), ('can_view_agency_margin', 'User can view margin in budget tab and view margin columns in tables and reports.'), ('can_view_platform_cost_breakdown', 'User can view platform costs broken down into media, data and fee.'), ('can_view_breakdown_by_delivery', 'User can view breakdowns by delivery.'), ('can_set_time_period_in_scheduled_reports', 'User can set time period when creating scheduled reports')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
