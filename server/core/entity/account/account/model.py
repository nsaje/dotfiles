# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import utils.demo_anonymizer
import utils.string_helper
from dash import constants

import core.features.yahoo_accounts

from . import instance
from . import manager
from . import queryset


class Account(instance.AccountInstanceMixin,
              models.Model):

    class Meta:
        ordering = ('-created_dt',)

        app_label = 'dash'

    _demo_fields = {'name': utils.demo_anonymizer.account_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=False,
        blank=False,
        null=False
    )
    agency = models.ForeignKey(
        'Agency', on_delete=models.PROTECT, null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    related_name='+', on_delete=models.PROTECT)

    default_whitelist = models.ForeignKey('PublisherGroup', related_name='whitelisted_accounts',
                                          on_delete=models.PROTECT, null=True, blank=True)
    default_blacklist = models.ForeignKey('PublisherGroup', related_name='blacklisted_accounts',
                                          on_delete=models.PROTECT, null=True, blank=True)

    allowed_sources = models.ManyToManyField('Source')

    outbrain_marketer_id = models.CharField(
        null=True, blank=True, max_length=255)
    yahoo_account = models.ForeignKey(
        core.features.yahoo_accounts.YahooAccount, on_delete=models.PROTECT, null=True, blank=True)

    salesforce_url = models.URLField(null=True, blank=True, max_length=255)

    # migration to the new system introduced by margings and fees project
    uses_bcm_v2 = models.BooleanField(
        default=False,
        verbose_name='Margins v2',
        help_text='This account will have license fee and margin included into all costs.'
    )
    custom_flags = JSONField(null=True, blank=True)
    real_time_campaign_stop = models.BooleanField(
        default=False,
        verbose_name='Default to real time campaign stop',
        help_text='Campaigns of this account will use real time campaign stop instead of landing mode.',
    )

    currency = models.CharField(
        max_length=3,
        null=True,
        default=constants.Currency.USD,
        choices=constants.Currency.get_choices()
    )

    settings = models.OneToOneField('AccountSettings', null=True, blank=True, on_delete=models.PROTECT, related_name='latest_for_entity')

    objects = manager.AccountManager.from_queryset(queryset.AccountQuerySet)()
