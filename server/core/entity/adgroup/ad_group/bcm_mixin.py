import core.bcm


class AdGroupBCMMixin(object):
    def get_todays_fee_and_margin(self):
        try:
            todays_budget = core.bcm.BudgetLineItem.objects.filter(
                campaign_id=self.campaign_id).filter_today().get()
            margin = todays_budget.margin
        except core.bcm.BudgetLineItem.DoesNotExist:
            margin = None

        try:
            todays_credit = core.bcm.CreditLineItem.objects.filter(
                account_id=self.campaign.account_id).filter_active().get()
            fee = todays_credit.license_fee
        except core.bcm.CreditLineItem.DoesNotExist:
            fee = None

        return fee, margin
