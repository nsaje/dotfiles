import rest_framework

from dash import models


def launch(request, account, name, iab_category, start_date, end_date, budget_amount,
           goal_type, goal_value, conversion_goal_type=None, conversion_goal_goal_id=None, conversion_goal_window=None):
    campaign = models.Campaign.objects.create(
        request=request,
        account=account,
        name=name,
        iab_category=iab_category,
    )

    credit_to_use = models.CreditLineItem.objects.get_any_for_budget_creation(account)
    if not credit_to_use:
        raise rest_framework.serializers.ValidationError("No credit available!")

    # TODO(nsaje): handle case where not enough credit for selected budget amount
    models.BudgetLineItem.objects.create(
        request=request,
        campaign=campaign,
        credit=credit_to_use,
        start_date=start_date,
        end_date=end_date,
        amount=budget_amount,
        comment='Created via campaign launcher.'
    )

    conversion_goal = None
    if conversion_goal_type is not None:
        conversion_goal = models.ConversionGoal.objects.create(
            request, campaign, conversion_goal_type, conversion_goal_goal_id, conversion_goal_window)
    models.CampaignGoal.objects.create(request, campaign, goal_type, goal_value, conversion_goal, primary=True)

    return campaign
