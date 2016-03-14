# -*- coding: utf-8 -*-
import jsonfield
import binascii
import datetime
import urlparse
import newrelic.agent

from decimal import Decimal
import pytz
from django.db.models import Sum, Func
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib import auth
from django.db import models, transaction
from django.contrib.postgres.fields import ArrayField
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _
from timezone_field import TimeZoneField

import utils.string_helper

from dash import constants
from dash import region_targeting_helper
from dash import views
import reports.constants
from reports import budget_helpers
from utils import encryption_helpers
from utils import statsd_helper
from utils import exc
from utils import dates_helper


SHORT_NAME_MAX_LENGTH = 22
CC_TO_DEC_MULTIPLIER = Decimal('0.0001')
TO_CC_MULTIPLIER = 10**4
TO_NANO_MULTIPLIER = 10**9


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 0)'


class Coalesce(Func):
    function = 'COALESCE'
    template = '%(function)s(%(expressions)s, 0)'


def nano_to_cc(num):
    return int(round(num * 0.00001))


def nano_to_dec(num):
    return Decimal(nano_to_cc(num) * CC_TO_DEC_MULTIPLIER)


def validate(*validators):
    errors = {}
    for v in validators:
        try:
            v()
        except ValidationError, e:
            errors[v.__name__.replace('validate_', '')] = e.error_list
    if errors:
        raise ValidationError(errors)


def should_filter_by_sources(sources):
    if sources is None:
        return False

    return Source.objects.exclude(id__in=[s.id for s in sources]).exists()


class PermissionMixin(object):
    USERS_FIELD = ''

    def has_permission(self, user, permission=None):
        try:
            if user.is_superuser or (
                    (not permission or user.has_perm(permission)) and
                    getattr(self, self.USERS_FIELD).filter(id=user.id).exists()):
                return True
        except auth.get_user_model().DoesNotExist:
            return False

        return False


class QuerySetManager(models.Manager):

    def get_queryset(self):
        return self.model.QuerySet(self.model)


class DemoManager(models.Manager):

    def get_queryset(self):
        queryset = super(DemoManager, self).get_queryset()
        if queryset.model is Account:
            with statsd_helper.statsd_block_timer('dash.models', 'account_demo_objects'):
                queryset = queryset.filter(
                    campaign__adgroup__in=AdGroup.demo_objects.all()
                ).distinct()
        elif queryset.model is Campaign:
            with statsd_helper.statsd_block_timer('dash.models', 'campaign_demo_objects'):
                queryset = queryset.filter(
                    adgroup__in=AdGroup.demo_objects.all()
                ).distinct()
        else:
            assert queryset.model is AdGroup
            with statsd_helper.statsd_block_timer('dash.models', 'adgroup_demo_objects'):
                queryset = queryset.filter(
                    id__in=(d2r.demo_ad_group_id for d2r in DemoAdGroupRealAdGroup.objects.all())
                )
        return queryset


class FootprintModel(models.Model):

    def __init__(self, *args, **kwargs):
        super(FootprintModel, self).__init__(*args, **kwargs)
        if not self.pk:
            return
        self._footprint()

    def _get_value_fieldname(self, fieldname):
        field = self._meta.get_field(fieldname)
        if field.many_to_one:
            return field.attname
        return fieldname

    def has_changed(self, field=None):
        if not self.pk:
            return False
        if field:
            return self._orig[field] != getattr(self, self._get_value_fieldname(field))
        for f in self._meta.fields:
            if self._orig[f.name] != getattr(self, self._get_value_fieldname(f.name)):
                return True
        return False

    def previous_value(self, fieldname):
        field = self._meta.get_field(fieldname)
        if field.many_to_one:
            raise Exception("Previous value not stored as an object")
        return self.pk and self._orig[fieldname]

    def _footprint(self):
        self._orig = {}
        for f in self._meta.fields:
            self._orig[f.name] = getattr(self, self._get_value_fieldname(f.name))

    def save(self, *args, **kwargs):
        super(FootprintModel, self).save(*args, **kwargs)
        self._footprint()

    class Meta:
        abstract = True


class HistoryModel(models.Model):
    snapshot = jsonfield.JSONField(blank=False, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                   related_name='+', on_delete=models.PROTECT)

    def to_dict(self):
        raise NotImplementedError()

    class Meta:
        abstract = True


