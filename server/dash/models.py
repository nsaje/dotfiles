import jsonfield
import binascii
from decimal import Decimal

from django.conf import settings
from django.contrib import auth
from django.db import models

from dash import constants
from utils import encryption_helpers


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
        if user.is_superuser:
            return queryset
        elif queryset.model is Account:
            return queryset.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id)
            ).distinct()
        elif queryset.model is Campaign:
            return queryset.filter(
                models.Q(users__id=user.id) |
                models.Q(groups__user__id=user.id) |
                models.Q(account__users__id=user.id) |
                models.Q(account__groups__user__id=user.id)
            ).distinct()
        else:
            # AdGroup
            return queryset.filter(
                models.Q(campaign__users__id=user.id) |
                models.Q(campaign__groups__user__id=user.id) |
                models.Q(campaign__account__users__id=user.id) |
                models.Q(campaign__account__groups__user__id=user.id)
            ).distinct()


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

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ('group_account_automatically_add', 'All new accounts are automatically added to group.'),
        )

    def __unicode__(self):
        return self.name


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

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True


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

    class Meta:
        abstract = True


class CampaignSettings(SettingsBase):
    _settings_fields = [
        'name',
        'account_manager',
        'sales_representative',
        'service_fee',
        'iab_category',
        'promotion_goal'
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

    objects = UserAuthorizationManager()

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


class AdGroupSource(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.PROTECT)

    source_credentials = models.ForeignKey(SourceCredentials, null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)

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

    class Meta:
        ordering = ('-created_dt',)

        permissions = (
            ("settings_view", "Can view settings in dashboard."),
        )


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
