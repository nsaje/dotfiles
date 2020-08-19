# -*- coding: utf-8 -*-

from django.contrib.auth import models as auth_models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.core import validators as django_validators
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import utils.demo_anonymizer
from core.models import Source

from . import constants
from . import entity_permission
from . import instance
from . import manager
from . import queryset
from . import validation
from . import validators


class User(
    validation.UserValidationMixin,
    instance.UserMixin,
    entity_permission.EntityPermissionMixin,
    auth_models.AbstractBaseUser,
    auth_models.PermissionsMixin,
):
    """ Describes custom Zemanta user.

    IMPORTANT: Default unique constraint on the email created by Django is deleted and
    replaced by case-insensitive unique index created by one of migrations.
    """

    _demo_fields = {
        "email": utils.demo_anonymizer.fake_email,
        "username": utils.demo_anonymizer.fake_username,
        "first_name": utils.demo_anonymizer.fake_first_name,
        "last_name": utils.demo_anonymizer.fake_last_name,
    }
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    username = models.CharField(
        _("username"),
        max_length=30,
        blank=True,
        null=True,
        help_text=_("30 characters or fewer. Letters, digits and " "@/./+/-/_ only."),
        validators=[django_validators.RegexValidator(r"^[\w.@+-]+$", _("Enter a valid username."), "invalid")],
    )
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    is_staff = models.BooleanField(
        _("staff status"), default=False, help_text=_("Designates whether the user can log into this admin " "site.")
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as " "active. Unselect this instead of deleting accounts."
        ),
    )

    country = models.CharField(_("country"), max_length=2, null=True, blank=True)
    company_type = models.IntegerField(_("company type"), null=True, blank=True)
    job_title = models.CharField(_("job title"), max_length=256, null=True, blank=True)
    start_year_of_experience = models.IntegerField(_("start year of experience"), null=True, blank=True)
    programmatic_platforms = ArrayField(models.PositiveSmallIntegerField(), default=list, null=True, blank=True)

    is_test_user = models.BooleanField(
        default=False,
        help_text=_(
            "Designates whether user is an internal testing user and will not contribute towards certain statistics."
        ),
    )

    is_service = models.BooleanField(
        default=False, help_text=_("Designates whether a user represents an internal service.")
    )

    sspd_sources = models.ManyToManyField(Source, blank=True)

    sspd_sources_markets = JSONField(null=True, blank=True, validators=[validators.validate_sspd_sources_markets])
    outbrain_user_id = models.CharField(null=True, blank=True, max_length=30, help_text="Outbrain ID")

    status = models.IntegerField(default=constants.Status.INVITATION_PENDING, choices=constants.Status.get_choices())

    objects = manager.UserManager.from_queryset(queryset.UserQuerySet)()

    _settings_fields = [
        "first_name",
        "last_name",
        "country",
        "company_type",
        "job_title",
        "start_year_of_experience",
        "programmatic_platforms",
        "status",
    ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

        permissions = (
            ("campaign_settings_sales_rep", "Can be chosen as sales representative."),
            ("supply_dash_link_view", "Can view supply dash link."),
            ("all_accounts_accounts_view", "Can view all accounts's accounts tab."),
            ("account_campaigns_view", "Can view accounts's campaigns tab."),
            ("account_credit_view", "Can view accounts's credit tab."),
            ("ad_group_sources_add_source", "Can add media sources."),
            ("account_sources_view", "Can view account sources view."),
            ("all_accounts_sources_view", "Can view all accounts sources view."),
            ("account_campaigns_add_campaign", "Can add campaigns."),
            ("archive_restore_entity", "Can archive or restore an entity."),
            ("account_agency_access_permissions", "Can view and set account access permissions."),
            ("campaign_ad_groups_detailed_report", "Can download detailed report on campaign level."),
            ("view_pubs_postclick_acquisition", "Can view publishers postclick acq. metrics."),
            ("data_status_column", "Can see data status column in table."),
            (
                "can_see_media_source_status_on_submission_popover",
                "Can see media source status on submission status popover",
            ),
            ("can_set_subdivision_targeting", "Can set subdivision targeting"),
            ("can_set_media_source_to_auto_pilot", "Can set media source to auto-pilot"),
            ("has_intercom", "Can see intercom widget"),
            ("can_see_publishers", "Can see publishers"),
            ("can_see_publisher_blacklist_status", "Can see publishers blacklist status"),
            ("can_modify_publisher_blacklist_status", "Can modify publishers blacklist status"),
            ("can_see_account_type", "Can see account type"),
            ("can_modify_account_type", "Can modify account type"),
            ("can_modify_allowed_sources", "Can modify allowed sources on account level"),
            ("can_access_global_publisher_blacklist_status", "Can view or modify global publishers blacklist status"),
            (
                "can_access_campaign_account_publisher_blacklist_status",
                "Can view or modify account and campaign publishers blacklist status",
            ),
            ("can_see_all_available_sources", "Can see all available media sources in account settings"),
            ("account_account_view", "Can view account's Account tab."),
            ("can_view_actual_costs", "Can view actual costs"),
            (
                "can_modify_outbrain_account_publisher_blacklist_status",
                "Can modify Outbrain account publisher blacklist status",
            ),
            ("can_set_adgroup_to_auto_pilot", "Can set Ad Group to Auto-Pilot (budget and CPC automation)"),
            ("can_set_ad_group_max_cpc", "Can set ad group max cpc"),
            ("can_set_ad_group_max_cpm", "Can set ad group max CPM"),
            ("can_view_retargeting_settings", "Can view retargeting settings"),
            ("can_control_ad_group_state_in_table", "Can control ad group state in Campaign / Ad Groups table"),
            ("can_see_campaign_goals", "Can see and manage campaign goals"),
            (
                "can_see_managers_in_accounts_table",
                "Can see Account Manager and Sales Representative in accounts table.",
            ),
            ("can_see_managers_in_campaigns_table", "Can see Campaign Manager in campaigns table."),
            ("can_hide_chart", "Can show or hide chart"),
            ("can_access_all_accounts_infobox", "Can access info box on all accounts level"),
            ("campaign_goal_optimization", "Can view aggregate campaign goal optimisation metrics"),
            ("campaign_goal_performance", "Can view goal performance information"),
            ("can_include_model_ids_in_reports", "Can include model ids in reports"),
            ("has_supporthero", "Has Supporthero snippet"),
            ("can_filter_sources_through_table", "Can filter sources through sources table"),
            (
                "can_set_account_sales_representative",
                "Can view and set account sales representative on account settings tab.",
            ),
            ("can_modify_account_name", "Can see and modify account name on account settings tab."),
            ("can_modify_facebook_page", "Can see and modify facebook page."),
            ("can_modify_account_manager", "Can view and set account manager on account settings tab."),
            ("account_history_view", "Can view account" "s history tab."),
            (
                "hide_old_table_on_all_accounts_account_campaign_level",
                "Hide old table on all accounts, account and campaign level.",
            ),
            ("hide_old_table_on_ad_group_level", "Hide old table on ad group level."),
            (
                "can_access_table_breakdowns_feature",
                "Can access table breakdowns feature on all accounts, account and campaign level.",
            ),
            (
                "can_access_table_breakdowns_feature_on_ad_group_level",
                "Can access table breakdowns feature on ad group level.",
            ),
            (
                "can_access_table_breakdowns_feature_on_ad_group_level_publishers",
                "Can access table breakdowns feature on ad group level on publishers tab.",
            ),
            ("can_view_sidetabs", "Can view sidetabs."),
            ("can_view_campaign_content_insights_side_tab", "Can view content insights side tab on campaign level."),
            ("can_modify_campaign_manager", "Can view and set campaign manager on campaign settings tab."),
            ("can_modify_campaign_iab_category", "Can view and set campaign IAB category on campaign settings tab."),
            ("ad_group_history_view", "Can view ad group's history tab."),
            ("campaign_history_view", "Can view campaign's history tab."),
            ("can_view_new_history_backend", "Can view history from new history models."),
            ("can_request_demo_v3", "Can request demo v3."),
            ("can_set_ga_api_tracking", "Can set GA API tracking."),
            ("can_filter_by_agency", "Can filter by agency"),
            ("can_filter_by_account_type", "Can filter by account type"),
            ("can_access_agency_infobox", "Can access info box on all accounts agency level"),
            ("can_manage_agency_margin", "User can define margin in budget line item."),
            (
                "can_view_agency_margin",
                "[IGNORED if not BCMv2] User can view margin in budget tab and view margin columns in tables and reports.",
            ),
            (
                "can_view_platform_cost_breakdown",
                "[IGNORED if not BCMv2] User can view platform costs broken down into media, data and fee.",
            ),
            (
                "can_view_platform_cost_breakdown_derived",
                "[IGNORED if not BCMv2] User can view columns derived from platform costs.",
            ),
            ("can_view_agency_cost_breakdown", "User can view agency costs broken down into margin."),
            ("can_view_end_user_cost_breakdown", "User can view only total costs without margin, data and fee."),
            (
                "can_switch_between_cost_breakdowns",
                "User can switch between stats that include fee and margin and stats that don't.",
            ),
            ("can_view_breakdown_by_delivery", "User can view breakdowns by delivery."),
            ("account_custom_audiences_view", "User can manage custom audiences."),
            ("can_target_custom_audiences", "User can target custom audiences."),
            ("can_set_time_period_in_scheduled_reports", "User can set time period when creating scheduled reports"),
            ("can_set_day_of_week_in_scheduled_reports", "User can set day of week when creating scheduled reports"),
            (
                "can_see_agency_managers_under_access_permissions",
                "User can see agency managers under access permissions",
            ),
            ("can_promote_agency_managers", "User can promote agency managers on account settings tab"),
            ("can_set_agency_for_account", "User can set agency for account"),
            ("can_use_single_ad_upload", "User can use single content ad upload"),
            ("can_toggle_new_design", "User can toggle between old and new design"),
            ("can_see_new_header", "User can see new header"),
            ("can_see_new_filter_selector", "User can see new filter selector"),
            ("can_see_new_infobox", "User can see new infobox"),
            ("can_see_new_theme", "User can see new theme"),
            ("can_use_partial_updates_in_upload", "Partially update upload candidate fields"),
            ("can_use_own_images_in_upload", "User can use their own images in upload"),
            ("can_see_all_users_for_managers", "User can see all users when selecting account or campaign manager"),
            ("can_include_totals_in_reports", "Can include totals in reports"),
            ("can_view_additional_targeting", "Can view additional targeting"),
            ("bulk_actions_on_all_levels", "User can do bulk actions on all levels"),
            ("can_see_landing_mode_alerts", "User can see landing mode alerts above tables"),
            ("can_manage_oauth2_apps", "User can manage OAuth2 applications"),
            ("can_use_restapi", "User can use the REST API"),
            ("can_see_new_settings", "User can see new settings"),
            ("can_access_publisher_reports", "User can generate publisher reports"),
            ("can_see_rtb_sources_as_one", "User can see RTB Sources grouped as one"),
            ("can_set_interest_targeting", "User can set and see interest targeting settings"),
            ("can_edit_content_ads", "User can use edit form to edit existing content ads"),
            ("can_edit_publisher_groups", "User can edit publisher groups"),
            ("can_set_white_blacklist_publisher_groups", "User can set white or blacklist publisher groups"),
            (
                "can_access_additional_outbrain_publisher_settings",
                "User can see, set or edit additional Outbrain specific publisher settings",
            ),
            ("can_see_pixel_traffic", "User can see pixel traffic in pixels table"),
            ("can_set_rtb_sources_as_one_cpc", "User can see and set the bid CPC for RTB Sources grouped as one"),
            ("can_see_new_chart", "User can see new chart component"),
            ("can_see_new_user_permissions", "User can see new user permissions page"),
            ("can_see_new_content_insights", "User can see new content insights component"),
            ("can_see_history_in_drawer", "User can see history in drawer"),
            ("can_see_new_account_credit", "User can see new account credit component"),
            ("can_see_new_budgets", "User can see new campaing budget component"),
            ("can_see_new_scheduled_reports", "User can see new scheduled reports component"),
            ("can_see_backend_hacks", "User can see backend hacks"),
            ("can_redirect_pixels", "User can set redirect url for pixels"),
            ("can_see_pixel_notes", "User can see pixel notes"),
            ("can_see_new_pixels_view", "User can see new pixels view"),
            ("can_see_salesforce_url", "User can see SalesForce URL"),
            (
                "can_set_account_cs_representative",
                "Can view and set account CS representative on account settings tab.",
            ),
            ("campaign_settings_cs_rep", "Can be chosen as CS representative."),
            ("can_download_custom_reports", "Can download custom reports."),
            ("can_receive_pacing_email", "Can receive pacing emails."),
            ("can_see_publisher_groups_ui", "Can see publisher groups UI"),
            ("can_receive_sales_credit_email", "Can receive depleting credit emails."),
            ("can_see_new_report_download", "User can see new report download."),
            ("can_use_new_routing", "User can use new routing."),
            ("can_see_id_columns_in_table", "User can see id columns in table."),
            ("fea_new_geo_targeting", "Feature: new geo targeting widget."),
            ("can_set_advanced_device_targeting", "User can set advanced device targeting."),
            ("can_see_new_report_schedule", "User can see new report schedule."),
            ("can_clone_contentads", "User can clone content ads."),
            ("can_clone_adgroups", "User can clone ad groups."),
            ("can_clone_campaigns", "User can clone campaigns."),
            ("can_see_publishers_all_levels", "User can see publishers on all levels."),
            ("fea_can_see_roas", "User can see ROAS-related things."),
            ("can_use_bluekai_targeting", "User can use bluekai targeting"),
            ("can_see_realtime_spend", "User can see realtime spend"),
            ("can_set_delivery_type", "User can set delivery type."),
            ("can_set_click_capping", "User can set click capping on ad group level."),
            ("can_see_grid_actions", "User can see grid actions"),
            ("fea_can_see_inventory_planning", "User can use the inventory planning tool"),
            ("fea_can_use_column_picker_in_reports", "User can use column picker in reports modal."),
            ("disable_budget_management", "User can NOT manage campaign budgets (negated permission)"),
            ("can_view_breakdown_by_delivery_extended", "User can view extended breakdowns by delivery."),
            ("can_breakdown_reports_by_ads_and_publishers", "User can breakdown reports by ad and publishers"),
            ("can_see_all_accounts", "User can see all accounts."),
            ("can_see_campaign_language_choices", "User can see campaign language choices"),
            ("can_see_stats_in_local_currency", "User can see stats in local currency"),
            ("can_use_ad_additional_data", "User can use the additionalData field on content ad"),
            ("can_manage_goals_in_local_currency", "User can manage goals in local currency"),
            ("can_manage_settings_in_local_currency", "User can manage settings in local currency"),
            ("can_see_budget_optimization", "User can see budget optimization settings"),
            ("can_see_infobox_in_local_currency", "User can see infobox in local currency"),
            ("can_manage_budgets_in_local_currency", "User can manage budgets in local currency"),
            ("can_see_currency_setting", "User can see currency setting"),
            ("disable_public_rcs", "Disable some public features for RCS."),
            ("can_filter_by_media_source", "Can filter by media source"),
            (
                "can_request_accounts_report_in_local_currencies",
                "User can request all accounts report in local currencies",
            ),
            ("can_see_vast", "User can see vast upload option"),
            ("can_manage_restapi_access", "User can manage REST API access"),
            ("can_manage_credit_refunds", "User can see and create credit refunds"),
            ("can_see_mediamond_publishers", "User can see Mediamond publishers in inventory planning"),
            ("can_see_rcs_publishers", "User can see RCS publishers in inventory planning"),
            ("can_see_newscorp_publishers", "User can see News Corp publishers in inventory planning"),
            ("can_promote_additional_pixel", "User can promote a pixel to an additional audience pixel"),
            ("can_be_ob_representative", "User can be chosen as OB representative"),
            ("can_set_account_ob_representative", "User can set OB representative"),
            ("can_include_credit_refunds_in_report", "User can export credit refunds in all accounts report"),
            ("can_edit_advanced_custom_flags", "User can modify the advanced custom flags in admin"),
            ("can_see_amplify_review_link", "User can see link to Amplify review campaign"),
            ("fea_can_change_campaign_type", "User can change campaign type"),
            (
                "can_set_auto_add_new_sources",
                "User can set automatical addition of newly released sources to ad groups",
            ),
            ("sspd_can_see_all_sources", "SSPD: user can see all sources"),
            ("sspd_can_use_sspd", "SSPD: User can use SSP dashboard"),
            ("fea_can_use_cpm_buying", "User can use CPM Buying"),
            ("can_see_amplify_live_preview", "User can see Amplify Live Preview link in grid"),
            ("disable_public_newscorp", "Disable some public features for Newscorp"),
            ("can_manage_ad_group_dayparting", "User can manage ad groups' dayparting"),
            ("can_see_sspd_url", "User can see SSP dashboard URL"),
            ("fea_can_change_campaign_type_to_display", "User can change campaign type to display"),
            ("can_set_frequency_capping", "User can set frequency capping"),
            ("can_use_new_account_settings_drawer", "User can use new account settings drawer"),
            ("can_use_new_campaign_settings_drawer", "User can use new campaign settings drawer"),
            ("can_use_new_ad_group_settings_drawer", "User can use new ad_group settings drawer"),
            ("can_see_amplify_ad_id_column", "User can see Amplify ad id column in grid"),
            ("can_see_deals_in_ui", "User can see the deals on the entity settings"),
            ("can_see_open_in_admin", "User can see Open in Admin link"),
            ("can_use_advanced_inventory_planning_features", "Can use advanced inventory planning features."),
            ("can_set_export_delimiter_separator", "User can customize CSV export delimiter & decimal separator"),
            ("can_use_language_targeting", "User can use language targeting"),
            ("can_see_top_level_delivery_breakdowns", "User can see top-level delivery breakdowns"),
            ("can_set_bid_modifiers", "User can set bid modifiers"),
            ("can_review_bid_modifiers", "User can review bid modifiers in settings"),
            ("this_is_restapi_group", "MARKS THE GROUP THAT CONTAINS PUBLIC REST API PERMISSIONS."),
            ("this_is_agency_manager_group", "MARKS THE GROUP THAT CONTAINS AGENCY MANAGER PERMISSIONS."),
            ("this_is_public_group", "MARKS THE GROUP THAT CONTAINS PUBLIC PERMISSIONS."),
            ("this_is_amplify_group", "MARKS THE GROUP THAT CONTAINS AMPLIFY USERS."),
            ("sspd_can_filter_by_account", "SSPD: User can filter by account"),
            ("sspd_can_filter_by_agency", "SSPD: User can filter by agency"),
            ("sspd_can_block_agency", "SSPD: User can block agency"),
            ("sspd_can_block_account", "SSPD: User can block account"),
            ("sspd_can_block_campaign", "SSPD: User can block campaign"),
            ("sspd_can_block_ad_group", "SSPD: User can block ad group"),
            ("sspd_can_see_link_to_entity_in_z1", "SSPD: User can see link to entity in Z1"),
            ("can_set_click_capping_daily_click_budget", "User can set click capping daily click budget"),
            ("can_create_agency", "User can create a new agency"),
            ("can_include_tags_in_reports", "Can include tags in reports"),
            ("can_filter_by_business", "User can filter by business"),
            ("fea_can_create_automation_rules", "User can create automation rules."),
            ("can_see_all_nas_in_inventory_planning", "User can see all NAS sources in Inventory Planning."),
            ("can_set_source_bid_modifiers", "User can set source bid modifiers"),
            (
                "disable_ad_group_sources_bid",
                "User can NOT set bid cpc/cpm on ad group sources level (negated permission).",
            ),
            ("settings_defaults_on_campaign_level", "Can view ad group settings defaults on campaign level"),
            ("can_use_creative_icon", "User can use an icon on creatives."),
            ("can_see_deals_library", "User can see deals library."),
            ("can_see_user_management", "User can see user management."),
            ("can_see_direct_deals_section", "User can see direct deals section."),
            ("can_review_and_set_bid_modifiers_in_settings", "User can review and set bid modifiers in settings."),
            ("can_see_internal_deals", "User can see and edit internal deals in the library."),
            ("can_use_placement_targeting", "User can use publisher placement targeting."),
            ("can_see_new_publisher_library", "User can see the new Publishers & Placements library."),
            ("can_see_add_to_pub_plac_button", "User can see the Add to Publishers and Placements button"),
            ("fea_use_entity_permission", "User can use entity permissions."),
            ("can_see_mrc100_metrics", "User can see the MRC100 viewability metrics"),
            ("can_see_vast4_metrics", "User can see the VAST4 viewability metrics"),
            (
                "can_see_service_fee",
                "User can view platform costs broken down into base media, base data and service fee.",
            ),
            ("can_enable_push_metrics", "User can enable push metrics through special link"),
        )