class OutbrainAccount(models.Model):
    marketer_id = models.CharField(blank=False, null=False, max_length=255)
    used = models.BooleanField(default=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=True,
        blank=False,
        null=False
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    groups = models.ManyToManyField(auth_models.Group)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    objects = QuerySetManager()
    demo_objects = DemoManager()
    allowed_sources = models.ManyToManyField('Source')

    outbrain_marketer_id = models.CharField(null=True, blank=True, max_length=255)

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ('group_account_automatically_add', 'All new accounts are automatically added to group.'),
        )

    def __unicode__(self):
        return self.name

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Account settings can\'t be fetched because acount hasn\'t been saved yet.'
            )

        settings = AccountSettings.objects.\
            filter(account_id=self.pk).\
            order_by('-created_dt').first()
        if not settings:
            settings = AccountSettings(
                account=self,
                name=self.name
            )

        return settings

    @newrelic.agent.function_trace()
    def can_archive(self):
        for campaign in self.campaign_set.all():
            if not campaign.can_archive():
                return False

        return True

    @newrelic.agent.function_trace()
    def can_restore(self):
        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Account can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for campaign in self.campaign_set.all():
                campaign.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(request)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(request)

    def get_account_url(self, request):
        account_settings_url = request.build_absolute_uri(
            reverse('admin:dash_account_change', args=(self.pk,))
        )
        campaign_settings_url = account_settings_url.replace('http://', 'https://')
        return campaign_settings_url

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user
        super(Account, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            return self.filter(
                models.Q(id__in=Account.demo_objects.all()) |
                models.Q(campaign__adgroup__adgroupsource__source__id__in=sources)
            ).distinct()

        def exclude_archived(self):
            related_settings = AccountSettings.objects.all().filter(
                account__in=self
            ).group_current_settings()

            archived_accounts = AccountSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list(
                'account__id', flat=True
            )
            return self.exclude(pk__in=archived_accounts)


class Campaign(models.Model, PermissionMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    groups = models.ManyToManyField(auth_models.Group)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT, null=True)
    landing_mode = models.BooleanField(default=False)

    USERS_FIELD = 'users'

    objects = QuerySetManager()
    demo_objects = DemoManager()

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    def get_campaign_url(self, request):
        campaign_settings_url = request.build_absolute_uri(
            reverse('admin:dash_campaign_change', args=(self.pk,))
        )
        campaign_settings_url = campaign_settings_url.replace('http://', 'https://')
        return campaign_settings_url

    admin_link.allow_tags = True

    def get_sales_representative(self):
        return self.account.get_current_settings().default_sales_representative

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Campaign settings can\'t be fetched because campaign hasn\'t been saved yet.'
            )

        settings = CampaignSettings.objects.\
            filter(campaign_id=self.pk).\
            order_by('-created_dt').first()
        if not settings:
            settings = CampaignSettings(campaign=self, **CampaignSettings.get_defaults_dict())

        return settings

    def can_archive(self):
        for ad_group in self.adgroup_set.all():
            if not ad_group.can_archive():
                return False

        return True

    def can_restore(self):
        if self.account.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Campaign can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for ad_group in self.adgroup_set.all():
                ad_group.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(request)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Campaign can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(request)

    def save(self, request, *args, **kwargs):
        self.modified_by = None
        if request is not None:
            self.modified_by = request.user
        super(Campaign, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id) |
                models.Q(account__users__id=user.id) |
                models.Q(account__groups__user__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            return self.filter(
                models.Q(id__in=Campaign.demo_objects.all()) |
                models.Q(adgroup__adgroupsource__source__in=sources)
            ).distinct()

        def exclude_archived(self):
            related_settings = CampaignSettings.objects.all().filter(
                campaign__in=self
            ).group_current_settings()

            archived_campaigns = CampaignSettings.objects.all().filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list(
                'campaign__id', flat=True
            )
            return self.exclude(pk__in=archived_campaigns)


class SettingsBase(models.Model):
    _settings_fields = None

    @classmethod
    def get_settings_fields(cls):
        return cls._settings_fields

    def get_settings_dict(self):
        return {settings_key: getattr(self, settings_key) for settings_key in self._settings_fields}

    def get_setting_changes(self, new_settings):
        changes = {}

        current_settings_dict = self.get_settings_dict()
        new_settings_dict = new_settings.get_settings_dict()

        for field_name in self._settings_fields:
            if current_settings_dict[field_name] != new_settings_dict[field_name]:
                changes[field_name] = new_settings_dict[field_name]

        return changes

    @classmethod
    def get_default_value(cls, prop_name):
        return cls.get_defaults_dict().get(prop_name)

    @classmethod
    def get_defaults_dict(cls):
        return {}

    def copy_settings(self):
        new_settings = type(self)()

        for name in self._settings_fields:
            setattr(new_settings, name, getattr(self, name))

        if type(self) == AccountSettings:
            new_settings.account = self.account
        elif type(self) == CampaignSettings:
            new_settings.campaign = self.campaign
        elif type(self) == AdGroupSettings:
            new_settings.ad_group = self.ad_group

        return new_settings

    class Meta:
        abstract = True


class AccountSettings(SettingsBase):
    _settings_fields = [
        'name',
        'archived',
        'default_account_manager',
        'default_sales_representative',
        'service_fee'
    ]

    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, related_name='settings', on_delete=models.PROTECT)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    default_account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    default_sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    service_fee = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        default=Decimal('0.2000'),
    )
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    objects = QuerySetManager()

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(AccountSettings, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created_dt',)

    class QuerySet(models.QuerySet):

        def group_current_settings(self):
            return self.order_by('account_id', '-created_dt').distinct('account')


class CampaignSettings(SettingsBase):
    _settings_fields = [
        'name',
        'campaign_manager',
        'iab_category',
        'campaign_goal',
        'goal_quantity',
        'service_fee',
        'promotion_goal',
        'archived',
        'target_devices',
        'target_regions'
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign, related_name='settings', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    campaign_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )

    service_fee = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        default=Decimal('0.2000'),
    )
    iab_category = models.SlugField(
        max_length=10,
        default=constants.IABCategory.IAB24,
        choices=constants.IABCategory.get_choices()
    )
    promotion_goal = models.IntegerField(
        default=constants.PromotionGoal.BRAND_BUILDING,
        choices=constants.PromotionGoal.get_choices()
    )
    campaign_goal = models.IntegerField(
        default=constants.CampaignGoal.NEW_UNIQUE_VISITORS,
        choices=constants.CampaignGoal.get_choices()
    )
    goal_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=False,
        null=False,
        default=0
    )
    target_devices = jsonfield.JSONField(blank=True, default=[])
    target_regions = jsonfield.JSONField(blank=True, default=[])

    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    objects = QuerySetManager()

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(CampaignSettings, self).save(*args, **kwargs)

    @classmethod
    def get_changes_text(cls, old_settings, new_settings, separator=', '):

        if new_settings.changes_text is not None:
            return new_settings.changes_text

        changes = old_settings.get_setting_changes(new_settings) if old_settings is not None else None

        if changes is None:
            return 'Created settings'

        change_strings = []

        for key, value in changes.iteritems():
            prop = cls.get_human_prop_name(key)
            val = cls.get_human_value(key, value)
            change_strings.append(
                u'{} set to "{}"'.format(prop, val)
            )

        return separator.join(change_strings)

    class Meta:
        ordering = ('-created_dt',)

    class QuerySet(models.QuerySet):

        def group_current_settings(self):
            return self.order_by('campaign_id', '-created_dt').distinct('campaign')

    @classmethod
    def get_defaults_dict(cls):
        return {
            'target_devices': constants.AdTargetDevice.get_all(),
            'target_regions': ['US']
        }

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'name': 'Name',
            'campaign_manager': 'Campaign Manager',
            'iab_category': 'IAB Category',
            'campaign_goal': 'Campaign Goal',
            'goal_quantity': 'Goal Quantity',
            'service_fee': 'Service Fee',
            'promotion_goal': 'Promotion Goal',
            'archived': 'Archived',
            'target_devices': 'Device targeting',
            'target_regions': 'Locations',
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'campaign_manager':
            value = views.helpers.get_user_full_name_or_email(value).decode('utf-8')
        elif prop_name == 'iab_category':
            value = constants.IABCategory.get_text(value)
        elif prop_name == 'campaign_goal':
            value = constants.CampaignGoal.get_text(value)
        elif prop_name == 'service_fee':
            value = views.helpers.format_decimal_to_percent(value) + '%'
        elif prop_name == 'promotion_goal':
            value = constants.PromotionGoal.get_text(value)
        elif prop_name == 'target_devices':
            value = ', '.join(constants.AdTargetDevice.get_text(x) for x in value)
        elif prop_name == 'target_regions':
            if value:
                value = ', '.join(constants.AdTargetLocation.get_text(x) for x in value)
            else:
                value = 'worldwide'
        elif prop_name == 'archived':
            value = str(value)

        return value


class CampaignGoal(models.Model):
    campaign = models.ForeignKey(Campaign)
    type = models.PositiveSmallIntegerField(
        default=constants.CampaignGoalKPI.TIME_ON_SITE,
        choices=constants.CampaignGoalKPI.get_choices(),
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        unique_together = ('campaign', 'type')


class CampaignGoalValue(models.Model):
    campaign_goal = models.ForeignKey(CampaignGoal)
    value = models.DecimalField(max_digits=15, decimal_places=5)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)


