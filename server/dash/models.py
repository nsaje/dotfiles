from django.contrib.auth import models as auth_models
from django.db import models
import jsonfield

from dash import constants


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=True,
        blank=False,
        null=False
    )
    users = models.ManyToManyField(auth_models.User)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(auth_models.User, related_name='+')

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    account = models.ForeignKey(Account)
    users = models.ManyToManyField(auth_models.User)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(auth_models.User, related_name='+')

    def __unicode__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d">Edit</a>' % self.id
        else:
            return 'N/A'

    admin_link.allow_tags = True


class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(auth_models.User, related_name='+')

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
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
    created_dt = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(auth_models.User, related_name='+')
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
        null=True
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True
    )
    target_devices = jsonfield.JSONField(blank=True, default=[])
    target_regions = jsonfield.JSONField(blank=True, default=[])
    tracking_code = models.TextField(blank=True)


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)
    created_dt = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(auth_models.User, related_name='+')
    state = models.IntegerField(
        default=constants.AdGroupNetworkSettingsState.INACTIVE,
        choices=constants.AdGroupNetworkSettingsState.get_choices()
    )
    cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True
    )
