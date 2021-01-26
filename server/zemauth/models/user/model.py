# -*- coding: utf-8 -*-

from django.contrib.auth import models as auth_models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.core import validators as django_validators
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import utils.demo_anonymizer

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
    """Describes custom Zemanta user.

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

    sspd_sources = models.ManyToManyField("dash.Source", blank=True)

    sspd_sources_markets = JSONField(null=True, blank=True, validators=[validators.validate_sspd_sources_markets])
    outbrain_user_id = models.CharField(null=True, blank=True, max_length=30, help_text="Outbrain ID")

    status = models.IntegerField(default=constants.Status.INVITATION_PENDING, choices=constants.Status.get_choices())
    is_externally_managed = models.BooleanField(default=False)
    sales_office = models.CharField(null=True, blank=True, max_length=255)

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
        "email",
        "sales_office",
    ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

        permissions = (
            ("campaign_settings_sales_rep", "Can be chosen as sales representative."),
            ("supply_dash_link_view", "Can view supply dash link."),
            ("account_credit_view", "Can view accounts's credit tab."),
            ("account_agency_access_permissions", "Can view and set account access permissions."),
            ("campaign_ad_groups_detailed_report", "Can download detailed report on campaign level."),
            ("view_pubs_postclick_acquisition", "Can view publishers postclick acq. metrics."),
            ("data_status_column", "Can see data status column in table."),
            ("can_see_account_type", "Can see account type"),
            ("can_modify_account_type", "Can modify account type"),
            ("can_access_global_publisher_blacklist_status", "Can view or modify global publishers blacklist status"),
            ("can_see_all_available_sources", "Can see all available media sources in account settings"),
            ("can_view_actual_costs", "Can view actual costs"),
            ("can_set_ad_group_max_cpm", "Can set ad group max CPM"),
            (
                "can_see_managers_in_accounts_table",
                "Can see Account Manager and Sales Representative in accounts table.",
            ),
            ("can_see_managers_in_campaigns_table", "Can see Campaign Manager in campaigns table."),
            ("can_hide_chart", "Can show or hide chart"),
            ("can_access_all_accounts_infobox", "Can access info box on all accounts level"),
            (
                "can_set_account_sales_representative",
                "Can view and set account sales representative on account settings tab.",
            ),
            ("can_modify_account_manager", "Can view and set account manager on account settings tab."),
            ("can_request_demo_v3", "Can request demo v3."),
            ("can_filter_by_account_type", "Can filter by account type"),
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
            (
                "can_switch_between_cost_breakdowns",
                "User can switch between stats that include fee and margin and stats that don't.",
            ),
            ("can_promote_agency_managers", "User can promote agency managers on account settings tab"),
            ("can_toggle_new_design", "User can toggle between old and new design"),
            ("can_see_all_users_for_managers", "User can see all users when selecting account or campaign manager"),
            (
                "can_access_additional_outbrain_publisher_settings",
                "User can see, set or edit additional Outbrain specific publisher settings",
            ),
            ("can_see_new_account_credit", "User can see new account credit component"),
            ("can_see_backend_hacks", "User can see backend hacks"),
            ("can_redirect_pixels", "User can set redirect url for pixels"),
            ("can_see_salesforce_url", "User can see SalesForce URL"),
            (
                "can_set_account_cs_representative",
                "Can view and set account CS representative on account settings tab.",
            ),
            ("campaign_settings_cs_rep", "Can be chosen as CS representative."),
            ("can_download_custom_reports", "Can download custom reports."),
            ("can_receive_sales_credit_email", "Can receive depleting credit emails."),
            ("can_view_breakdown_by_delivery_extended", "User can view extended breakdowns by delivery."),
            ("can_use_ad_additional_data", "User can use the additionalData field on content ad"),
            ("can_manage_restapi_access", "User can manage REST API access"),
            ("can_manage_credit_refunds", "User can see and create credit refunds"),
            ("can_see_mediamond_publishers", "User can see Mediamond publishers in inventory planning"),
            ("can_see_rcs_publishers", "User can see RCS publishers in inventory planning"),
            ("can_see_newscorp_publishers", "User can see News Corp publishers in inventory planning"),
            ("can_be_ob_representative", "User can be chosen as OB representative"),
            ("can_set_account_ob_representative", "User can set OB representative"),
            ("can_include_credit_refunds_in_report", "User can export credit refunds in all accounts report"),
            ("can_edit_advanced_custom_flags", "User can modify the advanced custom flags in admin"),
            ("can_see_amplify_review_link", "User can see link to Amplify review campaign"),
            ("sspd_can_see_all_sources", "SSPD: user can see all sources"),
            ("sspd_can_use_sspd", "SSPD: User can use SSP dashboard"),
            ("can_see_amplify_live_preview", "User can see Amplify Live Preview link in grid"),
            ("can_see_sspd_url", "User can see SSP dashboard URL"),
            ("fea_can_change_campaign_type_to_display", "User can change campaign type to display"),
            ("can_see_amplify_ad_id_column", "User can see Amplify ad id column in grid"),
            ("can_see_deals_in_ui", "User can see the deals on the entity settings"),
            ("can_see_open_in_admin", "User can see Open in Admin link"),
            ("can_review_bid_modifiers", "User can review bid modifiers in settings"),
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
            ("settings_defaults_on_campaign_level", "Can view ad group settings defaults on campaign level"),
            ("can_see_internal_deals", "User can see and edit internal deals in the library."),
            ("can_see_mrc100_metrics", "User can see the MRC100 viewability metrics"),
            ("can_see_vast4_metrics", "User can see the VAST4 viewability metrics"),
            (
                "can_see_service_fee",
                "User can view platform costs broken down into base media, base data and service fee.",
            ),
            ("can_enable_push_metrics", "User can enable push metrics through special link"),
            ("can_use_smart_grid_in_analytics_view", "User can use smart grid in analytics view"),
            ("can_use_3rdparty_js_trackers", "User can use 3rd party JS tracking"),
            ("can_use_oen_browser_targeting", "User can use OEN browser targeting"),
            ("can_see_creative_library", "User can see the Creative library"),
            ("can_use_realtimestats_api", "User can use realtimestats API"),
        )
