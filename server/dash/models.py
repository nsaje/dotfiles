import jsonfield
import binascii
import datetime
import urlparse

from decimal import Decimal
import pytz
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib import auth
from django.db import models, transaction

import utils.string_helper

from dash import constants
from utils import encryption_helpers
from utils import statsd_helper
from utils import exc


SHORT_NAME_MAX_LENGTH = 22


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
                    id__in=(d2r.demo_ad_group.id for d2r in DemoAdGroupRealAdGroup.objects.all())
                )
        return queryset


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
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = AccountSettings(
                account=self,
                name=self.name
            )

        return settings

    def can_archive(self):
        for campaign in self.campaign_set.all():
            if not campaign.can_archive():
                return False

        return True

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
            if set(sources) == set(Source.objects.all()):
                return self

            return self.filter(
                models.Q(id__in=Account.demo_objects.all()) |
                models.Q(campaign__adgroup__adgroupsource__source__id__in=sources)
            ).distinct()

        def exclude_archived(self):
            archived_settings = AccountSettings.objects.\
                distinct('account_id').\
                order_by('account_id', '-created_dt').\
                select_related('account')

            return self.exclude(pk__in=[s.account.id for s in archived_settings if s.archived])


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
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

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

    admin_link.allow_tags = True

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Campaign settings can\'t be fetched because campaign hasn\'t been saved yet.'
            )

        settings = CampaignSettings.objects.\
            filter(campaign_id=self.pk).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = CampaignSettings(
                campaign=self,
                name=self.name
            )

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
            if set(sources) == set(Source.objects.all()):
                return self

            return self.filter(
                models.Q(id__in=Campaign.demo_objects.all()) |
                models.Q(adgroup__adgroupsource__source__in=sources)
            ).distinct()

        def exclude_archived(self):
            archived_settings = CampaignSettings.objects.\
                distinct('campaign_id').\
                order_by('campaign_id', '-created_dt').\
                select_related('campaign')

            return self.exclude(pk__in=[s.campaign.id for s in archived_settings if s.archived])


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
        'archived'
    ]

    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, related_name='settings', on_delete=models.PROTECT)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(AccountSettings, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created_dt',)


class CampaignSettings(SettingsBase):
    _settings_fields = [
        'name',
        'account_manager',
        'sales_representative',
        'service_fee',
        'iab_category',
        'promotion_goal',
        'archived'
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
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    sales_representative = models.ForeignKey(
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
        max_length=5,
        default=constants.IABCategory.IAB24,
        choices=constants.IABCategory.get_choices()
    )
    promotion_goal = models.IntegerField(
        default=constants.PromotionGoal.BRAND_BUILDING,
        choices=constants.PromotionGoal.get_choices()
    )
    archived = models.BooleanField(default=False)

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(CampaignSettings, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created_dt',)


class SourceAction(models.Model):
    action = models.IntegerField(
        primary_key=True,
        choices=constants.SourceAction.get_choices()
    )

    def __str__(self):
        return constants.SourceAction.get_text(self.action)


class SourceType(models.Model):
    type = models.CharField(
        max_length=127,
        unique=True
    )

    available_actions = models.ManyToManyField(
        SourceAction,
        blank=True
    )

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

    def can_update_state(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_STATE).exists()

    def can_update_cpc(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_CPC).exists()

    def can_update_daily_budget_manual(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_MANUAL).exists()

    def can_update_daily_budget_automatic(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC).exists()

    def can_manage_content_ads(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MANAGE_CONTENT_ADS).exists()

    def has_3rd_party_dashboard(self):
        return self.available_actions.filter(action=constants.SourceAction.HAS_3RD_PARTY_DASHBOARD).exists()

    def can_modify_start_date(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_START_DATE).exists()

    def can_modify_end_date(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_END_DATE).exists()

    def can_modify_targeting(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_TARGETING).exists()

    def can_modify_tracking_codes(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_TRACKING_CODES).exists()

    def can_modify_ad_group_name(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_AD_GROUP_NAME).exists()

    def can_modify_ad_group_iab_category(self):
        return self.available_actions.filter(action=constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY).exists()

    def update_tracking_codes_on_content_ads(self):
        return self.available_actions.filter(
            action=constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS
        ).exists()

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

    def can_modify_targeting(self):
        return self.source_type.can_modify_targeting() and not self.maintenance and not self.deprecated

    def can_modify_tracking_codes(self):
        return self.source_type.can_modify_tracking_codes() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_name(self):
        return self.source_type.can_modify_ad_group_name() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_iab_category(self):
        return self.source_type.can_modify_ad_group_iab_category() and not self.maintenance and not self.deprecated

    def update_tracking_codes_on_content_ads(self):
        return self.source_type.update_tracking_codes_on_content_ads()

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

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Ad group setting couln\'t be fetched because ad group hasn\'t been saved yet.'
            )

        settings = AdGroupSettings.objects.\
            filter(ad_group_id=self.pk).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = AdGroupSettings(
                ad_group=self,
                state=constants.AdGroupSettingsState.INACTIVE,
                start_date=datetime.datetime.utcnow().date(),
                cpc_cc=0.4000,
                daily_budget_cc=10.0000,
                target_devices=constants.AdTargetDevice.get_all()
            )

        return settings

    def can_archive(self):
        current_settings = self.get_current_settings()
        return current_settings.state == constants.AdGroupSettingsState.INACTIVE

    def can_restore(self):
        if self.campaign.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

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
            if set(sources) == set(Source.objects.all()):
                return self

            return self.filter(
                models.Q(id__in=AdGroup.demo_objects.all()) |
                models.Q(adgroupsource__source__in=sources)
            ).distinct()

        def exclude_archived(self):
            archived_settings = AdGroupSettings.objects.\
                distinct('ad_group_id').\
                order_by('ad_group_id', '-created_dt').\
                select_related('ad_group')

            return self.exclude(pk__in=[s.ad_group.id for s in archived_settings if s.archived])

    class Meta:
        ordering = ('name',)


class AdGroupSource(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.PROTECT)

    source_credentials = models.ForeignKey(SourceCredentials, null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)
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

    def get_tracking_ids(self):
        msid = None
        if self.source.source_type and\
           self.source.source_type.type in [
                constants.SourceType.ZEMANTA, constants.SourceType.B1, constants.SourceType.OUTBRAIN]:
            msid = '{sourceDomain}'
        elif self.source.tracking_slug is not None and self.source.tracking_slug != '':
            msid = self.source.tracking_slug

        tracking_codes = '_z1_adgid=%s' % (self.ad_group.id)
        if msid is not None:
            tracking_codes += '&_z1_msid=%s' % (msid)

        return tracking_codes

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

    def _shorten_name(self, name):
        # if the first word is too long, cut it
        words = name.split()
        if not len(words) or len(words[0]) > SHORT_NAME_MAX_LENGTH:
            return name[:SHORT_NAME_MAX_LENGTH]

        while len(name) > SHORT_NAME_MAX_LENGTH:
            name = name.rsplit(None, 1)[0]

        return name

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
        'tracking_code',
        'archived',
        'display_url',
        'brand_name',
        'description',
        'call_to_action',
        'ad_group_name'
    ]

    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup, related_name='settings', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
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
        verbose_name='CPC'
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
    tracking_code = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    display_url = models.CharField(max_length=25, blank=True, default='')
    brand_name = models.CharField(max_length=25, blank=True, default='')
    description = models.CharField(max_length=100, blank=True, default='')
    call_to_action = models.CharField(max_length=25, blank=True, default='')
    ad_group_name = models.CharField(max_length=127, blank=True, default='')

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

    @classmethod
    def get_default_value(cls, prop_name):
        DEFAULTS = {
            'state': constants.AdGroupSettingsState.INACTIVE,
            'start_date': datetime.datetime.utcnow().date(),
            'cpc_cc': 0.4000,
            'daily_budget_cc': 10.0000,
            'target_devices': constants.AdTargetDevice.get_all()
        }

        return DEFAULTS.get(prop_name)

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'start_date': 'Start date',
            'end_date': 'End date',
            'cpc_cc': 'Max CPC bid',
            'daily_budget_cc': 'Daily budget',
            'target_devices': 'Device targeting',
            'target_regions': 'Geographic targeting',
            'tracking_code': 'Tracking code',
            'state': 'State',
            'archived': 'Archived',
            'display_url': 'Display URL',
            'brand_name': 'Brand name',
            'description': 'Description',
            'call_to_action': 'Call to action',
            'ad_group_name': 'AdGroup name'
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'state':
            value = constants.AdGroupSourceSettingsState.get_text(value)
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
                value = ', '.join(constants.AdTargetCountry.get_text(x) for x in value)
            else:
                value = 'worldwide'
        elif prop_name == 'archived':
            value = str(value)

        return value

    def get_tracking_codes(self):
        # Strip the first '?' as we don't want to send it as a part of query string
        return self.tracking_code.lstrip('?')

    def save(self, request, *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user

        super(AdGroupSettings, self).save(*args, **kwargs)


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

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)


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


class UploadBatch(models.Model):
    name = models.CharField(max_length=1024)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    status = models.IntegerField(
        default=constants.UploadBatchStatus.IN_PROGRESS,
        choices=constants.UploadBatchStatus.get_choices()
    )
    error_report_key = models.CharField(max_length=1024, null=True, blank=True)
    num_errors = models.PositiveIntegerField(null=True)
    display_url = models.CharField(max_length=25, blank=True, default='')
    brand_name = models.CharField(max_length=25, blank=True, default='')
    description = models.CharField(max_length=100, blank=True, default='')
    call_to_action = models.CharField(max_length=25, blank=True, default='')

    class Meta:
        get_latest_by = 'created_dt'


class ContentAd(models.Model):
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)

    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)
    batch = models.ForeignKey(UploadBatch, on_delete=models.PROTECT)
    sources = models.ManyToManyField(Source, through='ContentAdSource')

    image_id = models.CharField(max_length=256, editable=False, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)

    redirect_id = models.CharField(max_length=128, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    state = models.IntegerField(
        null=True,
        default=constants.ContentAdSourceState.ACTIVE,
        choices=constants.ContentAdSourceState.get_choices()
    )

    objects = QuerySetManager()

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
            if set(sources) == set(Source.objects.all()):
                return self

            content_ad_ids = ContentAdSource.objects.filter(source=sources).select_related(
                'content_ad').distinct('content_ad_id').values_list('content_ad_id', flat=True)

            return self.filter(id__in=content_ad_ids)


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
            return self.content_ad.id
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


class DemoAdGroupRealAdGroup(models.Model):
    demo_ad_group = models.OneToOneField(AdGroup, on_delete=models.PROTECT, related_name='+')
    real_ad_group = models.OneToOneField(AdGroup, on_delete=models.PROTECT, related_name='+')
    multiplication_factor = models.IntegerField(null=False, blank=False, default=1)
