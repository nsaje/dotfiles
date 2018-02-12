# -*- coding: utf-8 -*-
from automation import campaign_stop

from dash import constants


def _get_campaign_budget_link(request, campaign):
    query_string = 'settings&settingsScrollTo=zemCampaignBudgetsSettings'
    link = '/v2/analytics/campaign/{}?{}'.format(campaign.id, query_string)
    return request.build_absolute_uri(link)


def _get_campaign_ad_groups_link(request, campaign):
    link = '/v2/analytics/campaign/{}'.format(campaign.id)
    return request.build_absolute_uri(link)


def _construct_depleting_items(request, campaigns):
    campaign_items = []
    for campaign in sorted(campaigns, key=lambda x: x.name):
        campaign_items.append(
            '{} - <a href="{}">Add budget</a> or <a href="{}">Lower daily caps</a>'.format(
                campaign.name,
                _get_campaign_budget_link(request, campaign),
                _get_campaign_ad_groups_link(request, campaign),
            )
        )
    return campaign_items


def _construct_landing_items(request, campaigns):
    campaign_items = []
    for campaign in sorted(campaigns, key=lambda x: x.name):
        campaign_items.append(
            '{} - <a href="{}">Add budget</a>'.format(
                campaign.name,
                _get_campaign_budget_link(request, campaign),
            )
        )
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
        message = '<p><strong>Campaigns will soon run out of budget.</strong></p>'\
                  '<p>Please add budget or lower daily caps to continue to adjust media sources settings. If you '\
                  'don’t take any actions, the system will automatically turn on the landing mode to hit your '\
                  'budget. <a href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  'target="_blank">Learn more ...</a></p>'\
                  '<ul class="list-with-bullets">{campaigns}</ul>'

        depleting_budget_campaign_items = _construct_depleting_items(request, depleting_budget_campaigns)
        alerts.append({
            'type': constants.AlertType.WARNING,
            'message': message.format(
                campaigns=''.join('<li>{}</li>'.format(item) for item in depleting_budget_campaign_items)),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if landing_campaigns:
        message = '<p><strong>Campaigns are currently running in landing mode.</strong></p>'\
                  '<p>Please add budget to continue to adjust media sources settings. If you don’t take any actions, '\
                  'your campaigns will end in a few days. <a '\
                  'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  'target="_blank">Learn more ...</a></p>'\
                  '<ul class="list-with-bullets">{campaigns}</ul>'

        landing_campaign_items = _construct_landing_items(request, landing_campaigns)
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                campaigns=''.join('<li>{}</li>'.format(item) for item in landing_campaign_items)),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts


def get_campaign_landing_mode_alerts(request, campaign):
    if not request.user.has_perm('zemauth.can_see_landing_mode_alerts'):
        return []

    campaign_settings = campaign.get_current_settings()

    alerts = []
    if campaign_stop.is_campaign_running_out_of_budget(campaign, campaign_settings):
        message = '<p><strong>This campaign will run out of budget soon.</strong></p>'\
                  '<p>Please <a href="{budget_link}">add budget</a> or <a href="{sources_link}">lower daily caps</a> '\
                  'to continue to adjust media sources settings. If you don’t take any actions, the system '\
                  'will automatically turn on the landing mode to hit your budget. <a '\
                  'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  'target="_blank">Learn more ...</a></p>'
        alerts.append({
            'type': constants.AlertType.WARNING,
            'message': message.format(
                budget_link=_get_campaign_budget_link(request, campaign),
                sources_link=_get_campaign_ad_groups_link(request, campaign),
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    if campaign_settings.landing_mode:
        message = '<p><strong>This campaign is currently running in landing mode.</strong></p>'\
                  '<p>Please <a href="{budget_link}">add budget</a> to continue to adjust media sources settings. '\
                  'If you don’t take any actions, your campaign will end in a few days. <a '\
                  'href="http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode" '\
                  'target="_blank">Learn more ...</a></p>'
        alerts.append({
            'type': constants.AlertType.INFO,
            'message': message.format(
                budget_link=_get_campaign_budget_link(request, campaign),
            ),
            'permission': 'zemauth.can_see_landing_mode_alerts',
        })

    return alerts
