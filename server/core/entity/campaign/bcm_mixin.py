from django.db import transaction


class CampaignBCMMixin(object):

    def get_bcm_modifiers(self):
        modifiers = None
        if self.account.uses_bcm_v2:
            fee, margin = self.get_todays_fee_and_margin()
            modifiers = {
                'fee': fee,
                'margin': margin,
            }
        return modifiers

    def get_todays_fee_and_margin(self):
        budget = self.budgets.select_related('credit').filter_today().first()
        if not budget:
            return None, None
        return budget.credit.license_fee, budget.margin

    @transaction.atomic
    def migrate_to_bcm_v2(self, request):
        fee, margin = self.get_todays_fee_and_margin()
        self._migrate_ad_groups(request, fee, margin)
        self._migrate_campaign_goals(request, fee, margin)

    def _migrate_ad_groups(self, request, fee, margin):
        for ad_group in self.adgroup_set.all():
            ad_group.migrate_to_bcm_v2(request, fee, margin)

    def _migrate_campaign_goals(self, request, fee, margin):
        for campaign_goal in self.campaigngoal_set.all():
            campaign_goal.migrate_to_bcm_v2(request, fee, margin)
