from django.db import transaction
from django.db.models import Q

import core.bcm
import dash.constants
from utils import k1_helper, numbers


class AdGroupBCMMixin(object):

    def get_bcm_modifiers(self):
        modifiers = None
        if self.campaign.account.uses_bcm_v2:
            fee, margin = self.get_todays_fee_and_margin()
            modifiers = {
                'fee': fee,
                'margin': margin,
            }
        return modifiers

    def get_todays_fee_and_margin(self):
        todays_budget = core.bcm.BudgetLineItem.objects \
            .filter(campaign_id=self.campaign_id) \
            .filter_today() \
            .select_related('credit') \
            .order_by('id') \
            .first()

        fee, margin = None, None
        if todays_budget:
            margin = todays_budget.margin
            fee = todays_budget.credit.license_fee
        else:
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
        ad_group_sources = self._get_ad_group_sources_to_migrate()
        for ad_group_source in ad_group_sources:
            ad_group_source.migrate_to_bcm_v2(request, fee, margin)

    def _get_ad_group_sources_to_migrate(self):
        ad_group_sources = self.adgroupsource_set.all()
        if self.settings.b1_sources_group_enabled:
            ad_group_sources = ad_group_sources.exclude(
                source__source_type__type=dash.constants.SourceType.B1)
        return ad_group_sources

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
            skip_validation=True,
            b1_sources_group_daily_budget=new_b1_sources_group_daily_budget,
            max_cpm=new_max_cpm,
            autopilot_daily_budget=new_autopilot_daily_budget,
            cpc_cc=new_cpc_cc,
        )

        # NOTE: this is done separately so that cpc_cc is already set,
        # otherwise ad group sources cpcs are changed before settings
        # are saved and can exceed max ad group cpc
        self.settings.update(
            request,
            skip_validation=True,
            b1_sources_group_cpc_cc=new_b1_sources_group_cpc_cc
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
        return numbers.round_decimal_ceiling(including_fee_and_margin, places=0)

    def _transform_fractional_value(self, number, fee, margin):
        if not number:
            return
        including_fee_and_margin = core.bcm.calculations.apply_fee_and_margin(number, fee, margin)
        return numbers.round_decimal_half_down(including_fee_and_margin, places=3)
