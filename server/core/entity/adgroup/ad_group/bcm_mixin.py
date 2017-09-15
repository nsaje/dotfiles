from django.db import transaction
from django.db.models import Q

import core.bcm
from utils import k1_helper, numbers


class AdGroupBCMMixin(object):
    def get_todays_fee_and_margin(self):
        todays_budget = core.bcm.BudgetLineItem.objects \
            .filter(campaign_id=self.campaign_id) \
            .filter_today() \
            .order_by('id') \
            .first()

        margin = todays_budget.margin if todays_budget else None

        todays_credit = core.bcm.CreditLineItem.objects \
            .filter(
                Q(account_id=self.campaign.account_id) |
                Q(agency_id=self.campaign.account.agency_id)) \
            .filter_active() \
            .order_by('id') \
            .first()
        fee = todays_credit.license_fee if todays_credit else None

        return fee, margin

    @transaction.atomic
    def migrate_to_bcm_v2(self, request):
        fee, margin = self.get_todays_fee_and_margin()
        self._migrate_settings_to_bcm_v2(request, fee, margin)
        self._validate_correct_settings_migration(request)
        self._migrate_ad_group_sources_to_bcm_v2(request, fee, margin)
        k1_helper.update_ad_group(self.id, 'migrate_to_bcm_v2')

    def _migrate_ad_group_sources_to_bcm_v2(self, request, fee, margin):
        for ad_group_source in self.adgroupsource_set.all():
            ad_group_source.migrate_to_bcm_v2(request, fee, margin)

    def _migrate_settings_to_bcm_v2(self, request, fee, margin):
        new_b1_sources_group_daily_budget = self._transform_whole_value(
            self.settings.b1_sources_group_daily_budget, fee, margin)
        new_b1_sources_group_cpc_cc = self._transform_fractional_value(
            self.settings.b1_sources_group_cpc_cc, fee, margin)
        new_cpc_cc = self._transform_fractional_value(
            self.settings.cpc_cc, fee, margin)
        new_max_cpm = self._transform_fractional_value(
            self.settings.max_cpm, fee, margin)
        new_autopilot_daily_budget = self._transform_whole_value(
            self.settings.autopilot_daily_budget, fee, margin)

        self.settings.update(
            request,
            b1_sources_group_daily_budget=new_b1_sources_group_daily_budget,
            b1_sources_group_cpc_cc=new_b1_sources_group_cpc_cc,
            max_cpm=new_max_cpm,
            autopilot_daily_budget=new_autopilot_daily_budget,
            cpc_cc=new_cpc_cc,
        )

    def _validate_correct_settings_migration(self, request):
        # NOTE: We could be saving invalid settings because we skip this part of validation when
        # updating settings.
        campaign_settings = self.campaign.get_current_settings()
        self.settings.clean(request, self, self.settings, self.settings, campaign_settings)

    def _transform_whole_value(self, number, fee, margin):
        if not number:
            return
        including_fee_and_margin = core.bcm.calculations.apply_fee_and_margin(number, fee, margin)
        return numbers.round_decimal_floor(including_fee_and_margin)

    def _transform_fractional_value(self, number, fee, margin):
        if not number:
            return
        including_fee_and_margin = core.bcm.calculations.apply_fee_and_margin(number, fee, margin)
        return numbers.round_decimal_half_down(including_fee_and_margin, places=4)
