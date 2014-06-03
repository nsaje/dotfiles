from django.contrib.auth import models as auth_models
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
    users = models.ManyToManyField(auth_models.User)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

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

    def __unicode__(self):
        return self.name


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

    def __unicode__(self):
        return self.name


# class Network(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(
#         max_length=127,
#         editable=True,
#         blank=False,
#         null=False
#     )
#     created_dt = models.DateTimeField(auto_now_add=True)
#     modified_dt = models.DateTimeField(auto_now=True)
#
#     def __unicode__(self):
#         return self.name


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
    created_dt = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(
        default=constants.AdGroupSettingsState.INACTIVE,
        choices=constants.AdGroupSettingsState.get_choices()
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    target_devices = jsonfield.JSONField(blank=True, default=[])
    target_regions = jsonfield.JSONField(blank=True, default=[])
    tracking_code = models.TextField(blank=True)


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)
    #: Ad network as defined in constants
    network = models.CharField(
        max_length=127,
        choices=constants.AdNetwork.get_choices(),
        blank=False,
        null=False
    )
    #network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)
    created_dt = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(
        default=constants.AdGroupNetworkSettingsState.INACTIVE,
        choices=constants.AdGroupNetworkSettingsState.get_choices()
    )
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
