import rest_framework

from dash import models


def launch(user, account, name, iab_category, start_date, end_date, budget_amount):
    campaign = models.Campaign.objects.create(
        user=user,
        account=account,
        name=name,
        iab_category=iab_category,
    )

    credit_to_use = models.CreditLineItem.objects.get_any_for_budget_creation(account)
    if not credit_to_use:
        raise rest_framework.serializers.ValidationError("No credit available!")

    # TODO(nsaje): handle case where not enough credit for selected budget amount
    models.BudgetLineItem.objects.create(
        user=user,
        campaign=campaign,
        credit=credit_to_use,
        start_date=start_date,
        end_date=end_date,
        amount=budget_amount,
        comment='Created via campaign launcher.'
    )

    return campaign
