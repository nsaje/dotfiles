from django.db.models import Q

import core.features.bcm


class CampaignBCMMixin(object):
    def get_bcm_modifiers(self):
        fee, margin = self.get_todays_fee_and_margin()
        modifiers = {"fee": fee, "margin": margin}
        return modifiers

    def get_todays_fee_and_margin(self):
        budget = self._get_todays_budget()
        if budget:
            return budget.credit.license_fee, budget.margin
        else:
            credit = self._get_todays_credit()
            if credit:
                return credit.license_fee, None
        return None, None

    def _get_todays_budget(self):
        return self.budgets.select_related("credit").filter_today().first()

    def _get_todays_credit(self):
        credit = (
            core.features.bcm.CreditLineItem.objects.filter(
                Q(account_id=self.account_id) | Q(agency_id=self.account.agency_id)
            )
            .filter_active()
            .first()
        )
        return credit
