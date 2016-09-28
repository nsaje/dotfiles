# -*- coding: utf-8 -*-
from automation import campaign_stop

from dash import constants


def get_account_landing_mode_alerts(user, account):
    if not user.has_perm('zemauth.can_see_landing_mode_alerts'):
        return []

    landing_campaigns, depleting_budget_campaigns = [], []
    for campaign in account.campaign_set.all().exclude_archived():
        campaign_settings = campaign.get_current_settings()
        if campaign_settings.landing_mode:
            landing_campaigns.append(campaign)

        if campaign_stop.is_campaign_running_out_of_budget(campaign, campaign_settings):
            depleting_budget_campaigns.append(campaign)

    alerts = []
    if depleting_budget_campaigns:
        message = u'The following campaigns will soon run out of budget: {campaigns}.<br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. If you don’t take any actions, system will '\
                  u'automatically turn on the landing mode to hit your budget. While a campaign is in landing mode, '\
                  u'CPCs and daily budgets of media sources will not be available for any changes. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more about landing mode ...</a>'
        alerts.append({
            'type': constants.AlertType.DANGER,
            'message': message.format(
                campaigns=', '.join(c.name for c in sorted(depleting_budget_campaigns, key=lambda x: x.name))),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if landing_campaigns:
        message = u'The following campaigns are currently running in landing mode: {campaigns}.<br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. While a campaign is in landing mode, '\
                  u'CPCs and daily budgets of media sources will not be available for any changes. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more about landing mode ...</a>'
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                campaigns=', '.join(c.name for c in sorted(landing_campaigns, key=lambda x: x.name))),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts


def get_campaign_landing_mode_alerts(user, campaign):
    if not user.has_perm('zemauth.can_see_landing_mode_alerts'):
        return []

    campaign_settings = campaign.get_current_settings()

    alerts = []
    if campaign_stop.is_campaign_running_out_of_budget(campaign, campaign_settings):
        message = u'This campaign will run out of budget soon.<br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. If you don’t take any actions, system will '\
                  u'automatically turn on the landing mode to hit your budget. While a campaign is in landing mode, '\
                  u'CPCs and daily budgets of media sources will not be available for any changes. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more about landing mode ...</a>'
        alerts.append({
            'type': constants.AlertType.DANGER,
            'message': message.format(
                campaign_name=campaign.name,
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if campaign_settings.landing_mode:
        message = u'This campaign is currently running in landing mode.<br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. While a campaign is in landing mode, '\
                  u'CPCs and daily budgets of media sources will not be available for any changes. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more about landing mode ...</a>'
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                campaign_name=campaign.name,
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts
