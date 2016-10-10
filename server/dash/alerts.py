# -*- coding: utf-8 -*-
from automation import campaign_stop

from dash import constants


def _construct_campaign_items(request, campaigns):
        campaign_items = []
        for campaign in sorted(campaigns, key=lambda x: x.name):
            campaign_link = request.build_absolute_uri('/campaigns/{}/ad_groups'.format(campaign.id))
            budget_link = request.build_absolute_uri('/campaigns/{}/budget'.format(campaign.id))
            campaign_items.append(u'<a href="{}">{}</a> - <a href="{}">Add budget</a>'.format(
                campaign_link, campaign.name, budget_link))
        return campaign_items


def get_account_landing_mode_alerts(request, account):
    if not request.user.has_perm('zemauth.can_see_landing_mode_alerts'):
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
        message = u'<strong>Campaigns will soon run out of budget.</strong><br /><br />'\
                  u'Please add budget or lower daily caps to continue to adjust media sources settings by your needs, '\
                  u'if you don’t want campaign to end in a few days. If you don’t take any actions, system will '\
                  u'automatically turn on the landing mode to hit your budget. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more ...</a><br /><br />'\
                  u'<ul>{campaigns}</ul>'

        depleting_budget_campaign_items = _construct_campaign_items(request, depleting_budget_campaigns)
        alerts.append({
            'type': constants.AlertType.DANGER,
            'message': message.format(
                campaigns=u''.join(u'<li>{}</li>'.format(item) for item in depleting_budget_campaign_items)),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if landing_campaigns:
        message = u'<strong>Campaigns are currently running in landing mode.</strong><br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more ...</a><br /><br />'\
                  u'<ul>{campaigns}</ul>'

        landing_campaign_items = _construct_campaign_items(request, landing_campaigns)
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                campaigns=u''.join(u'<li>{}</li>'.format(item) for item in landing_campaign_items)),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts


def get_campaign_landing_mode_alerts(request, campaign):
    if not request.user.has_perm('zemauth.can_see_landing_mode_alerts'):
        return []

    campaign_settings = campaign.get_current_settings()

    alerts = []
    if campaign_stop.is_campaign_running_out_of_budget(campaign, campaign_settings):
        message = u'<strong>This campaign will run out of budget soon.</strong><br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. If you don’t take any actions, system will '\
                  u'automatically turn on the landing mode to hit your budget. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more ...</a>'
        alerts.append({
            'type': constants.AlertType.DANGER,
            'message': message.format(
                campaign_name=campaign.name,
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if campaign_settings.landing_mode:
        message = u'<strong>This campaign is currently running in landing mode.</strong><br /><br />'\
                  u'Please add budget to continue to adjust media sources settings by your needs, if you '\
                  u'don’t want campaign to end in a few days. <a '\
                  u'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  u'target="_blank">Learn more ...</a>'
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                campaign_name=campaign.name,
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts
