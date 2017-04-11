# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-05 15:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0133_auto_20170404_1139'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_credit_view', "Can view accounts's credit tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('unspent_budget_view', 'Can view unspent budget.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('view_pubs_postclick_acquisition', 'Can view publishers postclick acq. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_subdivision_targeting', 'Can set subdivision targeting'), ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'), ('add_media_sources_automatically', 'Automatically add media sources on ad group creation'), ('has_intercom', 'Can see intercom widget'), ('can_see_publishers', 'Can see publishers'), ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'), ('group_campaign_stop_on_budget_depleted', 'Automatic campaign stop on depleted budget applies to campaigns in this group'), ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'), ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'), ('can_see_account_type', 'Can see account type'), ('can_modify_account_type', 'Can modify account type'), ('can_modify_allowed_sources', 'Can modify allowed sources on account level'), ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'), ('can_access_campaign_account_publisher_blacklist_status', 'Can view or modify account and campaign publishers blacklist status'), ('can_see_all_available_sources', 'Can see all available media sources in account settings'), ('account_account_view', "Can view account's Account tab."), ('can_view_actual_costs', 'Can view actual costs'), ('can_modify_outbrain_account_publisher_blacklist_status', 'Can modify Outbrain account publisher blacklist status'), ('can_set_adgroup_to_auto_pilot', 'Can set Ad Group to Auto-Pilot (budget and CPC automation)'), ('can_set_ad_group_max_cpc', 'Can set ad group max cpc'), ('can_set_ad_group_max_cpm', 'Can set ad group max CPM'), ('can_view_retargeting_settings', 'Can view retargeting settings'), ('can_view_flat_fees', 'Can view flat fees in All accounts/accounts table'), ('can_control_ad_group_state_in_table', 'Can control ad group state in Campaign / Ad Groups table'), ('can_see_campaign_goals', 'Can see and manage campaign goals'), ('can_see_projections', 'Can see projections'), ('can_see_managers_in_accounts_table', 'Can see Account Manager and Sales Representative in accounts table.'), ('can_see_managers_in_campaigns_table', 'Can see Campaign Manager in campaigns table.'), ('can_hide_chart', 'Can show or hide chart'), ('can_access_all_accounts_infobox', 'Can access info box on all accounts level'), ('campaign_goal_optimization', 'Can view aggregate campaign goal optimisation metrics'), ('campaign_goal_performance', 'Can view goal performance information'), ('can_include_model_ids_in_reports', 'Can include model ids in reports'), ('has_supporthero', 'Has Supporthero snippet'), ('can_filter_sources_through_table', 'Can filter sources through sources table'), ('can_view_account_agency_information', 'Can view agency column in tables.'), ('can_set_account_sales_representative', 'Can view and set account sales representative on account settings tab.'), ('can_modify_account_name', 'Can see and modify account name on account settings tab.'), ('can_modify_facebook_page', 'Can see and modify facebook page.'), ('can_modify_account_manager', 'Can view and set account manager on account settings tab.'), ('account_history_view', 'Can view accounts history tab.'), ('hide_old_table_on_all_accounts_account_campaign_level', 'Hide old table on all accounts, account and campaign level.'), ('hide_old_table_on_ad_group_level', 'Hide old table on ad group level.'), ('can_access_table_breakdowns_feature', 'Can access table breakdowns feature on all accounts, account and campaign level.'), ('can_access_table_breakdowns_feature_on_ad_group_level', 'Can access table breakdowns feature on ad group level.'), ('can_access_table_breakdowns_feature_on_ad_group_level_publishers', 'Can access table breakdowns feature on ad group level on publishers tab.'), ('can_view_sidetabs', 'Can view sidetabs.'), ('can_view_campaign_content_insights_side_tab', 'Can view content insights side tab on campaign level.'), ('can_modify_campaign_manager', 'Can view and set campaign manager on campaign settings tab.'), ('can_modify_campaign_iab_category', 'Can view and set campaign IAB category on campaign settings tab.'), ('ad_group_history_view', "Can view ad group's history tab."), ('campaign_history_view', "Can view campaign's history tab."), ('can_view_new_history_backend', 'Can view history from new history models.'), ('can_request_demo_v3', 'Can request demo v3.'), ('can_set_ga_api_tracking', 'Can set GA API tracking.'), ('can_filter_by_agency', 'Can filter by agency'), ('can_filter_by_account_type', 'Can filter by account type'), ('can_access_agency_infobox', 'Can access info box on all accounts agency level'), ('can_manage_agency_margin', 'User can define margin in budget line item.'), ('can_view_agency_margin', 'User can view margin in budget tab and view margin columns in tables and reports.'), ('can_view_platform_cost_breakdown', 'User can view platform costs broken down into media, data and fee.'), ('can_view_breakdown_by_delivery', 'User can view breakdowns by delivery.'), ('account_custom_audiences_view', 'User can manage custom audiences.'), ('can_target_custom_audiences', 'User can target custom audiences.'), ('can_set_time_period_in_scheduled_reports', 'User can set time period when creating scheduled reports'), ('can_set_day_of_week_in_scheduled_reports', 'User can set day of week when creating scheduled reports'), ('can_see_agency_managers_under_access_permissions', 'User can see agency managers under access permissions'), ('can_promote_agency_managers', 'User can promote agency managers on account settings tab'), ('group_agency_manager_add', 'Agency managers are added to this group when promoted'), ('can_set_agency_for_account', 'User can set agency for account'), ('can_use_single_ad_upload', 'User can use single content ad upload'), ('can_toggle_new_design', 'User can toggle between old and new design'), ('can_see_new_header', 'User can see new header'), ('can_see_new_filter_selector', 'User can see new filter selector'), ('can_see_new_infobox', 'User can see new infobox'), ('can_see_new_theme', 'User can see new theme'), ('can_use_partial_updates_in_upload', 'Partially update upload candidate fields'), ('can_use_own_images_in_upload', 'User can use their own images in upload'), ('can_see_all_users_for_managers', 'User can see all users when selecting account or campaign manager'), ('can_include_totals_in_reports', 'Can include totals in reports'), ('can_view_additional_targeting', 'Can view additional targeting'), ('bulk_actions_on_all_levels', 'User can do bulk actions on all levels'), ('can_see_landing_mode_alerts', 'User can see landing mode alerts above tables'), ('can_manage_oauth2_apps', 'User can manage OAuth2 applications'), ('can_use_restapi', 'User can use the REST API'), ('can_see_new_settings', 'User can see new settings'), ('can_access_publisher_reports', 'User can generate publisher reports'), ('can_see_rtb_sources_as_one', 'User can see RTB Sources grouped as one'), ('can_set_interest_targeting', 'User can set and see interest targeting settings'), ('can_edit_content_ads', 'User can use edit form to edit existing content ads'), ('can_edit_publisher_groups', 'User can edit publisher groups'), ('can_set_white_blacklist_publisher_groups', 'User can set white or blacklist publisher groups'), ('can_access_additional_outbrain_publisher_settings', 'User can see, set or edit additional Outbrain specific publisher settings'), ('can_see_pixel_traffic', 'User can see pixel traffic in pixels table'), ('can_set_rtb_sources_as_one_cpc', 'User can see and set the bid CPC for RTB Sources grouped as one'), ('can_see_new_chart', 'User can see new chart component'), ('can_see_new_user_permissions', 'User can see new user permissions page'), ('can_see_new_content_insights', 'User can see new content insights component'), ('can_see_history_in_drawer', 'User can see history in drawer'), ('can_see_new_account_credit', 'User can see new account credit component'), ('can_see_new_budgets', 'User can see new campaing budget component'), ('can_see_new_scheduled_reports', 'User can see new scheduled reports component'), ('can_see_backend_hacks', 'User can see backend hacks'), ('can_redirect_pixels', 'User can set redirect url for pixels'), ('can_see_pixel_notes', 'User can see pixel notes'), ('can_see_new_pixels_view', 'User can see new pixels view'), ('can_see_salesforce_url', 'User can see SalesForce URL'), ('can_set_account_cs_representative', 'Can view and set account CS representative on account settings tab.'), ('campaign_settings_cs_rep', 'Can be chosen as CS representative.'), ('can_download_custom_reports', 'Can download custom reports.'), ('can_receive_pacing_email', 'Can receive pacing emails.'), ('can_see_publisher_groups_ui', 'Can see publisher groups UI'), ('can_receive_sales_credit_email', 'Can receive depleting credit emails.'), ('can_see_new_report_download', 'User can see new report download.'), ('can_use_new_routing', 'User can use new routing.'), ('can_see_id_columns_in_table', 'User can see id columns in table.'), ('can_set_advanced_device_targeting', 'User can set advanced device targeting.'), ('can_see_new_report_schedule', 'User can see new report schedule.')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
