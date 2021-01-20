import datetime
import decimal

import pytz
from django.conf import settings
from django.db.models import Q

import automation.models
import dash.constants
import utils.dates_helper
import utils.email_helper
import utils.k1_helper
import utils.url_helper
from utils import metrics_compat
from utils import zlogging

logger = zlogging.getLogger(__name__)

DEPLETING_AVAILABLE_BUDGET_SCALAR = decimal.Decimal(1.5)
DEPLETING_CAMPAIGN_BUDGET_EMAIL = "help@zemanta.com"


@metrics_compat.timer("automation.campaignstop.simple.budget_campaigns", operation="notify_depleting")
def notify_depleting_budget_campaigns():
    campaigns = _get_active_campaigns()
    available_budgets = _get_available_budgets(campaigns)
    yesterdays_spends = _get_yesterdays_spends(campaigns)

    for camp in campaigns:
        budgets = available_budgets.get(camp.id)
        spends = yesterdays_spends.get(camp.id)
        if (
            not camp.real_time_campaign_stop
            and _budget_is_depleting(budgets, spends)
            and not _manager_has_been_notified(camp)
        ):
            _notify_campaign_with_depleting_budget(camp, available_budgets.get(camp.id), yesterdays_spends.get(camp.id))


def _budget_is_depleting(available_budget, yesterdays_spend):
    return (available_budget < yesterdays_spend * DEPLETING_AVAILABLE_BUDGET_SCALAR) and (yesterdays_spend > 0)


def _notify_campaign_with_depleting_budget(campaign, available_budget, yesterdays_spend):
    campaign_manager = campaign.get_current_settings().campaign_manager
    sales_rep = campaign.get_sales_representative()
    emails = utils.email_helper.email_manager_list(campaign)
    if sales_rep is not None:
        emails.append(sales_rep.email)

    total_daily_budget = _get_total_daily_budget_amount(campaign)
    campaign_url = utils.url_helper.get_full_z1_url(
        "/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings".format(campaign.pk)
    )

    _send_depleting_budget_notification_email(
        campaign, campaign_url, emails, available_budget, yesterdays_spend, total_daily_budget
    )
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=campaign_manager,
    ).save()


def _manager_has_been_notified(campaign):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = today - datetime.timedelta(days=1, hours=-1)
    campaign_manager = campaign.get_current_settings().campaign_manager
    return (
        automation.models.CampaignBudgetDepletionNotification.objects.filter(
            Q(campaign=campaign), Q(account_manager=campaign_manager), Q(created_dt__gte=yesterday)
        ).count()
        > 0
    )


@metrics_compat.timer("automation.campaignstop.simple.budget_campaigns", operation="stop_and_notify_depleted")
def stop_and_notify_depleted_budget_campaigns():
    campaigns = _get_active_campaigns()
    available_budgets = _get_available_budgets(campaigns)
    yesterdays_spends = _get_yesterdays_spends(campaigns)

    for camp in campaigns:
        if available_budgets.get(camp.id) <= 0:
            _stop_campaign(camp)
            _notify_depleted_budget_campaign_stopped(
                camp, available_budgets.get(camp.id), yesterdays_spends.get(camp.id)
            )


def _notify_depleted_budget_campaign_stopped(campaign, available_budget, yesterdays_spend):
    if campaign.real_time_campaign_stop:
        return

    campaign_manager = campaign.get_current_settings().campaign_manager
    sales_rep = campaign.get_sales_representative()

    emails = utils.email_helper.email_manager_list(campaign)
    if sales_rep is not None:
        emails.append(sales_rep.email)

    campaign_url = utils.url_helper.get_full_z1_url(
        "/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings".format(campaign.pk)
    )
    _send_campaign_stopped_notification_email(campaign, campaign_url, emails)
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=campaign_manager,
        stopped=True,
    ).save()


