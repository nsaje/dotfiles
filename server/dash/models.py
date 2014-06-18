from django.conf import settings
from django.contrib import auth
from django.db import models
import jsonfield

from dash import constants


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
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    user_objects = UserAdGroupManager()

    @classmethod
    def get_for_user(cls, id, user):
        sql = '''
        SELECT dag.id, dag.name, dag.campaign_id, dag.created_dt, dag.modified_dt, dag.modified_by_id
        FROM dash_adgroup AS dag
        INNER JOIN dash_campaign AS dc ON dc.id = dag.campaign_id
        LEFT JOIN dash_campaign_users AS dcu ON dcu.campaign_id = dc.id
        LEFT JOIN dash_account_users AS dau ON dau.account_id = dc.account_id
        WHERE dag.id = %(ad_group_id)s AND (dcu.user_id = %(user_id)s OR dau.user_id = %(user_id)s)
        LIMIT 1
        '''

        ad_groups = cls.objects.raw(
            sql, params={'ad_group_id': id, 'user_id': str(user.id)})

        if not ad_groups:
            return None

        return ad_groups[0]

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


class Network(models.Model):
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(
        max_length=127,
        editable=False,
        blank=False,
        null=False
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


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
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


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
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
