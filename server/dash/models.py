from django.contrib.auth import models as auth_models
from django.conf import settings
from django.db import models
import jsonfield

import constants

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
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class Campaign(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    account = models.ForeignKey(Account)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class Network(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
    created_datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        default=constants.AdGroupSettingsStatus.INACTIVE,
        choices=constants.AdGroupSettingsStatus.get_choices()
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    target_devices = jsonfield.JSONField(blank=True)
    target_regions = jsonfield.JSONField(blank=True)
    tracking_code = models.TextField(blank=True)


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)
    created_datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        default=constants.AdGroupNetworkSettingsStatus.INACTIVE,
        choices=constants.AdGroupNetworkSettingsStatus.get_choices()
    )
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