def _send_depleting_budget_notification_email(
    campaign, campaign_url, emails, available_budget, yesterdays_spend, total_daily_budget
):
    args = {
        "campaign": campaign,
        "account": campaign.account,
        "link_url": campaign_url,
        "available_budget": _round_budget(available_budget),
        "cap": _round_budget(total_daily_budget),
        "yesterday_spend": _round_budget(yesterdays_spend),
    }

    try:
        utils.email_helper.send_official_email(
            agency_or_user=campaign.account.agency,
            recipient_list=emails,
            from_email=DEPLETING_CAMPAIGN_BUDGET_EMAIL,
            **utils.email_helper.params_from_template(dash.constants.EmailTemplateType.BUDGET_DEPLETING, **args),
        )
    except Exception:
        logger.exception(
            "Budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:",
            campaign.name,
            ", ".join(emails),
        )


def _round_budget(budget):
    return decimal.Decimal(budget).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def _send_campaign_stopped_notification_email(campaign, campaign_url, emails):
    args = {"campaign": campaign, "account": campaign.account, "link_url": campaign_url}
    try:
        utils.email_helper.send_official_email(
            agency_or_user=campaign.account.agency,
            recipient_list=emails,
            from_email=DEPLETING_CAMPAIGN_BUDGET_EMAIL,
            **utils.email_helper.params_from_template(dash.constants.EmailTemplateType.CAMPAIGN_STOPPED, **args),
        )
    except Exception:
        logger.exception(
            "Campaign stop because of budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:",
            campaign.name,
            ", ".join(emails),
        )


def _get_yesterdays_spends(campaigns):
    yesterday = utils.dates_helper.local_today() - datetime.timedelta(1)
    spends = {campaign.id: _get_total_campaign_spend(campaign, yesterday) for campaign in campaigns}

    return spends


def _get_available_budgets(campaigns):
    available_budgets = {campaign.id: decimal.Decimal(_get_total_available_budget(campaign)) for campaign in campaigns}

    return available_budgets


def _get_total_available_budget(campaign, date=None):
    date = date or utils.dates_helper.local_today()
    return sum(
        budget.get_available_etfm_amount(date)
        for budget in campaign.budgets.all()
        if budget.state() == dash.constants.BudgetLineItemState.ACTIVE
    )


def _get_total_campaign_spend(campaign, date=None):
    date = date or utils.dates_helper.local_today()
    return sum(
        decimal.Decimal(budget.get_daily_spend(date)["etfm_total"])
        for budget in campaign.budgets.all()
        if budget.state() == dash.constants.BudgetLineItemState.ACTIVE
    )


def _get_total_daily_budget_amount(campaign):
    total_daily_budget = decimal.Decimal(0.0)
    for adg in _get_active_ad_groups(campaign):
        adg_daily_budget = adg.settings.daily_budget or 0
        total_daily_budget += adg_daily_budget
    return total_daily_budget


def _get_active_campaigns():
    return _get_active_campaigns_subset(
        dash.models.Campaign.objects.exclude(account_id=settings.HARDCODED_ACCOUNT_ID_OEN).exclude(
            account__agency_id__in=[663, 635, 629]
        )
    )


def _get_active_ad_groups(campaign):
    return list(_filter_active_ad_groups(campaign.adgroup_set.all()))


def _get_active_campaigns_subset(campaigns):
    ad_groups = _filter_active_ad_groups(dash.models.AdGroup.objects.filter(campaign__in=campaigns)).select_related(
        "campaign"
    )
    return list(set(ad_group.campaign for ad_group in ad_groups))


def _filter_active_ad_groups(ad_groups_qs):
    return ad_groups_qs.filter_current_and_active().filter_allowed_to_run().distinct()


def _stop_campaign(campaign):
    if campaign.account_id == settings.HARDCODED_ACCOUNT_ID_OEN:
        return
    if campaign.real_time_campaign_stop:
        _stop_real_time(campaign)
    else:
        _stop_all_ad_groups(campaign)


def _stop_real_time(campaign):
    campaign_state, _ = automation.campaignstop.CampaignStopState.objects.get_or_create(campaign=campaign)
    campaign_state.set_allowed_to_run(False)
    # automation.campaignstop.RealTimeCampaignStopLog.objects.create(
    #     campaign=campaign,
    #     event=automation.campaignstop.constants.CampaignStopEvent.SIMPLE_CAMPAIGN_STOP,
    #     context={},
    # )


def _stop_all_ad_groups(campaign):
    for ad_group in _get_active_ad_groups(campaign):
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
        new_settings.save(None)
        utils.k1_helper.update_ad_group(ad_group, msg="automation.stop_campaign", priority=True)
