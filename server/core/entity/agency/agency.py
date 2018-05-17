# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField

from dash import constants
from utils import json_helper
from utils import exc

import core.common
import core.entity
import core.features.yahoo_accounts
import core.history
import core.source


class AgencyManager(core.common.QuerySetManager):

    def create(self, request, name, **kwargs):
        agency = Agency(name=name, **kwargs)
        agency.save(request)
        agency.allowed_sources.add(*core.source.Source.objects.filter(released=True, deprecated=False))

        agency.settings = core.entity.settings.AgencySettings(agency=agency)
        agency.settings.update(request)
        agency.settings_id = agency.settings.id
        agency.save(request)

        return agency


class Agency(models.Model):

    class Meta:
        app_label = 'dash'
        verbose_name_plural = 'Agencies'
        ordering = ('-created_dt',)

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=True,
        blank=False,
        null=False
    )
    sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    cs_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    whitelabel = models.CharField(
        max_length=255,
        choices=constants.Whitelabel.get_choices(),
        editable=True,
        unique=False,
        blank=True,
    )
    custom_favicon_url = models.CharField(
        max_length=255,
        editable=True,
        blank=True,
        default='',
    )
    custom_dashboard_title = models.CharField(
        max_length=255,
        editable=True,
        blank=True,
        default='',
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)
    default_account_type = models.IntegerField(
        default=constants.AccountType.UNKNOWN,
        choices=constants.AccountType.get_choices()
    )
    new_accounts_use_bcm_v2 = models.BooleanField(
        default=True,
        verbose_name='Margins v2',
        help_text=('New accounts created by this agency\'s users will have '
                   'license fee and margin included into all costs.')
    )
    allowed_sources = models.ManyToManyField('Source', blank=True)
    custom_flags = JSONField(null=True, blank=True)

    default_whitelist = models.OneToOneField('PublisherGroup', related_name='whitelisted_agencies',
                                             on_delete=models.PROTECT, null=True, blank=True)
    default_blacklist = models.OneToOneField('PublisherGroup', related_name='blacklisted_agencies',
                                             on_delete=models.PROTECT, null=True, blank=True)

    yahoo_account = models.ForeignKey(
        core.features.yahoo_accounts.YahooAccount, on_delete=models.PROTECT, null=True)

    settings = models.OneToOneField('AgencySettings', null=True, blank=True, on_delete=models.PROTECT, related_name='latest_for_entity')

    def get_long_name(self):
        return 'Agency {}'.format(self.name)

    def get_salesforce_id(self):
        return 'a{}'.format(self.pk)

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError(
                'Account settings can\'t be fetched because acount hasn\'t been saved yet.'
            )

        # FIXME:circular dependency
        import core.entity.settings
        settings = core.entity.settings.AgencySettings.objects.\
            filter(agency_id=self.pk).\
            order_by('-created_dt').first()
        if not settings:
            settings = core.entity.settings.AgencySettings(agency=self)

        return settings

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None,
                      action_type=None):
        if not changes and not changes_text:
            return None
        return core.history.History.objects.create(
            agency=self,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.AGENCY,
            action_type=action_type
        )

    def set_new_accounts_use_bcm_v2(self, request, enabled):
        self.new_accounts_use_bcm_v2 = bool(enabled)
        self.save(request)

    def save(self, request, *args, **kwargs):
        self.modified_by = request.user
        super(Agency, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class QuerySet(models.QuerySet):
        def filter_by_user(self, user):
            if user.has_perm('zemauth.can_see_all_accounts'):
                return self
            return self.filter(
                models.Q(users__id=user.id) |
                models.Q(sales_representative__id=user.id) |
                models.Q(cs_representative__id=user.id)
            ).distinct()

    objects = AgencyManager.from_queryset(QuerySet)()
