from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe

import core.features.deals
import core.models
from dash import constants
from utils import json_helper


class CampaignInstanceMixin:
    def __str__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return mark_safe('<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id)
        else:
            return "N/A"

    def get_campaign_url(self, request):
        campaign_settings_url = request.build_absolute_uri(reverse("admin:dash_campaign_change", args=(self.pk,)))
        campaign_settings_url = campaign_settings_url.replace("http://", "https://")
        return campaign_settings_url

    def get_long_name(self):
        return "{}, Campaign {}".format(self.account.get_long_name(), self.name)

    def get_sales_representative(self):
        return self.account.get_current_settings().default_sales_representative

    def get_cs_representative(self):
        return self.account.get_current_settings().default_cs_representative

    def get_current_settings(self):
        return self.settings

    def can_restore(self):
        if self.account.is_archived():
            return False

        return True

    def is_archived(self):
        return self.archived

    @transaction.atomic
    def archive(self, request):
        self.settings.update(request, archived=True)

    @transaction.atomic
    def restore(self, request):
        self.settings.update(request, archived=False)

    def write_history(self, changes_text, changes=None, user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, account, agency = core.models.helpers.generate_parents(campaign=self)
        return core.features.history.History.objects.create(
            campaign=self,
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.CAMPAIGN,
            action_type=action_type,
        )

    def get_default_blacklist_name(self):
        return "Default blacklist for campaign {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return "Default whitelist for campaign {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.CAMPAIGN

    def get_account(self):
        return self.account

    def get_all_custom_flags(self):
        custom_flags = self.account.get_all_custom_flags()
        if self.custom_flags:
            custom_flags.update({k: v for k, v in self.custom_flags.items() if v})
        return custom_flags

    def get_all_configured_deals(self):
        return core.features.deals.DirectDealConnection.objects.filter(
            Q(campaign=self.id)
            | Q(account=self.account)
            | Q(agency=self.account.agency, agency__isnull=False)
            | Q(agency=None, account=None, campaign=None, adgroup=None)
        )

    def get_deals(self, request):
        deals = (
            core.features.deals.DirectDeal.objects.filter(
                directdealconnection__campaign__isnull=False, directdealconnection__campaign__id=self.id
            )
            .select_related("source")
            .distinct()
        )

        if request and not request.user.has_perm("zemauth.can_see_internal_deals"):
            deals = deals.exclude(is_internal=True)

        return list(deals)

    def remove_deals(self, request, deals):
        self.directdealconnection_set.filter(deal__id__in=[x.id for x in deals]).delete(request=request)

    def add_deals(self, request, deals):
        for deal in deals:
            core.features.deals.DirectDealConnection.objects.create(request, deal, campaign=self)

    def set_real_time_campaign_stop(self, request=None, is_enabled=False):
        self.real_time_campaign_stop = is_enabled
        self.save(request)

    def save(self, request=None, user=None, *args, **kwargs):
        self.modified_by = None
        if request is not None:
            self.modified_by = request.user
        if user is not None:
            self.modified_by = user
        super().save(*args, **kwargs)

    def update_type(self, type=None):
        if type and self.type != type:
            self._validate_type(type)
            self.type = type
            self.save()