class SourceType(models.Model):
    type = models.CharField(
        max_length=127,
        unique=True
    )

    available_actions = ArrayField(models.PositiveSmallIntegerField(), null=True, blank=True)

    min_cpc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Minimum CPC'
    )

    min_daily_budget = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Minimum Daily Budget'
    )

    max_cpc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Maximum CPC'
    )

    max_daily_budget = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Maximum Daily Budget'
    )

    cpc_decimal_places = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='CPC Decimal Places'
    )

    delete_traffic_metrics_threshold = models.IntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name='Max clicks allowed to delete per daily report',
        help_text='When we receive an empty report, we don\'t override existing data but we mark report aggregation as failed. But for smaller changes (as defined by this parameter), we do override existing data since they are not material. Zero value means no reports will get deleted.',
    )

    budgets_tz = TimeZoneField(default='America/New_York')

    def can_update_state(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_UPDATE_STATE in self.available_actions

    def can_update_cpc(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_UPDATE_CPC in self.available_actions

    def can_update_daily_budget_manual(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_MANUAL in self.available_actions

    def can_update_daily_budget_automatic(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC in self.available_actions

    def can_manage_content_ads(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MANAGE_CONTENT_ADS in self.available_actions

    def has_3rd_party_dashboard(self):
        return self.available_actions is not None and\
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD in self.available_actions

    def can_modify_start_date(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_START_DATE in self.available_actions

    def can_modify_end_date(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_END_DATE in self.available_actions

    def can_modify_device_targeting(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_DEVICE_TARGETING in self.available_actions

    def can_modify_targeting_for_region_type_automatically(self, region_type):
        if self.available_actions is None:
            return False
        elif region_type == constants.RegionType.COUNTRY:
            return constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING in self.available_actions
        elif region_type == constants.RegionType.SUBDIVISION:
            return constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC in self.available_actions
        elif region_type == constants.RegionType.DMA:
            return constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC in self.available_actions

    def can_modify_targeting_for_region_type_manually(self, region_type):
        ''' Assume automatic targeting support implies manual targeting support

            This addresses the following situation: Imagine targeting
            GB (country) and 693 (DMA) and a SourceType that supports automatic
            DMA targeting and manual country targeting.

            Automatically setting the targeting would be impossible because
            the SourceType does not support modifying country targeting
            automatically.

            Manually setting the targeting would also be impossible because
            the SourceType does not support modifying DMA targeting manually.
            '''
        if self.can_modify_targeting_for_region_type_automatically(region_type):
            return True
        if region_type == constants.RegionType.COUNTRY:
            return True
        elif self.available_actions is None:
            return False
        elif region_type == constants.RegionType.SUBDIVISION:
            return constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL in self.available_actions
        elif region_type == constants.RegionType.DMA:
            return constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL in self.available_actions

    def can_modify_tracking_codes(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES in self.available_actions

    def can_modify_ad_group_name(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_AD_GROUP_NAME in self.available_actions

    def can_modify_ad_group_iab_category_automatic(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC in self.available_actions

    def can_modify_ad_group_iab_category_manual(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL in self.available_actions

    def update_tracking_codes_on_content_ads(self):
        return self.available_actions is not None and\
            constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS in self.available_actions

    def supports_targeting_region_type(self, region_type):
        return\
            self.can_modify_targeting_for_region_type_automatically(region_type) or\
            self.can_modify_targeting_for_region_type_manually(region_type)

    def can_fetch_report_by_publisher(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_FETCH_REPORT_BY_PUBLISHER in self.available_actions

    def can_modify_publisher_blacklist_automatically(self):
        return self.available_actions is not None and\
            constants.SourceAction.CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC in self.available_actions

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = "Source Type"
        verbose_name_plural = "Source Types"


class Source(models.Model):
    id = models.AutoField(primary_key=True)
    source_type = models.ForeignKey(
        SourceType,
        null=True
    )
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    tracking_slug = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        verbose_name='Tracking slug'
    )
    bidder_slug = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name='B1 Slug'
    )
    maintenance = models.BooleanField(default=True)
    deprecated = models.BooleanField(default=False, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    released = models.BooleanField(default=True)
    supports_retargeting = models.BooleanField(
        default=False,
        help_text=_('Designates whether source supports retargeting automatically.')
    )

    supports_retargeting_manually = models.BooleanField(
        default=False,
        help_text=_('Designates whether source supports retargeting via manual action.')
    )

    content_ad_submission_type = models.IntegerField(
        default=constants.SourceSubmissionType.DEFAULT,
        choices=constants.SourceSubmissionType.get_choices()
    )

    def can_update_state(self):
        return self.source_type.can_update_state() and not self.maintenance and not self.deprecated

    def can_update_cpc(self):
        return self.source_type.can_update_cpc() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_manual(self):
        return self.source_type.can_update_daily_budget_manual() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_automatic(self):
        return self.source_type.can_update_daily_budget_automatic() and not self.maintenance and not self.deprecated

    def can_manage_content_ads(self):
        return self.source_type.can_manage_content_ads() and not self.maintenance and not self.deprecated

    def has_3rd_party_dashboard(self):
        return self.source_type.has_3rd_party_dashboard()

    def can_modify_start_date(self):
        return self.source_type.can_modify_start_date() and not self.maintenance and not self.deprecated

    def can_modify_end_date(self):
        return self.source_type.can_modify_end_date() and not self.maintenance and not self.deprecated

    def can_modify_device_targeting(self):
        return self.source_type.can_modify_device_targeting() and not self.maintenance and not self.deprecated

    def can_modify_targeting_for_region_type_automatically(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_automatically(region_type)

    def can_modify_targeting_for_region_type_manually(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_manually(region_type)

    def can_modify_tracking_codes(self):
        return self.source_type.can_modify_tracking_codes() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_name(self):
        return self.source_type.can_modify_ad_group_name() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_iab_category_automatic(self):
        return self.source_type.can_modify_ad_group_iab_category_automatic() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_iab_category_manual(self):
        return self.source_type.can_modify_ad_group_iab_category_manual() and not self.maintenance and not self.deprecated

    def update_tracking_codes_on_content_ads(self):
        return self.source_type.update_tracking_codes_on_content_ads()

    def can_fetch_report_by_publisher(self):
        return self.source_type.can_fetch_report_by_publisher()

    def can_modify_publisher_blacklist_automatically(self):
        return self.source_type.can_modify_publisher_blacklist_automatically() and not self.maintenance and not self.deprecated

    def can_modify_retargeting_automatically(self):
        return self.supports_retargeting and not self.maintenance and not self.deprecated

    def __unicode__(self):
        return self.name


class SourceCredentials(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    credentials = models.TextField(blank=True, null=False)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')

    class Meta:
        verbose_name_plural = "Source Credentials"

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            existing_instance = SourceCredentials.objects.get(id=self.id)
        except SourceCredentials.DoesNotExist:
            existing_instance = None

        if (not existing_instance) or\
           (existing_instance and existing_instance.credentials != self.credentials):
            encrypted_credentials = encryption_helpers.aes_encrypt(
                self.credentials,
                settings.CREDENTIALS_ENCRYPTION_KEY
            )
            self.credentials = binascii.b2a_base64(encrypted_credentials)

        super(SourceCredentials, self).save(*args, **kwargs)

    def decrypt(self):
        if not self.id or not self.credentials:
            return self.credentials

        return encryption_helpers.aes_decrypt(
            binascii.a2b_base64(self.credentials),
            settings.CREDENTIALS_ENCRYPTION_KEY
        )


class DefaultSourceSettings(models.Model):
    source = models.OneToOneField(Source, unique=True, on_delete=models.PROTECT)
    credentials = models.ForeignKey(SourceCredentials, on_delete=models.PROTECT, null=True, blank=True)
    params = jsonfield.JSONField(
        blank=True,
        null=False,
        default={},
        verbose_name='Additional action parameters',
        help_text='Information about format can be found here: <a href="https://sites.google.com/a/zemanta.com/root/content-ads-dsp/additional-source-parameters-format" target="_blank">Zemanta Pages</a>'
    )

    default_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Default CPC'
    )

    mobile_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Default CPC (if ad group is targeting mobile only)'
    )

    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Default daily budget'
    )

    objects = QuerySetManager()

    class QuerySet(models.QuerySet):

        def with_credentials(self):
            return self.exclude(credentials__isnull=True)

    class Meta:
        verbose_name_plural = "Default Source Settings"

    def __unicode__(self):
        return self.source.name


class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT)
    sources = models.ManyToManyField(Source, through='AdGroupSource')
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    is_demo = models.BooleanField(null=False, blank=False, default=False)
    content_ads_tab_with_cms = models.BooleanField(
        null=False,
        blank=False,
        default=True,
        verbose_name='Content ads tab with CMS'
    )

    objects = QuerySetManager()
    demo_objects = DemoManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/'

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/adgroup/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True

    @newrelic.agent.function_trace()
    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Ad group setting couldn\'t be fetched because ad group hasn\'t been saved yet.'
            )

        settings = AdGroupSettings.objects.\
            filter(ad_group_id=self.pk).\
            order_by('created_dt').last()
        if settings is None:
            settings = AdGroupSettings(ad_group=self, **AdGroupSettings.get_defaults_dict())

        return settings

    def can_archive(self):
        current_settings = self.get_current_settings()
        return not self.is_ad_group_active(current_settings)

    def can_restore(self):
        if self.campaign.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @classmethod
    def get_running_status(cls, ad_group_settings, ad_group_sources_settings):
        """
        Returns the actual running status of ad group settings with selected sources settings.
        """

        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        if (cls.get_running_status_by_flight_time(ad_group_settings) == constants.AdGroupRunningStatus.ACTIVE and
                cls.get_running_status_by_sources_setting(ad_group_settings, ad_group_sources_settings) ==
                constants.AdGroupRunningStatus.ACTIVE):
            return constants.AdGroupRunningStatus.ACTIVE

        return constants.AdGroupRunningStatus.INACTIVE

    @classmethod
    def get_running_status_by_flight_time(cls, ad_group_settings):
        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        now = dates_helper.local_today()
        if ad_group_settings.start_date <= now and\
           (ad_group_settings.end_date is None or now <= ad_group_settings.end_date):
            return constants.AdGroupRunningStatus.ACTIVE
        return constants.AdGroupRunningStatus.INACTIVE

    @classmethod
    def get_running_status_by_sources_setting(cls, ad_group_settings, ad_group_sources_settings):
        """
        Returns "running" when at least one of the ad group sources settings status is
        set to be active.
        """
        if not cls.is_ad_group_active(ad_group_settings):
            return constants.AdGroupRunningStatus.INACTIVE

        if ad_group_sources_settings and\
           any(x.state == constants.AdGroupSourceSettingsState.ACTIVE for x in ad_group_sources_settings):
            return constants.AdGroupRunningStatus.ACTIVE
        return constants.AdGroupRunningStatus.INACTIVE

    @classmethod
    def is_ad_group_active(cls, ad_group_settings):
        if ad_group_settings and ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
            return True
        return False

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Ad group has to be in state "Paused" in order to archive it.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(request)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account and campaign have to not be archived in order to restore an ad group.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(request)

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user
        super(AdGroup, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):
        def filter_by_user(self, user):
            return self.filter(
                models.Q(campaign__users__id=user.id) |
                models.Q(campaign__groups__user__id=user.id) |
                models.Q(campaign__account__users__id=user.id) |
                models.Q(campaign__account__groups__user__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            return self.filter(
                models.Q(id__in=AdGroup.demo_objects.all()) |
                models.Q(adgroupsource__source__in=sources)
            ).distinct()

        def exclude_archived(self):
            related_settings = AdGroupSettings.objects.all().filter(
                ad_group__in=self
            ).group_current_settings()

            archived_adgroups = AdGroupSettings.objects.filter(
                pk__in=related_settings
            ).filter(
                archived=True
            ).values_list('ad_group', flat=True)

            return self.exclude(pk__in=archived_adgroups)

        def filter_running(self):
            """
            This function checks if adgroup is active on arbitrary number of adgroups
            with a fixed amount of queries.
            An adgroup is active if:
                - it was set as active(adgroupsettings)
                - current date is between start and stop(flight time)
                - has at least one running mediasource(adgroupsourcesettings)
            """
            now = dates_helper.local_today()
            # ad group settings and ad group source settings
            # are fetched in a separate queryset
            # because getting current settings and filtering them
            # in one qs could cause latest settings to be filtered out
            # but we want to take only latest settings into account
            latest_ad_group_settings = AdGroupSettings.objects.filter(
                ad_group__in=self
            ).group_current_settings()

            ad_group_settings = AdGroupSettings.objects.filter(
                pk__in=latest_ad_group_settings
            ).filter(
                state=constants.AdGroupSettingsState.ACTIVE,
                start_date__lte=now
            ).exclude(
                end_date__isnull=False,
                end_date__lt=now
            ).values_list('ad_group__id', flat=True)

            latest_ad_group_source_settings = AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group__in=self
            ).group_current_settings()

            ad_group_source_settings = AdGroupSourceSettings.objects.filter(
                pk__in=latest_ad_group_source_settings
            ).filter(
                state=constants.AdGroupSourceSettingsState.ACTIVE
            ).values_list('ad_group_source__ad_group__id', flat=True)

            ids = set(ad_group_settings) & set(ad_group_source_settings)
            return self.filter(id__in=ids)

    class Meta:
        ordering = ('name',)


class AdGroupSource(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.PROTECT)

    source_credentials = models.ForeignKey(SourceCredentials, null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_reports_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_status_sync_dt = models.DateTimeField(blank=True, null=True)
    can_manage_content_ads = models.BooleanField(null=False, blank=False, default=False)

    source_content_ad_id = models.CharField(max_length=100, null=True, blank=True)
    submission_status = models.IntegerField(
        default=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
        choices=constants.ContentAdSubmissionStatus.get_choices()
    )
    submission_errors = models.TextField(
        blank=True,
        null=True
    )

    objects = QuerySetManager()

    class QuerySet(models.QuerySet):

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            return self.filter(source__in=sources)

    def get_tracking_ids(self):
        msid = self.source.tracking_slug or ''
        if self.source.source_type and\
           self.source.source_type.type in [
                constants.SourceType.ZEMANTA, constants.SourceType.B1, constants.SourceType.OUTBRAIN]:
            msid = '{sourceDomain}'

        return '_z1_adgid={}&_z1_msid={}'.format(self.ad_group_id, msid)

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.ad_group.campaign.account.name
        campaign_name = self.ad_group.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.ad_group.name
        else:
            ad_group_name = new_adgroup_name
        ad_group_id = self.ad_group.id
        source_name = self.source.name
        return u'ONE: {} / {} / {} / {} / {}'.format(
            self._shorten_name(account_name),
            self._shorten_name(campaign_name),
            self._shorten_name(ad_group_name),
            ad_group_id,
            source_name
        )

    def get_supply_dash_url(self):
        if not self.source.has_3rd_party_dashboard() or\
                self.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
            return None

        return '{}?ad_group_id={}&source_id={}'.format(
            reverse('dash.views.views.supply_dash_redirect'),
            self.ad_group.id,
            self.source.id
        )

    def get_latest_state(self):
        try:
            return AdGroupSourceState.objects.filter(
                ad_group_source=self
            ).latest()
        except AdGroupSourceState.DoesNotExist:
            return None

    def _shorten_name(self, name):
        # if the first word is too long, cut it
        words = name.split()
        if not len(words) or len(words[0]) > SHORT_NAME_MAX_LENGTH:
            return name[:SHORT_NAME_MAX_LENGTH]

        while len(name) > SHORT_NAME_MAX_LENGTH:
            name = name.rsplit(None, 1)[0]

        return name

    def get_current_settings(self):
        current_settings = self.get_current_settings_or_none()
        return current_settings if current_settings else \
            AdGroupSourceSettings(ad_group_source=self)

    def get_current_settings_or_none(self):
        if not self.pk:
            raise exc.BaseError(
                'Ad group source settings can\'t be fetched because ad group source hasn\'t been saved yet.'
            )

        try:
            return AdGroupSourceSettings.objects\
                                        .filter(ad_group_source_id=self.pk)\
                                        .latest('created_dt')
        except ObjectDoesNotExist:
            return None

    def save(self, request=None, *args, **kwargs):
        super(AdGroupSource, self).save(*args, **kwargs)
        if not AdGroupSourceSettings.objects.filter(ad_group_source=self).exists():
            settings = AdGroupSourceSettings(ad_group_source=self)
            settings.save(request)

    def __unicode__(self):
        return u'{} - {}'.format(self.ad_group, self.source)

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')


class AdGroupSettings(SettingsBase):
    _settings_fields = [
        'state',
        'start_date',
        'end_date',
        'cpc_cc',
        'daily_budget_cc',
        'target_devices',
        'target_regions',
        'retargeting_ad_groups',
        'tracking_code',
        'archived',
        'display_url',
        'brand_name',
        'description',
        'call_to_action',
        'ad_group_name',
        'enable_ga_tracking',
        'ga_tracking_type',
        'enable_adobe_tracking',
        'adobe_tracking_param',
        'autopilot_state',
        'autopilot_daily_budget',
    ]

    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup, related_name='settings', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   on_delete=models.PROTECT, null=True, blank=True)
    state = models.IntegerField(
        default=constants.AdGroupSettingsState.INACTIVE,
        choices=constants.AdGroupSettingsState.get_choices()
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Maximum CPC'
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily budget'
    )
    target_devices = jsonfield.JSONField(blank=True, default=[])
    target_regions = jsonfield.JSONField(blank=True, default=[])
    retargeting_ad_groups = jsonfield.JSONField(blank=True, default=[])
    tracking_code = models.TextField(blank=True)
    enable_ga_tracking = models.BooleanField(default=True)
    ga_tracking_type = models.IntegerField(
        default=constants.GATrackingType.EMAIL,
        choices=constants.GATrackingType.get_choices()
    )
    enable_adobe_tracking = models.BooleanField(default=False)
    adobe_tracking_param = models.CharField(max_length=10, blank=True, default='')
    archived = models.BooleanField(default=False)
    display_url = models.CharField(max_length=25, blank=True, default='')
    brand_name = models.CharField(max_length=25, blank=True, default='')
    description = models.CharField(max_length=140, blank=True, default='')
    call_to_action = models.CharField(max_length=25, blank=True, default='')
    ad_group_name = models.CharField(max_length=127, blank=True, default='')
    autopilot_state = models.IntegerField(
        blank=True,
        null=True,
        default=constants.AdGroupSettingsAutopilotState.INACTIVE,
        choices=constants.AdGroupSettingsAutopilotState.get_choices()
    )
    autopilot_daily_budget = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Auto-Pilot\'s Daily Budget',
        default=0
    )

    changes_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ("settings_view", "Can view settings in dashboard."),
        )

    def _convert_date_utc_datetime(self, date):
        dt = datetime.datetime(
            date.year,
            date.month,
            date.day,
            tzinfo=pytz.timezone(settings.DEFAULT_TIME_ZONE)
        )
        return dt.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)

    def get_utc_start_datetime(self):
        if self.start_date is None:
            return None

        return self._convert_date_utc_datetime(self.start_date)

    def get_utc_end_datetime(self):
        if self.end_date is None:
            return None

        dt = self._convert_date_utc_datetime(self.end_date)
        dt += datetime.timedelta(days=1)
        return dt

    def targets_region_type(self, region_type):
        regions = region_targeting_helper.get_list_for_region_type(region_type)

        return any(target_region in regions for target_region in self.target_regions or [])

    def get_targets_for_region_type(self, region_type):
        regions_of_type = region_targeting_helper.get_list_for_region_type(region_type)

        return [target_region for target_region in self.target_regions or [] if target_region in regions_of_type]

    def get_target_names_for_region_type(self, region_type):
        regions_of_type = region_targeting_helper.get_list_for_region_type(region_type)

        return [regions_of_type[target_region] for target_region
                in self.target_regions or [] if target_region in regions_of_type]

    def is_mobile_only(self):
        return bool(self.target_devices) \
            and len(self.target_devices) == 1 \
            and constants.AdTargetDevice.MOBILE in self.target_devices

    @classmethod
    def get_defaults_dict(cls):
        return {
            'state': constants.AdGroupSettingsState.INACTIVE,
            'start_date': dates_helper.utc_today(),
            'cpc_cc': None,
            'daily_budget_cc': 10.0000,
            'target_devices': constants.AdTargetDevice.get_all(),
            'target_regions': ['US'],
            'autopilot_state': constants.AdGroupSettingsAutopilotState.INACTIVE,
            'autopilot_daily_budget': 0.00
        }

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'start_date': 'Start date',
            'end_date': 'End date',
            'cpc_cc': 'Max CPC bid',
            'daily_budget_cc': 'Daily budget',
            'target_devices': 'Device targeting',
            'target_regions': 'Locations',
            'retargeting_ad_groups': 'Retargeting ad groups',
            'tracking_code': 'Tracking code',
            'state': 'State',
            'archived': 'Archived',
            'display_url': 'Display URL',
            'brand_name': 'Brand name',
            'description': 'Description',
            'call_to_action': 'Call to action',
            'ad_group_name': 'Ad group name',
            'enable_ga_tracking': 'Enable GA tracking',
            'ga_tracking_type': 'GA tracking type (via API or e-mail).',
            'autopilot_state': 'Auto-Pilot',
            'autopilot_daily_budget': 'Auto-Pilot\'s Daily Budget',
            'enable_adobe_tracking': 'Enable Adobe tracking',
            'adobe_tracking_param': 'Adobe tracking parameter'
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'state':
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == 'autopilot_state':
            value = constants.AdGroupSettingsAutopilotState.get_text(value)
        elif prop_name == 'autopilot_daily_budget' and value is not None:
            value = '$' + utils.string_helper.format_decimal(value, 2, 2)
        elif prop_name == 'end_date' and value is None:
            value = 'I\'ll stop it myself'
        elif prop_name == 'cpc_cc' and value is not None:
            value = '$' + utils.string_helper.format_decimal(value, 2, 3)
        elif prop_name == 'daily_budget_cc' and value is not None:
            value = '$' + utils.string_helper.format_decimal(value, 2, 2)
        elif prop_name == 'target_devices':
            value = ', '.join(constants.AdTargetDevice.get_text(x) for x in value)
        elif prop_name == 'target_regions':
            if value:
                value = ', '.join(constants.AdTargetLocation.get_text(x) for x in value)
            else:
                value = 'worldwide'
        elif prop_name == 'retargeting_ad_groups':
            names = AdGroup.objects.filter(pk__in=value).values_list('name', flat=True)
            value = ', '.join(names)
        elif prop_name in ('archived', 'enable_ga_tracking', 'enable_adobe_tracking'):
            value = str(value)
        elif prop_name == 'ga_tracking_type':
            value = constants.GATrackingType.get_text(value)

        return value

    @classmethod
    def get_changes_text(cls, old_settings, new_settings, user, separator=', '):

        if new_settings.changes_text is not None:
            return new_settings.changes_text

        changes = old_settings.get_setting_changes(new_settings) if old_settings is not None else None

        if changes is None:
            return 'Created settings'

        change_strings = []

        for key, value in changes.iteritems():
            if key in ['display_url', 'brand_name', 'description', 'call_to_action'] and\
                    not user.has_perm('zemauth.new_content_ads_tab'):
                continue
            if key == 'retargeting_ad_groups' and\
                    not user.has_perm('zemauth.can_view_retargeting_settings'):
                continue

            prop = cls.get_human_prop_name(key)
            val = cls.get_human_value(key, value)
            change_strings.append(
                u'{} set to "{}"'.format(prop, val)
            )

        return separator.join(change_strings)

    objects = QuerySetManager()

    def get_tracking_codes(self):
        # Strip the first '?' as we don't want to send it as a part of query string
        return self.tracking_code.lstrip('?')

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            if request is None:
                self.created_by = None
            else:
                self.created_by = request.user

        super(AdGroupSettings, self).save(*args, **kwargs)

    class QuerySet(models.QuerySet):

        def group_current_settings(self):
            return self.order_by('ad_group_id', '-created_dt').distinct('ad_group')


class AdGroupSourceState(models.Model):
    id = models.AutoField(primary_key=True)

    ad_group_source = models.ForeignKey(
        AdGroupSource,
        null=True,
        related_name='states',
        on_delete=models.PROTECT
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    state = models.IntegerField(
        default=constants.AdGroupSourceSettingsState.INACTIVE,
        choices=constants.AdGroupSourceSettingsState.get_choices()
    )
    cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='CPC'
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily budget'
    )

    objects = QuerySetManager()

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)

    class QuerySet(models.QuerySet):

        def group_current_states(self):
            return self.order_by('ad_group_source_id', '-created_dt').distinct('ad_group_source')


class AdGroupSourceSettings(models.Model):
    id = models.AutoField(primary_key=True)

    ad_group_source = models.ForeignKey(
        AdGroupSource,
        null=True,
        related_name='settings',
        on_delete=models.PROTECT
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    state = models.IntegerField(
        default=constants.AdGroupSourceSettingsState.INACTIVE,
        choices=constants.AdGroupSourceSettingsState.get_choices()
    )
    cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='CPC'
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily budget'
    )
    autopilot_state = models.IntegerField(
        default=constants.AdGroupSourceSettingsAutopilotState.INACTIVE,
        choices=constants.AdGroupSourceSettingsAutopilotState.get_choices()
    )

    objects = QuerySetManager()

    def save(self, request, *args, **kwargs):
        if self.pk is None and request is not None:
            self.created_by = request.user

        super(AdGroupSourceSettings, self).save(*args, **kwargs)

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)

    @classmethod
    def get_current_settings(cls, ad_group, sources):
        source_ids = [x.pk for x in sources]

        source_settings = cls.objects.filter(
            ad_group_source__ad_group=ad_group,
        ).order_by('-created_dt')

        result = {}
        for s in source_settings:
            source = s.ad_group_source.source

            if source.id in result:
                continue

            result[source.id] = s

            if len(result) == len(source_ids):
                break

        for sid in source_ids:
            if sid in result:
                continue

            result[sid] = cls(
                state=None,
                ad_group_source=AdGroupSource(
                    ad_group=ad_group,
                    source=Source.objects.get(pk=sid)
                )
            )

        return result

    class QuerySet(models.QuerySet):

        def group_current_settings(self):
            return self.order_by('ad_group_source_id', '-created_dt').distinct('ad_group_source')

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            return self.filter(
                models.Q(id__in=AdGroup.demo_objects.all()) |
                models.Q(ad_group_source__source__in=sources)
            ).distinct()


class UploadBatch(models.Model):
    name = models.CharField(max_length=1024)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    status = models.IntegerField(
        default=constants.UploadBatchStatus.IN_PROGRESS,
        choices=constants.UploadBatchStatus.get_choices()
    )
    error_report_key = models.CharField(max_length=1024, null=True, blank=True)
    num_errors = models.PositiveIntegerField(null=True)

    processed_content_ads = models.PositiveIntegerField(null=True)
    inserted_content_ads = models.PositiveIntegerField(null=True)
    propagated_content_ads = models.PositiveIntegerField(null=True)
    cancelled = models.BooleanField(default=False)
    batch_size = models.PositiveIntegerField(null=True)

    class Meta:
        get_latest_by = 'created_dt'


class ContentAd(models.Model):
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)
    display_url = models.CharField(max_length=25, blank=True, default='')
    brand_name = models.CharField(max_length=25, blank=True, default='')
    description = models.CharField(max_length=140, blank=True, default='')
    call_to_action = models.CharField(max_length=25, blank=True, default='')

    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)
    batch = models.ForeignKey(UploadBatch, on_delete=models.PROTECT)
    sources = models.ManyToManyField(Source, through='ContentAdSource')

    image_id = models.CharField(max_length=256, editable=False, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    crop_areas = models.CharField(max_length=128, null=True)

    redirect_id = models.CharField(max_length=128, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    state = models.IntegerField(
        null=True,
        default=constants.ContentAdSourceState.ACTIVE,
        choices=constants.ContentAdSourceState.get_choices()
    )

    archived = models.BooleanField(default=False)
    tracker_urls = ArrayField(models.CharField(max_length=2048), null=True)

    objects = QuerySetManager()

    def get_original_image_url(self, width=None, height=None):
        if self.image_id is None:
            return None

        return '{z3_image_url}{image_id}.jpg'.format(z3_image_url=settings.Z3_API_IMAGE_URL, image_id=self.image_id)

    def get_image_url(self, width=None, height=None):
        if self.image_id is None:
            return None

        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return '/'.join([
            settings.Z3_API_THUMBNAIL_URL,
            self.image_id,
            '{}x{}.jpg'.format(width, height)
        ])

    def url_with_tracking_codes(self, tracking_codes):
        if not tracking_codes:
            return self.url

        parsed = list(urlparse.urlparse(self.url))

        parts = []
        if parsed[4]:
            parts.append(parsed[4])
        parts.append(tracking_codes)

        parsed[4] = '&'.join(parts)

        return urlparse.urlunparse(parsed)

    def __unicode__(self):
        return '{cn}(id={id}, ad_group={ad_group}, image_id={image_id}, state={state})'.format(
            cn=self.__class__.__name__,
            id=self.id,
            ad_group=self.ad_group,
            image_id=self.image_id,
            state=self.state,
        )

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')

    class Meta:
        get_latest_by = 'created_dt'

    class QuerySet(models.QuerySet):

        def filter_by_sources(self, sources):
            if not should_filter_by_sources(sources):
                return self

            content_ad_ids = ContentAdSource.objects.filter(source=sources).select_related(
                'content_ad').distinct('content_ad_id').values_list('content_ad_id', flat=True)

            return self.filter(id__in=content_ad_ids)

        def exclude_archived(self):
            return self.filter(archived=False)

        def only_archived(self):
            return self.filter(archived=True)


class ContentAdSource(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    content_ad = models.ForeignKey(ContentAd, on_delete=models.PROTECT)

    submission_status = models.IntegerField(
        default=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
        choices=constants.ContentAdSubmissionStatus.get_choices()
    )
    submission_errors = models.TextField(
        blank=True,
        null=True
    )

    state = models.IntegerField(
        null=True,
        default=constants.ContentAdSourceState.INACTIVE,
        choices=constants.ContentAdSourceState.get_choices()
    )
    source_state = models.IntegerField(
        null=True,
        default=constants.ContentAdSourceState.INACTIVE,
        choices=constants.ContentAdSourceState.get_choices()
    )

    source_content_ad_id = models.CharField(max_length=50, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')

    def get_source_id(self):
        if self.source.source_type and self.source.source_type.type in [
                constants.SourceType.B1, constants.SourceType.GRAVITY]:
            return self.content_ad_id
        else:
            return self.source_content_ad_id

    def __unicode__(self):
        return '{}(id={}, content_ad={}, source={}, state={}, source_state={}, submission_status={}, source_content_ad_id={})'.format(
            self.__class__.__name__,
            self.id,
            self.content_ad,
            self.source,
            self.state,
            self.source_state,
            self.submission_status,
            self.source_content_ad_id,
        )

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')


class Article(models.Model):
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)

    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        get_latest_by = 'created_dt'
        unique_together = ('ad_group', 'url', 'title')


class CampaignBudgetSettings(models.Model):

    campaign = models.ForeignKey('Campaign', on_delete=models.PROTECT)
    allocate = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=False,
        null=False,
        default=0,
        verbose_name='Allocate amount'
    )
    revoke = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=False,
        null=False,
        default=0,
        verbose_name='Revoke amount'
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=False,
        null=False,
        default=0,
        verbose_name='Total budget'
    )
    comment = models.CharField(max_length=256)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(CampaignBudgetSettings, self).save(*args, **kwargs)

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)


class ConversionPixel(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    slug = models.CharField(blank=False, null=False, max_length=32)
    archived = models.BooleanField(default=False)

    last_sync_dt = models.DateTimeField(default=datetime.datetime.utcnow, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created on')

    class Meta:
        unique_together = ('slug', 'account')


class ConversionGoal(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT)
    type = models.PositiveSmallIntegerField(
        choices=constants.ConversionGoalType.get_choices()
    )
    name = models.CharField(max_length=100)

    pixel = models.ForeignKey(ConversionPixel, null=True, on_delete=models.PROTECT)
    conversion_window = models.PositiveSmallIntegerField(null=True, blank=True)
    goal_id = models.CharField(max_length=100, null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created on')

    class Meta:
        unique_together = (('campaign', 'name'), ('campaign', 'type', 'goal_id'))

    def get_stats_key(self):
        # map conversion goal to the key under which they are stored in stats database
        if self.type == constants.ConversionGoalType.GA:
            prefix = reports.constants.ReportType.GOOGLE_ANALYTICS
        elif self.type == constants.ConversionGoalType.OMNITURE:
            prefix = reports.constants.ReportType.OMNITURE
        else:
            raise Exception('Invalid conversion goal type')

        return prefix + '__' + self.goal_id

    def get_view_key(self, conversion_goals):
        # the key in view is based on the index of the conversion goal compared to others for the same campaign
        for i, cg in enumerate(sorted(conversion_goals, key=lambda x: x.id)):
            if cg.id == self.id:
                return 'conversion_goal_' + str(i + 1)

        raise Exception('Conversion goal not found')


class DemoAdGroupRealAdGroup(models.Model):
    demo_ad_group = models.OneToOneField(AdGroup, on_delete=models.PROTECT, related_name='+')
    real_ad_group = models.OneToOneField(AdGroup, on_delete=models.PROTECT, related_name='+')
    multiplication_factor = models.IntegerField(null=False, blank=False, default=1)


class UserActionLog(models.Model):

    id = models.AutoField(primary_key=True)

    action_type = models.PositiveSmallIntegerField(
        choices=constants.UserActionType.get_choices()
    )

    ad_group = models.ForeignKey(AdGroup, null=True, blank=True, on_delete=models.PROTECT)
    ad_group_settings = models.ForeignKey(AdGroupSettings, null=True, blank=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.PROTECT)
    campaign_settings = models.ForeignKey(CampaignSettings, null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT)
    account_settings = models.ForeignKey(AccountSettings, null=True, blank=True, on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT, null=True,
                                   blank=True)


class PublisherBlacklist(models.Model):

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, blank=False, null=False, verbose_name='Publisher name')
    everywhere = models.BooleanField(default=False, verbose_name='globally blacklisted')
    account = models.ForeignKey(Account, null=True, related_name='account', on_delete=models.PROTECT)
    campaign = models.ForeignKey(Campaign, null=True, related_name='campaign', on_delete=models.PROTECT)
    ad_group = models.ForeignKey(AdGroup, null=True, related_name='ad_group', on_delete=models.PROTECT)
    source = models.ForeignKey(Source, null=True, on_delete=models.PROTECT)
    external_id = models.CharField(max_length=127, blank=False, null=True, verbose_name='External ID')

    status = models.IntegerField(
        default=constants.PublisherStatus.BLACKLISTED,
        choices=constants.PublisherStatus.get_choices()
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    def get_blacklist_level(self):
        level = constants.PublisherBlacklistLevel.ADGROUP
        if self.campaign is not None:
            level = constants.PublisherBlacklistLevel.CAMPAIGN
        elif self.account is not None:
            level = constants.PublisherBlacklistLevel.ACCOUNT
        elif self.everywhere:
            level = constants.PublisherBlacklistLevel.GLOBAL
        return level

    def fill_keys(self, ad_group, level):
        self.everywhere = False
        self.account = None
        self.campaign = None
        self.ad_group = None

        if level == constants.PublisherBlacklistLevel.GLOBAL:
            self.everywhere = True
        if level == constants.PublisherBlacklistLevel.ACCOUNT:
            self.account = ad_group.campaign.account
        if level == constants.PublisherBlacklistLevel.CAMPAIGN:
            self.campaign = ad_group.campaign
        if level == constants.PublisherBlacklistLevel.ADGROUP:
            self.ad_group = ad_group

    class Meta:
        unique_together = (('name', 'everywhere', 'account', 'campaign', 'ad_group', 'source'), )


class CreditLineItem(FootprintModel):
    account = models.ForeignKey(Account, related_name='credits', on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()

    amount = models.IntegerField()
    license_fee = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        default=Decimal('0.2000'),
    )

    flat_fee_cc = models.IntegerField(default=0, verbose_name='Flat fee (cc)')
    flat_fee_start_date = models.DateField(blank=True, null=True)
    flat_fee_end_date = models.DateField(blank=True, null=True)

    status = models.IntegerField(
        default=constants.CreditLineItemStatus.PENDING,
        choices=constants.CreditLineItemStatus.get_choices()
    )
    comment = models.CharField(max_length=256, blank=True, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    objects = QuerySetManager()

    def is_active(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        return self.status == constants.CreditLineItemStatus.SIGNED and \
            (self.start_date <= date <= self.end_date)

    def is_past(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        return self.end_date < date

    def get_allocated_amount(self):
        return Decimal(sum(b.allocated_amount() for b in self.budgets.all()))

    def get_overlap(self, start_date, end_date):
        return dates_helper.get_overlap(self.start_date, self.end_date, start_date, end_date)

    def get_monthly_flat_fee(self):
        months = dates_helper.count_months(
            self.flat_fee_start_date,
            self.flat_fee_end_date
        ) + 1
        return self.flat_fee() / Decimal(months)

    def get_flat_fee_on_date_range(self, start_date, end_date):
        if not (self.flat_fee_start_date and self.flat_fee_end_date):
            return Decimal('0.0')
        overlap = dates_helper.get_overlap(
            self.flat_fee_start_date, self.flat_fee_end_date,
            start_date, end_date
        )
        if not all(overlap):
            return Decimal('0.0')
        effective_months = dates_helper.count_months(*overlap) + 1
        return min(
            self.get_monthly_flat_fee() * effective_months,
            self.flat_fee()
        )

    def cancel(self):
        self.status = constants.CreditLineItemStatus.CANCELED
        self.save()

    def delete(self):
        if self.status != constants.CreditLineItemStatus.PENDING:
            raise AssertionError('Credit item is not pending')
        super(CreditLineItem, self).delete()

    def save(self, request=None, *args, **kwargs):
        self.full_clean()
        if request and not self.pk:
            self.created_by = request.user
        super(CreditLineItem, self).save(*args, **kwargs)
        CreditHistory.objects.create(
            created_by=request.user if request else None,
            snapshot=model_to_dict(self),
            credit=self,
        )

    def __unicode__(self):
        return u'{} - {} - ${} - from {} to {}'.format(
            self.account.id, unicode(self.account), self.amount,
            self.start_date, self.end_date)

    def is_editable(self):
        return self.status == constants.CreditLineItemStatus.PENDING

    def flat_fee(self):
        return Decimal(self.flat_fee_cc) * CC_TO_DEC_MULTIPLIER

    def effective_amount(self):
        return Decimal(self.amount) - self.flat_fee()

    def is_available(self):
        return not self.is_past() and self.status == constants.CreditLineItemStatus.SIGNED\
            and (self.effective_amount() - self.get_allocated_amount()) > 0

    def clean(self):
        has_changed = any((
            self.has_changed('start_date'),
            self.has_changed('license_fee'),
        ))

        if has_changed and not self.is_editable():
            raise ValidationError({
                '__all__': ['Nonpending credit line item cannot change.'],
            })

        validate(
            self.validate_end_date,
            self.validate_license_fee,
            self.validate_status,
            self.validate_amount,
            self.validate_flat_fee_cc
        )

        if not self.pk or self.previous_value('status') != constants.CreditLineItemStatus.SIGNED:
            return

        budgets = self.budgets.all()
        if not budgets:
            return

        min_end_date = min(b.end_date for b in budgets)

        if self.has_changed('end_date') and self.end_date < min_end_date:
            raise ValidationError({
                'end_date': ['End date minimum is depending on budgets.'],
            })

    def validate_flat_fee_cc(self):
        if not self.flat_fee_cc:
            return
        delta = self.effective_amount() - self.get_allocated_amount()
        if delta < 0:
            raise ValidationError(
                'Flat fee exceeds the available credit amount by ${}.'.format(
                    -delta.quantize(Decimal('1.00'))
                )
            )

    def validate_amount(self):
        if self.amount < 0:
            raise ValidationError('Amount cannot be negative.')
        if not self.pk or not self.has_changed('amount'):
            return
        prev_amount = self.previous_value('amount')
        budgets = self.budgets.all()

        if prev_amount < self.amount or not budgets:
            return
        if self.effective_amount() < sum(b.allocated_amount() for b in budgets):
            raise ValidationError(
                'Credit line item amount needs to be larger than the sum of budgets.'
            )

    def validate_status(self):
        s = constants.CreditLineItemStatus
        if not self.has_changed('status'):
            return
        if self.status == s.PENDING:
            raise ValidationError('Credit line item status cannot change to PENDING.')

    def validate_end_date(self):
        if not self.end_date:
            return
        if self.has_changed('end_date') and self.previous_value('end_date') > self.end_date:
            raise ValidationError('New end date cannot be before than the previous.')
        if self.start_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be greater than the end date.')

    def validate_license_fee(self):
        if not self.license_fee:
            return
        if not (0 <= self.license_fee < 1):
            raise ValidationError('License fee must be between 0 and 100%.')

    class QuerySet(models.QuerySet):

        def filter_active(self, date=None):
            if date is None:
                date = dates_helper.local_today()
            return self.filter(
                start_date__lte=date,
                end_date__gte=date,
                status=constants.CreditLineItemStatus.SIGNED
            )

        def delete(self):
            if self.exclude(status=constants.CreditLineItemStatus.PENDING).count() != 0:
                raise AssertionError('Some credit items are not pending')
            super(CreditLineItem.QuerySet, self).delete()


class BudgetLineItem(FootprintModel):
    campaign = models.ForeignKey(Campaign, related_name='budgets', on_delete=models.PROTECT)
    credit = models.ForeignKey(CreditLineItem, related_name='budgets', on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()

    amount = models.IntegerField()
    freed_cc = models.BigIntegerField(default=0)

    comment = models.CharField(max_length=256, blank=True, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    objects = QuerySetManager()

    def __unicode__(self):
        return u'${} - from {} to {} (id: {}, campaign: {})'.format(
            self.amount,
            self.start_date,
            self.end_date,
            self.id,
            unicode(self.campaign),
        )

    def save(self, request=None, *args, **kwargs):
        self.full_clean()
        if request and not self.pk:
            self.created_by = request.user
        super(BudgetLineItem, self).save(*args, **kwargs)
        BudgetHistory.objects.create(
            created_by=request.user if request else None,
            snapshot=model_to_dict(self),
            budget=self,
        )

    def db_state(self, date=None):
        return BudgetLineItem.objects.get(pk=self.pk).state(date=date)

    def delete(self):
        if self.db_state() != constants.BudgetLineItemState.PENDING:
            raise AssertionError('Cannot delete nonpending budgets')
        super(BudgetLineItem, self).delete()

    def get_available_amount(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        total_spend = self.get_spend_data(date=date, use_decimal=True)['total']
        return Decimal(self.amount) - total_spend

    def state(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        if self.get_available_amount(date) <= 0:
            return constants.BudgetLineItemState.DEPLETED
        if self.end_date and self.end_date < date:
            return constants.BudgetLineItemState.INACTIVE
        if self.start_date and self.start_date <= date:
            return constants.BudgetLineItemState.ACTIVE
        return constants.BudgetLineItemState.PENDING

    def state_text(self, date=None):
        return constants.BudgetLineItemState.get_text(self.state(date=date))

    def allocated_amount_cc(self):
        return self.amount * TO_CC_MULTIPLIER - self.freed_cc

    def allocated_amount(self):
        return Decimal(self.allocated_amount_cc()) * CC_TO_DEC_MULTIPLIER

    def is_editable(self):
        return self.state() == constants.BudgetLineItemState.PENDING

    def is_updatable(self):
        return self.state() == constants.BudgetLineItemState.ACTIVE

    def free_inactive_allocated_assets(self):
        if self.state() != constants.BudgetLineItemState.INACTIVE:
            raise AssertionError('Budget has to be inactive to be freed.')
        amount_cc = self.amount * TO_CC_MULTIPLIER
        spend_data = self.get_spend_data()

        reserve = self.get_reserve_amount_cc()
        free_date = self.end_date + datetime.timedelta(days=settings.LAST_N_DAY_REPORTS)
        is_over_sync_time = dates_helper.local_today() > free_date

        if is_over_sync_time:
            # After we completed all syncs, free all the assets including reserve
            self.freed_cc = max(0, amount_cc - spend_data['total_cc'])
        elif self.freed_cc == 0 and reserve is not None:
            self.freed_cc = max(
                0, amount_cc - spend_data['total_cc'] - reserve
            )

        self.save()

    def get_reserve_amount_cc(self, factor_offset=0):
        try:
            # try to get previous statement that has more solid data
            statement = list(self.statements.all().order_by('-date')[:2])[-1]
        except IndexError:
            return None
        total_cc = nano_to_cc(
            statement.data_spend_nano + statement.media_spend_nano + statement.license_fee_nano
        )
        return total_cc * (factor_offset + settings.BUDGET_RESERVE_FACTOR)

    def get_latest_statement(self):
        return self.statements.all().order_by('-date').first()

    def get_latest_statement_qs(self):
        latest_statement = self.get_latest_statement()
        if not latest_statement:
            return reports.models.BudgetDailyStatement.objects.none()
        return self.statements.filter(id=latest_statement.id)

    def get_spend_data(self, date=None, use_decimal=False):
        return budget_helpers.calculate_spend_data(
            self.statements,
            date=date,
            use_decimal=use_decimal
        )

    def get_daily_spend(self, date, use_decimal=False):
        statement = date and self.statements.filter(date=date)\
            or self.get_latest_statement_qs()
        return budget_helpers.calculate_spend_data(
            statement,
            date=date,
            use_decimal=use_decimal
        )

    def get_ideal_budget_spend(self, date):
        '''
        Ideal budget spend at END of specified date.
        '''
        if date < self.start_date:
            return 0
        elif date >= self.end_date:
            return self.amount

        date_start_diff = (date - self.start_date).days + 1
        date_total_diff = (self.end_date - self.start_date).days + 1

        return self.amount * Decimal(date_start_diff) / Decimal(date_total_diff)

    def clean(self):
        if self.pk:
            db_state = self.db_state()
            if self.has_changed('start_date') and not db_state == constants.BudgetLineItemState.PENDING:
                raise ValidationError('Only pending budgets can change start date and amount.')
            is_reserve_update = all([
                not self.has_changed('start_date'),
                not self.has_changed('end_date'),
                not self.has_changed('amount'),
                not self.has_changed('campaign'),
            ])
            if not is_reserve_update and db_state not in (constants.BudgetLineItemState.PENDING,
                                                          constants.BudgetLineItemState.ACTIVE,):
                raise ValidationError('Only pending and active budgets can change.')

        validate(
            self.validate_start_date,
            self.validate_end_date,
            self.validate_amount,
            self.validate_credit,
        )

    def license_fee(self):
        return self.credit.license_fee

    def validate_credit(self):
        if self.has_changed('credit'):
            raise ValidationError('Credit cannot change.')
        if self.credit.status != constants.CreditLineItemStatus.SIGNED:
            raise ValidationError('Cannot allocate budget from an unsigned or canceled credit.')

    def validate_start_date(self):
        if not self.start_date:
            return
        if self.start_date < self.credit.start_date:
            raise ValidationError('Start date cannot be smaller than the credit\'s start date.')

    def validate_end_date(self):
        if not self.end_date:
            return
        if self.end_date > self.credit.end_date:
            raise ValidationError('End date cannot be bigger than the credit\'s end date.')
        if self.start_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be bigger than the end date.')

    def validate_amount(self):
        if not self.amount:
            return
        if self.amount < 0:
            raise ValidationError('Amount cannot be negative.')

        budgets = self.credit.budgets.exclude(pk=self.pk)
        delta = self.credit.effective_amount() - sum(b.allocated_amount() for b in budgets) - self.amount
        if delta < 0:
            raise ValidationError(
                'Budget exceeds the total credit amount by ${}.'.format(
                    -delta.quantize(Decimal('1.00'))
                )
            )
        if self.previous_value('amount') > self.amount:
            self._validate_smaller_amount()

    def _validate_smaller_amount(self):
        spend_cc = self.get_spend_data()['total_cc']
        if not spend_cc:
            return
        reserve = self.get_reserve_amount_cc(factor_offset=1)
        minimum_amount = int(float(spend_cc + reserve) / TO_CC_MULTIPLIER + 1)
        if self.amount < minimum_amount:
            raise ValidationError(
                'Budget exceeds the minimum budget amount by ${}.'.format(
                    Decimal(minimum_amount - self.amount).quantize(Decimal('1.00'))
                )
            )

    class QuerySet(models.QuerySet):

        def delete(self):
            if any(itm.state() != constants.BudgetLineItemState.PENDING for itm in self):
                raise AssertionError('Some budget items are not pending')
            super(BudgetLineItem.QuerySet, self).delete()

        def filter_active(self, date=None):
            if date is None:
                date = dates_helper.local_today()
            return self.exclude(
                end_date__lt=date
            ).filter(
                start_date__lte=date
            ).annotate(
                media_spend_sum=Sum('statements__media_spend_nano'),
                license_fee_spend_sum=Sum('statements__license_fee_nano'),
                data_spend_sum=Sum('statements__data_spend_nano')
            ).exclude(
                amount__lte=Round(
                    Coalesce('media_spend_sum') * 1e-9 +
                    Coalesce('license_fee_spend_sum') * 1e-9 +
                    Coalesce('data_spend_sum') * 1e-9
                )
            )


class CreditHistory(HistoryModel):
    credit = models.ForeignKey(CreditLineItem, related_name='history')


class BudgetHistory(HistoryModel):
    budget = models.ForeignKey(BudgetLineItem, related_name='history')


class ExportReport(models.Model):
    id = models.AutoField(primary_key=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=False,
        blank=False,
        on_delete=models.PROTECT
    )

    ad_group = models.ForeignKey(AdGroup, blank=True, null=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey(Campaign, blank=True, null=True, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.PROTECT)

    granularity = models.IntegerField(
        default=constants.ScheduledReportGranularity.CONTENT_AD,
        choices=constants.ScheduledReportGranularity.get_choices()
    )

    breakdown_by_day = models.BooleanField(null=False, blank=False, default=False)
    breakdown_by_source = models.BooleanField(null=False, blank=False, default=False)

    order_by = models.CharField(max_length=20, null=True, blank=True)
    additional_fields = models.CharField(max_length=500, null=True, blank=True)
    filtered_sources = models.ManyToManyField(Source, blank=True)

    def __unicode__(self):
        return u' '.join(filter(None, (
            constants.ScheduledReportLevel.get_text(self.level),
            '(',
            (self.account.name if self.account else ''),
            (self.campaign.name if self.campaign else ''),
            (self.ad_group.name if self.ad_group else ''),
            ') - by',
            constants.ScheduledReportGranularity.get_text(self.granularity),
            ('by Source' if self.breakdown_by_source else ''),
            ('by Day' if self.breakdown_by_day else '')
        )))

    @property
    def level(self):
        if self.account:
            return constants.ScheduledReportLevel.ACCOUNT
        elif self.campaign:
            return constants.ScheduledReportLevel.CAMPAIGN
        elif self.ad_group:
            return constants.ScheduledReportLevel.AD_GROUP
        return constants.ScheduledReportLevel.ALL_ACCOUNTS

    def get_exported_entity_name(self):
        if self.account:
            return self.account.name
        elif self.campaign:
            return self.campaign.name
        elif self.ad_group:
            return self.ad_group.name
        return 'All Accounts'

    def get_additional_fields(self):
        return views.helpers.get_additional_columns(self.additional_fields)

    def get_filtered_sources(self):
        all_sources = Source.objects.all()
        if not self.created_by.has_perm('zemauth.filter_sources') or len(self.filtered_sources.all()) == 0:
            return all_sources
        return all_sources.filter(id__in=[source.id for source in self.filtered_sources.all()])


class ScheduledExportReport(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    report = models.ForeignKey(ExportReport, related_name='scheduled_reports')

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=False,
        blank=False,
        on_delete=models.PROTECT
    )

    state = models.IntegerField(
        default=constants.ScheduledReportState.ACTIVE,
        choices=constants.ScheduledReportState.get_choices()
    )

    sending_frequency = models.IntegerField(
        default=constants.ScheduledReportSendingFrequency.DAILY,
        choices=constants.ScheduledReportSendingFrequency.get_choices()
    )

    def __unicode__(self):
        return u' '.join(filter(None, (
            self.name,
            '(',
            self.created_by.email,
            ') - ',
            constants.ScheduledReportSendingFrequency.get_text(self.sending_frequency),
            '-',
            str(self.report)
        )))

    def add_recipient_email(self, email_address):
        validate_email(email_address)
        if self.recipients.filter(email=email_address).count() < 1:
            self.recipients.create(email=email_address)

    def remove_recipient_email(self, email_address):
        self.recipients.filter(email__exact=email_address).delete()

    def get_recipients_emails_list(self):
        return [recipient.email for recipient in self.recipients.all()]

    def set_recipient_emails_list(self, email_list):
        self.recipients.all().delete()
        for email in email_list:
            self.add_recipient_email(email)


class ScheduledExportReportRecipient(models.Model):
    scheduled_report = models.ForeignKey(ScheduledExportReport, related_name='recipients')
    email = models.EmailField()

    class Meta:
        unique_together = ('scheduled_report', 'email')


class ScheduledExportReportLog(models.Model):
    scheduled_report = models.ForeignKey(ScheduledExportReport)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    report_filename = models.CharField(max_length=1024, blank=False, null=True)
    recipient_emails = models.CharField(max_length=1024, blank=False, null=True)

    state = models.IntegerField(
        default=constants.ScheduledReportSent.FAILED,
        choices=constants.ScheduledReportSent.get_choices(),
    )

    errors = models.TextField(blank=False, null=True)

    def add_error(self, error_msg):
        if self.errors is None:
            self.errors = error_msg
        else:
            self.errors += '\n\n' + error_msg


class GAAnalyticsAccount(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, null=False, blank=False, on_delete=models.PROTECT)
    ga_account_id = models.CharField(max_length=127, blank=False, null=False)
    ga_web_property_id = models.CharField(max_length=127, blank=False, null=False)

    def __unicode__(self):
        return self.account.name
