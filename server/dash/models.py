import jsonfield
import binascii

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
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

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
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    USERS_FIELD = 'users'

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True


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


class UserAdGroupManager(models.Manager):
    def get_for_user(self, user):
        queryset = super(UserAdGroupManager, self).get_queryset()
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(
                models.Q(campaign__users__id=user.id) |
                models.Q(campaign__account__users__id=user.id)
            ).distinct('id')


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

    objects = models.Manager()
    user_objects = UserAdGroupManager()

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

    def __unicode__(self):
        return '%s - %s' % (self.ad_group, self.source)


class AdGroupSettings(models.Model):
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

    @classmethod
    def get_settings_fields(cls):
        return cls._settings_fields

    def get_settings_dict(self):
        return {settings_key: getattr(self, settings_key) for settings_key in self._settings_fields}


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
