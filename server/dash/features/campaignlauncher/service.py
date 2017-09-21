import rest_framework

from dash import models
import dash.constants
from dash.features import contentupload
import utils.dates_helper
import utils.exc


AD_GROUP_NAME_TEMPLATE = '{campaign_name} - Ad Group #1'


def _extract_error_list(e):
    """ FIXME(nsaje) Hack until we unify validation errors from different services """
    error_list = []
    error_dict = getattr(e, 'message_dict', None) or getattr(e, 'errors', None)
    error_message = getattr(e, 'message', None)
    if error_dict:
        for error in error_dict.values():
            if isinstance(error, basestring):
                error_list.append(error)
            else:
                error_list.extend(error)
    elif error_message:
        if isinstance(error_message, basestring):
            error_list.append(error_message)
        else:
            error_list.extend(error_message)

    return error_list


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
        raise rest_framework.serializers.ValidationError({"budget_amount": ["No credit available!"]})

    start_date = utils.dates_helper.local_today()
    end_date = credit_to_use.end_date
    try:
        models.BudgetLineItem.objects.create(
            request=request,
            campaign=campaign,
            credit=credit_to_use,
            start_date=start_date,
            end_date=end_date,
            amount=budget_amount,
            comment='Created via campaign launcher.'
        )
    except Exception as e:
        raise rest_framework.serializers.ValidationError({"budget_amount": _extract_error_list(e)})

    conversion_goal = None
    if conversion_goal_type is not None:
        conversion_goal = models.ConversionGoal.objects.create(
            request, campaign, conversion_goal_type, conversion_goal_goal_id, conversion_goal_window)
    models.CampaignGoal.objects.create(request, campaign, goal_type, goal_value, conversion_goal, primary=True)

    try:
        ad_group_name = AD_GROUP_NAME_TEMPLATE.format(campaign_name=name)
        ad_group = models.AdGroup.objects.create(request, campaign)
        ad_group.settings.update(
            request,
            name=ad_group_name,
            start_date=start_date,
            cpc_cc=max_cpc,
            daily_budget_cc=daily_budget,
            autopilot_daily_budget=daily_budget,
            target_regions=target_regions,
            exclusion_target_regions=exclusion_target_regions,
            target_devices=target_devices,
            target_os=target_os,
            target_placements=target_placements,
        )
        # Change state separately because of a chicken-and-egg problem during settings validation.
        # Budget is validated against media sources' daily caps before the budget autopilot is run
        # to distribute and set daily caps appropriately.
        ad_group.settings.update(
            request,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )
    except utils.exc.ValidationError as e:
        raise rest_framework.serializers.ValidationError(', '.join(_extract_error_list(e)))

    upload_batch.set_ad_group(ad_group)
    contentupload.upload.persist_batch(upload_batch)

    return campaign
