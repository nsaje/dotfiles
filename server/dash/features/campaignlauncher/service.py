import rest_framework

from dash import models
from dash.features import contentupload
import utils.dates_helper


AD_GROUP_NAME_TEMPLATE = '{campaign_name} - Ad Group #1'


def launch(request, account, name, iab_category, budget_amount,
           goal_type, goal_value, max_cpc, daily_budget, upload_batch,
           target_regions=None, exclusion_target_regions=None, target_devices=None, target_os=None, target_placements=None,
           conversion_goal_type=None, conversion_goal_goal_id=None, conversion_goal_window=None):
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
    start_date = utils.dates_helper.local_today()
    end_date = credit_to_use.end_date
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

    ad_group_name = AD_GROUP_NAME_TEMPLATE.format(campaign_name=name)
    ad_group = models.AdGroup.objects.create(request, campaign)
    ad_group.settings.update(
        request,
        name=ad_group_name,
        start_date=start_date,
        cpc_cc=max_cpc,
        daily_budget_cc=daily_budget,
        target_regions=target_regions,
        exclusion_target_regions=exclusion_target_regions,
        target_devices=target_devices,
        target_os=target_os,
        target_placements=target_placements,
    )

    upload_batch.set_ad_group(ad_group)
    contentupload.upload.persist_batch(upload_batch)

    return campaign
