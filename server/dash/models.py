import jsonfield
import binascii
import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import auth
from django.db import models, transaction

from dash import constants
from utils import encryption_helpers
from utils import statsd_helper
from utils import exc


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


class UserAuthorizationManager(models.Manager):
    def get_for_user(self, user):
        queryset = super(UserAuthorizationManager, self).get_queryset()

        if queryset.model is Account:
            queryset = queryset.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id)
            ).distinct()
        elif queryset.model is Campaign:
            queryset = queryset.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id) |
                models.Q(account__users__id=user.id) |
                models.Q(account__groups__user__id=user.id)
            ).distinct()
        else:
            # AdGroup
            assert queryset.model is AdGroup
            queryset = queryset.filter(
                models.Q(campaign__users__id=user.id) |
                models.Q(campaign__groups__user__id=user.id) |
                models.Q(campaign__account__users__id=user.id) |
                models.Q(campaign__account__groups__user__id=user.id)
            ).distinct()

        return queryset


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
    groups = models.ManyToManyField(auth.models.Group)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    objects = UserAuthorizationManager()
    demo_objects = DemoManager()

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
    def archive(self):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Account can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for campaign in self.campaign_set.all():
                campaign.archive()

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save()

    @transaction.atomic
    def restore(self):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save()


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
    groups = models.ManyToManyField(auth.models.Group)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    USERS_FIELD = 'users'

    objects = UserAuthorizationManager()
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
    def archive(self):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Campaign can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for ad_group in self.adgroup_set.all():
                ad_group.archive()

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save()

    @transaction.atomic
    def restore(self):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Campaign can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save()


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

    class Meta:
        ordering = ('-created_dt',)


class Source(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(
        max_length=127,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    maintenance = models.BooleanField(default=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')

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

    objects = UserAuthorizationManager()
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
                ad_group=self
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
    def archive(self):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Ad group has to be in state "Paused" in order to archive it.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save()

    @transaction.atomic
    def restore(self):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account and campaign have to not be archived in order to restore an ad group.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save()

    class Meta:
        ordering = ('name',)


class AdGroupSource(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.PROTECT)

    source_credentials = models.ForeignKey(SourceCredentials, null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)

    def get_tracking_ids(self):
        if self.source.type == 'zemanta':
            msid = '{sourceDomain}'
        else:
            msid = self.source.name.lower()

        tracking_ids = {
            '_z1_msid': msid,
            '_z1_agid': self.ad_group.id
        }

        return tracking_ids

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
        'archived'
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

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ("settings_view", "Can view settings in dashboard."),
        )

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
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'state':
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == 'end_date' and value is None:
            value = 'I\'ll stop it myself'
        elif prop_name == 'cpc_cc' and value is not None:
            value = '${:.3f}'.format(value)
        elif prop_name == 'daily_budget_cc' and value is not None:
            value = '${:.2f}'.format(value)
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
    created_by = created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)


class DemoAdGroupRealAdGroup(models.Model):
    demo_ad_group = models.ForeignKey(AdGroup, unique=True, on_delete=models.PROTECT, related_name='+')
    real_ad_group = models.ForeignKey(AdGroup, unique=True, on_delete=models.PROTECT, related_name='+')
    multiplication_factor = models.IntegerField(null=False, blank=False, default=1)
