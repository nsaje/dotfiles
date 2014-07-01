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
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

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
    account = models.ForeignKey(Account)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    USERS_FIELD = 'users'

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True


class Network(models.Model):
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
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')

    def __unicode__(self):
        return self.name


class NetworkCredentials(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.ForeignKey(Network)
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
        verbose_name_plural = "Network Credentials"

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        encrypted_credentials = encryption_helpers.aes_encrypt(
            self.credentials,
            settings.CREDENTIALS_ENCRYPTION_KEY
        )

        self.credentials = binascii.b2a_base64(encrypted_credentials)
        super(NetworkCredentials, self).save(*args, **kwargs)


class UserAdGroupManager(models.Manager):
    def get_for_user(self, user):
        queryset = super(UserAdGroupManager, self).get_queryset()
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(models.Q(campaign__users__id=user.id) | models.Q(campaign__account__users__id=user.id))


class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign)
    networks = models.ManyToManyField(Network, through='AdGroupNetwork')
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    objects = models.Manager()
    user_objects = UserAdGroupManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/'

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/adgroup/%d">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True


class AdGroupNetwork(models.Model):
    network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)

    network_credentials = models.ForeignKey(NetworkCredentials, null=True)
    network_campaign_key = jsonfield.JSONField(blank=True, default={})

    def __unicode__(self):
        return '%s - %s' % (self.ad_group, self.network)

    class Meta:

        unique_together = ('network', 'network_campaign_key')


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup, related_name='settings')
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
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


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)

    ad_group_network = models.ForeignKey(AdGroupNetwork, null=True, related_name='settings')

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
    )

    state = models.IntegerField(
        default=constants.AdGroupNetworkSettingsState.INACTIVE,
        choices=constants.AdGroupNetworkSettingsState.get_choices()
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
    def get_current_settings(cls, ad_group):
        network_ids = constants.AdNetwork.get_all()

        network_settings = cls.objects.filter(
            ad_group_network__ad_group=ad_group,
        ).order_by('-created_dt')

        result = {}
        for ns in network_settings:
            network = ns.ad_group_network.network

            if network.id in result:
                continue

            result[network.id] = ns

            if len(result) == len(network_ids):
                break

        for nid in network_ids:
            if nid in result:
                continue

            result[nid] = cls(
                state=None,
                ad_group_network=AdGroupNetwork(
                    ad_group=ad_group,
                    network=Network.objects.get(pk=nid)
                )
            )

        return result


class Article(models.Model):

    url = models.CharField(max_length=2048, editable=False, null=True)
    title = models.CharField(max_length=256, editable=False, null=True)

    ad_group = models.ForeignKey('AdGroup')

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        get_latest_by = 'created_dt'
