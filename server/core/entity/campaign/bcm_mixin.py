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
        return budget.margin, budget.credit.license_fee
