from django.core.urlresolvers import reverse
from django.db import transaction

import core.entity

from dash import constants
from utils import json_helper


class CampaignInstanceMixin:

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/campaign/%d/">Edit</a>' % self.id
        else:
            return 'N/A'

    def get_campaign_url(self, request):
        campaign_settings_url = request.build_absolute_uri(
            reverse('admin:dash_campaign_change', args=(self.pk,))
        )
        campaign_settings_url = campaign_settings_url.replace(
            'http://', 'https://')
        return campaign_settings_url

    def get_long_name(self):
        return '{}, Campaign {}'.format(self.account.get_long_name(), self.name)

    admin_link.allow_tags = True

    def get_sales_representative(self):
        return self.account.get_current_settings().default_sales_representative

    def get_cs_representative(self):
        return self.account.get_current_settings().default_cs_representative

    def get_current_settings(self):
        return self.settings

    def can_archive(self):
        for ad_group in self.adgroup_set.all().select_related('settings'):
            if not ad_group.can_archive():
                return False

        for budget in self.budgets.all().annotate_spend_data():
            if budget.state() in (constants.BudgetLineItemState.ACTIVE,
                                  constants.BudgetLineItemState.PENDING):
                return False

        return True

    def can_restore(self):
        if self.account.is_archived():
            return False

        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    @transaction.atomic
    def archive(self, request):
        self.settings.update(request, archived=True)

    @transaction.atomic
    def restore(self, request):
        self.settings.update(request, archived=False)

    def is_in_landing(self):
        current_settings = self.get_current_settings()
        return current_settings.landing_mode

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, account, agency = core.entity.helpers.generate_parents(campaign=self)
        return core.history.History.objects.create(
            campaign=self,
            account=account,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.CAMPAIGN,
            action_type=action_type
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
        custom_flags.update(self.custom_flags or {})
        return custom_flags

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
