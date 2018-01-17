# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db import transaction
from dash import constants

import core.common
import core.entity
import core.entity.settings
import core.history


class PublisherGroupManager(core.common.QuerySetManager):

    @transaction.atomic
    def create(self, request, name, account, default_include_subdomains=True, implicit=False):
        if not implicit:
            core.common.entity_limits.enforce(
                PublisherGroup.objects.filter(account=account, implicit=False),
                account.id,
            )

        publisher_group = PublisherGroup(
            name=name,
            account=account,
            default_include_subdomains=default_include_subdomains,
            implicit=implicit)

        publisher_group.save(request)

        return publisher_group


class PublisherGroup(models.Model):
    class Meta:
        app_label = 'dash'
        ordering = ('pk',)

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )

    # it can be defined per account, agency or globaly
    account = models.ForeignKey('Account', on_delete=models.PROTECT, null=True, blank=True)
    agency = models.ForeignKey('Agency', on_delete=models.PROTECT, null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT,
                                    null=True, blank=True)

    implicit = models.BooleanField(default=False)

    default_include_subdomains = models.BooleanField(default=True)

    def save(self, request, *args, **kwargs):
        if request and request.user:
            self.modified_by = request.user
        super(PublisherGroup, self).save(*args, **kwargs)

    objects = PublisherGroupManager()

    class QuerySet(models.QuerySet):

        def filter_by_account(self, account):
            if account.agency:
                return self.filter(models.Q(account=account) | models.Q(agency=account.agency))

            return self.filter(account=account)

        def filter_by_agency(self, agency):
            return self.filter(models.Q(agency=agency))

    def can_delete(self):
        # Check all ad group settings of the corresponding account/agency if they reference the publisher group
        if self.agency:
            ad_groups_settings = core.entity.settings.AdGroupSettings.objects.\
                filter(ad_group__campaign__account__agency=self.agency)
        else:
            ad_groups_settings = core.entity.settings.AdGroupSettings.objects.\
                filter(ad_group__campaign__account=self.account)

        # use `only` instead of `values` so that JSON fields get converted to arrays
        ad_group_settings = ad_groups_settings.group_current_settings().only(
            'whitelist_publisher_groups', 'blacklist_publisher_groups')

        # flatten the list a bit (1 level still remains)
        publisher_groups = [
            x.whitelist_publisher_groups + x.blacklist_publisher_groups for x in ad_group_settings
        ]
        return not any(self.id in x for x in publisher_groups)

    def write_history(self, changes_text, changes, action_type,
                      user=None, system_user=None):

        if not changes and not changes_text:
            return None

        account = self.account
        agency = self.agency
        level = constants.HistoryLevel.ACCOUNT if account else constants.HistoryLevel.AGENCY

        if not agency:
            _, _, agency = core.entity.helpers.generate_parents(account=self)

        return core.history.History.objects.create(
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=changes,
            changes_text=changes_text or "",
            level=level,
            action_type=action_type
        )

    def __unicode__(self):
        return u'{} ({})'.format(self.name, self.id)

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')
