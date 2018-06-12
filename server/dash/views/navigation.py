# -*- coding: utf-8 -*-
import logging

import influx

import automation.campaignstop
from dash import models
from dash.views import helpers
from dash.views import navigation_helpers
from utils import api_common

logger = logging.getLogger(__name__)


class UsesBCMV2View(api_common.BaseApiView):
    def get(self, request):
        """
        Returns true if user has all accounts to which he has access to migrated to the new
        margins system.
        """

        user = request.user

        return self.create_api_response({
            'usesBCMv2': helpers.all_accounts_uses_bcm_v2(user)
        })


class NavigationDataView(api_common.BaseApiView):

    def get(self, request, level_, id_):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        account, campaign, ad_group = None, None, None
        response = {}

        if level_ == 'accounts':
            account = helpers.get_account(request.user, id_, sources=filtered_sources)

        if level_ == 'campaigns':
            campaign = helpers.get_campaign(request.user, id_, sources=filtered_sources)
            account = campaign.account

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(request.user, id_, sources=filtered_sources)
            campaign = ad_group.campaign
            account = campaign.account

        if account:
            account_dict = account.__dict__
            account_dict['agency__name'] = account.agency.name if account.agency else None
            response['account'] = navigation_helpers.get_account_dict(
                account_dict, account.get_current_settings())

        if campaign:
            response['campaign'] = navigation_helpers.get_campaign_dict(
                campaign.__dict__, campaign.get_current_settings())

        if ad_group:
            response['ad_group'] = navigation_helpers.get_ad_group_dict(
                request.user,
                ad_group.__dict__,
                ad_group.get_current_settings(),
                ad_group.campaign.get_current_settings(),
                automation.campaignstop.get_campaignstop_state(ad_group.campaign),
                real_time_campaign_stop=ad_group.campaign.real_time_campaign_stop,
            )

        return self.create_api_response(response)


class NavigationAllAccountsDataView(api_common.BaseApiView):

    def get(self, request):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        accounts = models.Account.objects.all().filter_by_user(request.user)\
                                               .filter_by_sources(filtered_sources)
        accounts_count = accounts.count()
        response = {
            'accounts_count': accounts_count
        }

        if accounts_count > 0:
            # find the first one that is not archived
            for account in accounts.iterator():
                if not account.is_archived():
                    response['default_account_id'] = account.id
                    break
            # if nothing found use an arhived one
            if 'default_account_id' not in response:
                response['default_account_id'] = accounts[0].id

        return self.create_api_response(response)


class NavigationTreeView(api_common.BaseApiView):

    def get(self, request):
        with influx.block_timer(
                'navigation',
                load_statuses=str(request.GET.get('loadStatuses') != 'false'),
                all_accounts=str(request.user.has_perm('zemauth.can_see_all_accounts'))):
            return self._get(request)

    def _get(self, request):
        view_filter = helpers.ViewFilter(request=request)
        user = request.user
        load_settings = request.GET.get('loadStatuses') != 'false'

        accounts = self._fetch_account_data_from_db(user, view_filter)
        campaigns, map_campaign_settings, map_campaignstop_states = self._fetch_campaign_data_from_db(
            user, view_filter, accounts, load_settings)
        ad_groups_data = self._load_ad_groups_data(
            user, view_filter, map_campaign_settings, map_campaignstop_states, campaigns, load_settings)
        campaigns_data = self._load_campaigns_data(
            ad_groups_data, campaigns, map_campaign_settings, load_settings)
        accounts_data = self._load_accounts_data(
            campaigns_data, accounts, load_settings)
        return self.create_api_response(accounts_data)

    def _load_ad_groups_data(
            self, user, view_filter, map_campaign_settings,
            map_campaignstop_states, campaigns, load_settings=True):
        # load necessary objects
        ad_groups = models.AdGroup.objects.all()\
            .filter_by_sources(view_filter.filtered_sources)\
            .filter(campaign__in=campaigns)\
            .order_by('name')

        map_ad_groups_settings = {}
        if load_settings:
            ad_groups_settings = models.AdGroupSettings.objects.filter(
                ad_group__in=ad_groups).group_current_settings().only(
                    'id', 'ad_group_id', 'state', 'autopilot_state', 'archived', 'start_date', 'end_date')
            map_ad_groups_settings = {ags.ad_group_id: ags for ags in ad_groups_settings}

        data_ad_groups = {}
        for ad_group in ad_groups.values('id', 'campaign_id', 'name', 'campaign__real_time_campaign_stop'):
            ad_group_settings = map_ad_groups_settings.get(ad_group['id'])

            ad_group_dict = navigation_helpers.get_ad_group_dict(
                user,
                ad_group,
                ad_group_settings,
                map_campaign_settings.get(ad_group['campaign_id']),
                map_campaignstop_states.get(ad_group['campaign_id']),
                real_time_campaign_stop=ad_group['campaign__real_time_campaign_stop'],
                with_settings=load_settings,
            )

            data_ad_groups.setdefault(ad_group['campaign_id'], []).append(ad_group_dict)

        return data_ad_groups

    def _fetch_campaign_data_from_db(self, user, view_filter, accounts, load_settings=True):
        campaigns = models.Campaign.objects.all()\
            .filter_by_sources(view_filter.filtered_sources)\
            .filter(account__in=accounts)\
            .order_by('name')

        map_campaigns_settings = {}
        map_campaignstop_states = {}
        if load_settings:
            campaigns_settings = models.CampaignSettings.objects.filter(
                campaign__in=campaigns).group_current_settings()
            map_campaigns_settings = {cs.campaign_id: cs for cs in campaigns_settings}

            map_campaignstop_states = automation.campaignstop.get_campaignstop_states(campaigns)

        return campaigns, map_campaigns_settings, map_campaignstop_states

    def _load_campaigns_data(self, ad_groups_data,
                             campaigns, map_campaign_settings, load_settings=True):
        data_campaigns = {}
        for campaign in campaigns.values('id', 'name', 'account_id'):
            campaign_dict = navigation_helpers.get_campaign_dict(
                campaign,
                map_campaign_settings.get(campaign['id']),
                with_settings=load_settings,
            )

            # use camel-case to optimize for JS naming conventions
            campaign_dict['adGroups'] = ad_groups_data.get(campaign['id'], [])

            data_campaigns.setdefault(campaign['account_id'], []).append(campaign_dict)

        return data_campaigns

    def _fetch_account_data_from_db(self, user, view_filter):
        accounts = models.Account.objects.all()\
            .filter_by_user(user)\
            .filter_by_sources(view_filter.filtered_sources)\
            .filter_by_agencies(view_filter.filtered_agencies)\
            .filter_by_account_types(view_filter.filtered_account_types)\

        return accounts

    def _load_accounts_data(self, campaings_data, accounts, load_settings=True):
        map_accounts_settings = {}
        if load_settings:
            accounts_settings = models.AccountSettings.objects.filter(
                account__in=accounts).group_current_settings()
            map_accounts_settings = {acs.account_id: acs for acs in accounts_settings}

        data_accounts = []
        for account in accounts.values('id', 'name', 'uses_bcm_v2', 'agency__name', 'currency'):
            account_dict = navigation_helpers.get_account_dict(
                account,
                map_accounts_settings.get(account['id']),
                with_settings=load_settings,
            )
            account_dict['campaigns'] = campaings_data.get(account['id'], [])

            data_accounts.append(account_dict)

        return data_accounts
