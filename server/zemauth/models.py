import operator

from django.contrib.auth import models as auth_models
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.core.exceptions import ValidationError
from django.conf import settings

import utils.demo_anonymizer
import utils.email_helper
from functools import reduce


class UserManager(auth_models.BaseUserManager):

    def get_queryset(self):
        return self.model.QuerySet(self.model)

    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

    def get_or_create_service_user(self, service_name):
        user, _ = self.get_or_create(username=service_name,
                                     email='%s@service.zemanta.com' % service_name,
                                     is_service=True)
        return user

    def get_users_with_perm(self, perm_name, include_superusers=False):
        perm = auth_models.Permission.objects.get(codename=perm_name)

        query_list = [
            models.Q(groups__permissions=perm),
            models.Q(user_permissions=perm)
        ]

        if include_superusers:
            query_list.append(models.Q(is_superuser=True))

        return self.filter(reduce(operator.or_, query_list)).distinct()


class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    ''' Describes custom Zemanta user.

    IMPORTANT: Default unique constraint on the email created by Django is deleted and
    replaced by case-insensitive unique index created by one of migrations.
    '''
    _demo_fields = {
        'email': utils.demo_anonymizer.fake_email,
        'username': utils.demo_anonymizer.fake_username,
        'first_name': utils.demo_anonymizer.fake_first_name,
        'last_name': utils.demo_anonymizer.fake_last_name,
    }
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    username = models.CharField(
        _('username'),
        max_length=30,
        blank=True,
        null=True,
        help_text=_('30 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+-]+$', _('Enter a valid username.'), 'invalid')
        ]
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.')
    )

    is_test_user = models.BooleanField(
        default=False,
        help_text=_('Designates whether user is an internal testing user and will not contribute towards certain statistics.')
    )

    is_service = models.BooleanField(
        default=False,
        help_text=_('Designates whether a user represents an internal service.')
    )

    objects = UserManager()

    class QuerySet(models.QuerySet):

        def filter_by_agencies(self, agencies):
            if not agencies:
                return self
            return self.filter(
                models.Q(agency__id__in=agencies) |
                models.Q(groups__permissions__codename='can_see_all_accounts') |
                models.Q(user_permissions__codename='can_see_all_accounts')
            ).distinct()

        def filter_selfmanaged(self):
            return self.filter(email__isnull=False)\
                .exclude(email__icontains="@zemanta")\
                .exclude(is_test_user=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    SUPERUSER_EXCLUDED_PERMISSIONS = (
        'disable_public_rcs',
        'disable_budget_management',
        'can_see_projections',
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

        permissions = (
            ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'),
            ('supply_dash_link_view', 'Can view supply dash link.'),
            ('all_accounts_accounts_view', "Can view all accounts's accounts tab."),
            ('account_campaigns_view', "Can view accounts's campaigns tab."),
            ('account_credit_view', "Can view accounts's credit tab."),
            ('ad_group_sources_add_source', "Can add media sources."),
            ('account_sources_view', 'Can view account sources view.'),
            ('all_accounts_sources_view', 'Can view all accounts sources view.'),
            ('account_campaigns_add_campaign', 'Can add campaigns.'),
            ('all_accounts_accounts_add_account', 'Can add accounts.'),
            ('archive_restore_entity', 'Can archive or restore an entity.'),
            ('account_agency_access_permissions', 'Can view and set account access permissions.'),
            ('group_new_user_add', 'New users are added to this group.'),
            ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'),
            ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'),
            ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'),
            ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'),
            ('view_pubs_postclick_acquisition', 'Can view publishers postclick acq. metrics.'),
            ('data_status_column', 'Can see data status column in table.'),
            ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'),
            ('can_set_subdivision_targeting', 'Can set subdivision targeting'),
            ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'),
            ('has_intercom', 'Can see intercom widget'),
            ('can_see_publishers', 'Can see publishers'),
            ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'),
            ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'),
            ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'),
            ('can_see_account_type', 'Can see account type'),
            ('can_modify_account_type', 'Can modify account type'),
            ('can_modify_allowed_sources', 'Can modify allowed sources on account level'),
            ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'),
            ('can_access_campaign_account_publisher_blacklist_status',
             'Can view or modify account and campaign publishers blacklist status'),
            ('can_see_all_available_sources', 'Can see all available media sources in account settings'),
            ('account_account_view', "Can view account's Account tab."),
            ('can_view_actual_costs', 'Can view actual costs'),
            ('can_modify_outbrain_account_publisher_blacklist_status',
             'Can modify Outbrain account publisher blacklist status'),
            ('can_set_adgroup_to_auto_pilot', 'Can set Ad Group to Auto-Pilot (budget and CPC automation)'),
            ('can_set_ad_group_max_cpc', 'Can set ad group max cpc'),
            ('can_set_ad_group_max_cpm', 'Can set ad group max CPM'),
            ('can_view_retargeting_settings', 'Can view retargeting settings'),
            ('can_view_flat_fees', '[IGNORED if not BCMv2] Can view flat fees in All accounts/accounts table'),
            ('can_control_ad_group_state_in_table', 'Can control ad group state in Campaign / Ad Groups table'),
            ('can_see_campaign_goals', 'Can see and manage campaign goals'),
            ('can_see_projections', 'Can see projections'),
            ('can_see_managers_in_accounts_table', "Can see Account Manager and Sales Representative in accounts table."),
            ('can_see_managers_in_campaigns_table', "Can see Campaign Manager in campaigns table."),
            ('can_hide_chart', 'Can show or hide chart'),
            ('can_access_all_accounts_infobox', 'Can access info box on all accounts level'),
            ('campaign_goal_optimization', 'Can view aggregate campaign goal optimisation metrics'),
            ('campaign_goal_performance', 'Can view goal performance information'),
            ('can_include_model_ids_in_reports', 'Can include model ids in reports'),
            ('has_supporthero', 'Has Supporthero snippet'),
            ('can_filter_sources_through_table', 'Can filter sources through sources table'),
            ('can_view_account_agency_information', 'Can view agency column in tables.'),
            ('can_set_account_sales_representative', 'Can view and set account sales representative on account settings tab.'),
            ('can_modify_account_name', 'Can see and modify account name on account settings tab.'),
            ('can_modify_facebook_page', 'Can see and modify facebook page.'),
            ('can_modify_account_manager', 'Can view and set account manager on account settings tab.'),
            ('account_history_view', 'Can view account''s history tab.'),
            ('hide_old_table_on_all_accounts_account_campaign_level',
             'Hide old table on all accounts, account and campaign level.'),
            ('hide_old_table_on_ad_group_level', 'Hide old table on ad group level.'),
            ('can_access_table_breakdowns_feature',
             'Can access table breakdowns feature on all accounts, account and campaign level.'),
            ('can_access_table_breakdowns_feature_on_ad_group_level',
             'Can access table breakdowns feature on ad group level.'),
            ('can_access_table_breakdowns_feature_on_ad_group_level_publishers',
             'Can access table breakdowns feature on ad group level on publishers tab.'),
            ('can_view_sidetabs', 'Can view sidetabs.'),
            ('can_view_campaign_content_insights_side_tab', 'Can view content insights side tab on campaign level.'),
            ('can_modify_campaign_manager', 'Can view and set campaign manager on campaign settings tab.'),
            ('can_modify_campaign_iab_category', 'Can view and set campaign IAB category on campaign settings tab.'),
            ('ad_group_history_view', "Can view ad group's history tab."),
            ('campaign_history_view', "Can view campaign's history tab."),
            ('can_view_new_history_backend', 'Can view history from new history models.'),
            ('can_request_demo_v3', 'Can request demo v3.'),
            ('can_set_ga_api_tracking', 'Can set GA API tracking.'),
            ('can_filter_by_agency', 'Can filter by agency'),
            ('can_filter_by_account_type', 'Can filter by account type'),
            ('can_access_agency_infobox', 'Can access info box on all accounts agency level'),
            ('can_manage_agency_margin', 'User can define margin in budget line item.'),
            ('can_view_agency_margin',
             '[IGNORED if not BCMv2] User can view margin in budget tab and view margin columns in tables and reports.'),
            ('can_view_platform_cost_breakdown',
             '[IGNORED if not BCMv2] User can view platform costs broken down into media, data and fee.'),
            ('can_view_platform_cost_breakdown_derived',
             '[IGNORED if not BCMv2] User can view columns derived from platform costs.'),
            ('can_view_agency_cost_breakdown', 'User can view agency costs broken down into margin.'),
            ('can_view_end_user_cost_breakdown', 'User can view only total costs without margin, data and fee.'),
            ('can_switch_between_cost_breakdowns', 'User can switch between stats that include fee and margin and stats that don\'t.'),
            ('can_view_breakdown_by_delivery', 'User can view breakdowns by delivery.'),
            ('account_custom_audiences_view', 'User can manage custom audiences.'),
            ('can_target_custom_audiences', 'User can target custom audiences.'),
            ('can_set_time_period_in_scheduled_reports', 'User can set time period when creating scheduled reports'),
            ('can_set_day_of_week_in_scheduled_reports', 'User can set day of week when creating scheduled reports'),
            ('can_see_agency_managers_under_access_permissions', 'User can see agency managers under access permissions'),
            ('can_promote_agency_managers', 'User can promote agency managers on account settings tab'),
            ('group_agency_manager_add', 'Agency managers are added to this group when promoted'),
            ('can_set_agency_for_account', 'User can set agency for account'),
            ('can_use_single_ad_upload', 'User can use single content ad upload'),
            ('can_toggle_new_design', 'User can toggle between old and new design'),
            ('can_see_new_header', 'User can see new header'),
            ('can_see_new_filter_selector', 'User can see new filter selector'),
            ('can_see_new_infobox', 'User can see new infobox'),
            ('can_see_new_theme', 'User can see new theme'),
            ('can_use_partial_updates_in_upload', 'Partially update upload candidate fields'),
            ('can_use_own_images_in_upload', 'User can use their own images in upload'),
            ('can_see_all_users_for_managers', 'User can see all users when selecting account or campaign manager'),
            ('can_include_totals_in_reports', 'Can include totals in reports'),
            ('can_view_additional_targeting', 'Can view additional targeting'),
            ('bulk_actions_on_all_levels', 'User can do bulk actions on all levels'),
            ('can_see_landing_mode_alerts', 'User can see landing mode alerts above tables'),
            ('can_manage_oauth2_apps', 'User can manage OAuth2 applications'),
            ('can_use_restapi', 'User can use the REST API'),
            ('can_see_new_settings', 'User can see new settings'),
            ('can_access_publisher_reports', 'User can generate publisher reports'),
            ('can_see_rtb_sources_as_one', 'User can see RTB Sources grouped as one'),
            ('can_set_interest_targeting', 'User can set and see interest targeting settings'),
            ('can_edit_content_ads', 'User can use edit form to edit existing content ads'),
            ('can_edit_publisher_groups', 'User can edit publisher groups'),
            ('can_set_white_blacklist_publisher_groups', 'User can set white or blacklist publisher groups'),
            ('can_access_additional_outbrain_publisher_settings',
             'User can see, set or edit additional Outbrain specific publisher settings'),
            ('can_see_pixel_traffic', 'User can see pixel traffic in pixels table'),
            ('can_set_rtb_sources_as_one_cpc', 'User can see and set the bid CPC for RTB Sources grouped as one'),
            ('can_see_new_chart', 'User can see new chart component'),
            ('can_see_new_user_permissions', 'User can see new user permissions page'),
            ('can_see_new_content_insights', 'User can see new content insights component'),
            ('can_see_history_in_drawer', 'User can see history in drawer'),
            ('can_see_new_account_credit', 'User can see new account credit component'),
            ('can_see_new_budgets', 'User can see new campaing budget component'),
            ('can_see_new_scheduled_reports', 'User can see new scheduled reports component'),
            ('can_see_backend_hacks', 'User can see backend hacks'),
            ('can_redirect_pixels', 'User can set redirect url for pixels'),
            ('can_see_pixel_notes', 'User can see pixel notes'),
            ('can_see_new_pixels_view', 'User can see new pixels view'),
            ('can_see_salesforce_url', 'User can see SalesForce URL'),
            ('can_set_account_cs_representative', 'Can view and set account CS representative on account settings tab.'),
            ('campaign_settings_cs_rep', 'Can be chosen as CS representative.'),
            ('can_download_custom_reports', 'Can download custom reports.'),
            ('can_receive_pacing_email', 'Can receive pacing emails.'),
            ('can_see_publisher_groups_ui', 'Can see publisher groups UI'),
            ('can_receive_sales_credit_email', 'Can receive depleting credit emails.'),
            ('can_see_new_report_download', 'User can see new report download.'),
            ('can_use_new_routing', 'User can use new routing.'),
            ('can_see_id_columns_in_table', 'User can see id columns in table.'),
            ('fea_new_geo_targeting', 'Feature: new geo targeting widget.'),
            ('can_set_advanced_device_targeting', 'User can set advanced device targeting.'),
            ('can_see_new_report_schedule', 'User can see new report schedule.'),
            ('can_clone_contentads', 'User can clone content ads.'),
            ('can_clone_adgroups', 'User can clone ad groups.'),
            ('can_see_publishers_all_levels', 'User can see publishers on all levels.'),
            ('fea_can_see_video_metrics', 'User can see video metrics.'),
            ('fea_can_see_roas', 'User can see ROAS-related things.'),
            ('can_use_bluekai_targeting', 'User can use bluekai targeting'),
            ('can_see_realtime_spend', 'User can see realtime spend'),
            ('fea_video_upload', 'User can upload videos'),
            ('can_set_delivery_type', 'User can set delivery type.'),
            ('can_set_click_capping', 'User can set click capping on ad group level.'),
            ('can_see_grid_actions', 'User can see grid actions'),
            ('can_create_campaign_via_campaign_launcher', 'User can create new campaign via Campaign launcher'),
            ('fea_can_see_inventory_planning', 'User can use the inventory planning tool'),
            ('fea_can_use_column_picker_in_reports', 'User can use column picker in reports modal.'),
            ('disable_budget_management', 'User can NOT manage campaign budgets (negated permission)'),
            ('can_view_breakdown_by_delivery_extended', 'User can view extended breakdowns by delivery.'),
            ('can_breakdown_reports_by_ads_and_publishers', 'User can breakdown reports by ad and publishers'),
            ('can_see_all_accounts', 'User can see all accounts.'),
            ('can_see_campaign_language_choices', 'User can see campaign language choices'),
            ('can_see_stats_in_local_currency', 'User can see stats in local currency'),
            ('can_use_ad_additional_data', 'User can use the additionalData field on content ad'),
            ('can_manage_goals_in_local_currency', 'User can manage goals in local currency'),
            ('can_manage_settings_in_local_currency', 'User can manage settings in local currency'),
            ('can_see_budget_optimization', 'User can see budget optimization settings'),
            ('can_see_infobox_in_local_currency', 'User can see infobox in local currency'),
            ('can_manage_budgets_in_local_currency', 'User can manage budgets in local currency'),
            ('can_see_currency_setting', 'User can see currency setting'),
            ('disable_public_rcs', 'Disable some public features for RCS.'),
            ('can_filter_by_media_source', 'Can filter by media source'),
            ('can_request_accounts_report_in_local_currencies', 'User can request all accounts report in local currencies'),
            ('can_see_vast', 'User can see vast upload option'),
            ('can_manage_restapi_access', 'User can manage REST API access'),
            ('can_manage_credit_refunds', 'User can see and create credit refunds'),
            ('can_see_mediamond_publishers', 'User can see Mediamond publishers in inventory planning'),
            ('can_see_rcs_publishers', 'User can see RCS publishers in inventory planning'),
            ('can_see_newscorp_publishers', 'User can see News Corp publishers in inventory planning'),
        )

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def __str__(self):
        return self.email

    def clean(self):
        if not self.pk and self.__class__.objects.filter(email=self.email.lower).exists():
            raise ValidationError({'email': 'User with this e-mail already exists.'})

    def get_all_permissions_with_access_levels(self):
        if not self.is_active or self.is_anonymous:
            return {}

        perm_cache_name = '_zemauth_permission_cache'
        if not hasattr(self, perm_cache_name):
            if self.is_superuser:
                perms = auth_models.Permission.objects.all().exclude(codename__in=User.SUPERUSER_EXCLUDED_PERMISSIONS)
            else:
                perms = auth_models.Permission.objects.\
                    filter(models.Q(id__in=self.user_permissions.all()) | models.Q(group__in=self.groups.all())).\
                    order_by('id').\
                    distinct('id')

            perms = perms.select_related('content_type')

            public_permissions = auth_models.Permission.objects.\
                filter(pk__in=(x.pk for x in perms)).\
                filter(group__in=auth_models.Group.objects.filter(internalgroup=None))

            public_permissions_ids = [x.pk for x in public_permissions]

            permissions = {
                '{}.{}'.format(
                    x.content_type.app_label, x.codename
                ): x.pk in public_permissions_ids for x in perms
            }

            setattr(self, perm_cache_name, permissions)

        return getattr(self, perm_cache_name)

    def is_self_managed(self):
        return self.email and '@zemanta' not in self.email.lower()


class InternalGroup(models.Model):
    group = models.OneToOneField(auth_models.Group, on_delete=models.PROTECT)

    def __str__(self):
        return self.group.name


class Device(models.Model):
    device_key = models.CharField(max_length=40, primary_key=True)
    expire_date = models.DateTimeField(db_index=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserDevice')


class UserDevice(models.Model):
    user = models.ForeignKey(User)
    device = models.ForeignKey(Device)
