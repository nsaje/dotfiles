# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db import transaction

import core.common
import core.features.history
import core.models
import core.models.settings
from dash import constants

ANNOTATION_QUALIFIED_PUBLISHER_GROUPS = set([16922])


class PublisherGroupManager(core.common.QuerySetManager):
    @transaction.atomic
    def create(self, request, name, account, default_include_subdomains=True, implicit=False):
        if not implicit:
            core.common.entity_limits.enforce(
                PublisherGroup.objects.filter(account=account, implicit=False), account.id
            )

        publisher_group = PublisherGroup(
            name=name, account=account, default_include_subdomains=default_include_subdomains, implicit=implicit
        )

        publisher_group.save(request)

        return publisher_group


class PublisherGroup(models.Model):
    class Meta:
        app_label = "dash"
        ordering = ("pk",)

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, editable=True, blank=False, null=False)

    # it can be defined per account, agency or globaly
    account = models.ForeignKey("Account", on_delete=models.PROTECT, null=True, blank=True)
    agency = models.ForeignKey("Agency", on_delete=models.PROTECT, null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )

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

        def filter_by_active_adgroups(self):
            data = (
                core.models.AdGroup.objects.all()
                .filter_current_and_active()
                .values_list(
                    "default_blacklist_id",
                    "default_whitelist_id",
                    "settings__whitelist_publisher_groups",
                    "settings__blacklist_publisher_groups",
                    "campaign__default_blacklist_id",
                    "campaign__default_whitelist_id",
                    "campaign__settings__whitelist_publisher_groups",
                    "campaign__settings__blacklist_publisher_groups",
                    "campaign__account__default_blacklist_id",
                    "campaign__account__default_whitelist_id",
                    "campaign__account__settings__whitelist_publisher_groups",
                    "campaign__account__settings__blacklist_publisher_groups",
                    "campaign__account__agency__default_blacklist_id",
                    "campaign__account__agency__default_whitelist_id",
                    "campaign__account__agency__settings__whitelist_publisher_groups",
                    "campaign__account__agency__settings__blacklist_publisher_groups",
                )
            )

            ids = set()
            ids.add(settings.GLOBAL_BLACKLIST_ID)
            ids.update(ANNOTATION_QUALIFIED_PUBLISHER_GROUPS)

            self._all_ids_from_values_list_to_set(data, ids)

            return self.filter(id__in=ids)

        def _all_ids_from_values_list_to_set(self, data, ids):
            for line in data:
                for item in line:
                    if not item:
                        continue
                    try:
                        for value in item:
                            if not value:
                                continue
                            ids.add(value)
                    except TypeError:
                        ids.add(item)

    def can_delete(self):
        # Check if any of the ad group, campaign and account settings of the corresponding account/agency reference the publisher group
        if self.agency:
            ad_groups_settings = core.models.settings.AdGroupSettings.objects.filter(
                ad_group__campaign__account__agency=self.agency
            )
            campaigns_settings = core.models.settings.CampaignSettings.objects.filter(
                campaign__account__agency=self.agency
            )
            accounts_settings = core.models.settings.AccountSettings.objects.filter(account__agency=self.agency)
        else:
            ad_groups_settings = core.models.settings.AdGroupSettings.objects.filter(
                ad_group__campaign__account=self.account
            )
            campaigns_settings = core.models.settings.CampaignSettings.objects.filter(campaign__account=self.account)
            accounts_settings = core.models.settings.AccountSettings.objects.filter(account=self.account)

        return not (
            self._is_publisher_group_in_use(ad_groups_settings)
            or self._is_publisher_group_in_use(campaigns_settings)
            or self._is_publisher_group_in_use(accounts_settings)
        )

    def _is_publisher_group_in_use(self, settings_queryset):
        # use `only` instead of `values` so that JSON fields get converted to arrays
        settings = settings_queryset.group_current_settings().only(
            "whitelist_publisher_groups", "blacklist_publisher_groups"
        )

        # flatten the list a bit (1 level still remains)
        publisher_groups = [x.whitelist_publisher_groups + x.blacklist_publisher_groups for x in settings]
        return any(self.id in x for x in publisher_groups)

    def write_history(self, changes_text, changes, action_type, user=None, system_user=None):

        if not changes and not changes_text:
            return None

        account = self.account
        agency = self.agency
        level = constants.HistoryLevel.ACCOUNT if account else constants.HistoryLevel.AGENCY

        if not agency:
            _, _, agency = core.models.helpers.generate_parents(account=self)

        return core.features.history.History.objects.create(
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=changes,
            changes_text=changes_text or "",
            level=level,
            action_type=action_type,
        )

    def __str__(self):
        return "{} ({})".format(self.name, self.id)
