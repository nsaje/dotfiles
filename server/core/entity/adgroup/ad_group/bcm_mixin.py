import core.bcm


class AdGroupBCMMixin(object):
    def get_todays_fee_and_margin(self):
        todays_budget = core.bcm.BudgetLineItem.objects.filter(
            campaign_id=self.campaign_id).filter_today().first()
        margin = todays_budget.margin if todays_budget else None

        todays_credit = core.bcm.CreditLineItem.objects.filter(
            account_id=self.campaign.account_id).filter_active().first()
        fee = todays_credit.license_fee if todays_credit else None

        return fee, margin
