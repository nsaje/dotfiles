# -*- coding: utf-8 -*-
import logging

from utils import api_common
from utils import statsd_helper

from dash import models
from dash.views import helpers
from dash.views import navigation_helpers

logger = logging.getLogger(__name__)


class NavigationDataView(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.navigation', 'get_navigation_data')
    def get(self, request, level_, id_):
        include_archived_flag = request.user.has_perm('zemauth.view_archived_entities')
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
            response['account'] = navigation_helpers.get_account_dict(
                account, account.get_current_settings(), include_archived_flag)

        if campaign:
            response['campaign'] = navigation_helpers.get_campaign_dict(
                campaign, campaign.get_current_settings(), include_archived_flag)

        if ad_group:
            ad_group_source_settings = models.AdGroupSourceSettings.objects\
                                                                   .filter(ad_group_source__ad_group_id=ad_group.id)\
                                                                   .filter_by_sources(filtered_sources)\
                                                                   .group_current_settings()

            response['ad_group'] = navigation_helpers.get_ad_group_dict(
                ad_group, ad_group.get_current_settings(), ad_group_source_settings, include_archived_flag)

        return self.create_api_response(response)


class NavigationAllAccountsDataView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.navigation', 'get_all_accounts_navigation_data')
    def get(self, request):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        accounts = models.Account.objects.all().filter_by_user(request.user)\
                                               .filter_by_sources(filtered_sources)
        response = {
            'has_accounts': False
        }
        if accounts.exists():
            response['has_accounts'] = True

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
    @statsd_helper.statsd_timer('dash.navigation', 'get_all_accounts_navigation_tree')
    def get(self, request):
        include_archived_flag = request.user.has_perm('zemauth.view_archived_entities')
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        user = request.user

        ad_groups_data = self._load_ad_groups_data(user, filtered_sources, include_archived_flag)
        campaigns_data = self._load_campaigns_data(ad_groups_data, user, filtered_sources, include_archived_flag)
        accounts_data = self._load_accounts_data(campaigns_data, user, filtered_sources, include_archived_flag)

        return self.create_api_response(accounts_data)

    def _load_ad_groups_data(self, user, filtered_sources, include_archived_flag):
        # load necessary objects
        ad_groups = models.AdGroup.objects.all().filter_by_user(user).filter_by_sources(filtered_sources).only(
            'id', 'name', 'campaign_id', 'content_ads_tab_with_cms')

        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__in=ad_groups).filter_by_sources(
            filtered_sources).only('id', 'ad_group_id')

        map_ad_group_source = dict(ad_group_sources.values_list('id', 'ad_group_id'))

        ad_groups_settings = models.AdGroupSettings.objects.filter(ad_group__in=ad_groups)\
                                                           .group_current_settings()\
                                                           .only('ad_group_id', 'state', 'start_date', 'end_date')

        map_ad_groups_settings = {ags.ad_group_id: ags for ags in ad_groups_settings}

        # takes too long to do a join when constraints are applied
        ad_groups_sources_settings = models.AdGroupSourceSettings.objects.all().group_current_settings().only(
            'ad_group_source_id', 'state')

        map_ad_groups_sources_settings = {}
        for ad_group_source_settings in ad_groups_sources_settings:
            ad_group_source_id = ad_group_source_settings.ad_group_source_id

            # filter by ad group and source
            if ad_group_source_id in map_ad_group_source:
                ad_group_id = map_ad_group_source[ad_group_source_id]
                map_ad_groups_sources_settings.setdefault(ad_group_id, []).append(ad_group_source_settings)

        data_ad_groups = {}
        for ad_group in ad_groups:
            ad_group_settings = map_ad_groups_settings.get(ad_group.id)
            ad_group_source_settings = map_ad_groups_sources_settings.get(ad_group.id)

            ad_group_dict = navigation_helpers.get_ad_group_dict(
                ad_group, ad_group_settings, ad_group_source_settings, include_archived_flag)

            data_ad_groups.setdefault(ad_group.campaign_id, []).append(ad_group_dict)

        return data_ad_groups

    def _load_campaigns_data(self, ad_groups_data, user, filtered_sources, include_archived_flag):
        campaigns = models.Campaign.objects.all().filter_by_user(user).filter_by_sources(
            filtered_sources).only('id', 'name', 'account_id')

        map_campaigns_settings = {}
        if include_archived_flag:
            campaigns_settings = models.CampaignSettings.objects.filter(
                campaign__in=campaigns).group_current_settings().only('campaign_id', 'archived')

            map_campaigns_settings = {cs.campaign_id: cs for cs in campaigns_settings}

        data_campaigns = {}
        for campaign in campaigns:
            campaign_dict = navigation_helpers.get_campaign_dict(
                campaign, map_campaigns_settings.get(campaign.id), include_archived_flag)

            # use camel-case to optimize for JS naming conventions
            campaign_dict['adGroups'] = ad_groups_data.get(campaign.id, [])

            data_campaigns.setdefault(campaign.account_id, []).append(campaign_dict)

        return data_campaigns

    def _load_accounts_data(self, campaings_data, user, filtered_sources, include_archived_flag):
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(
            filtered_sources).only('id', 'name')

        map_accounts_settings = {}
        if include_archived_flag:
            accounts_settings = models.AccountSettings.objects.filter(account__in=accounts)\
                                                              .group_current_settings()\
                                                              .only('account_id', 'archived')
            map_accounts_settings = {acs.account_id: acs for acs in accounts_settings}

        data_accounts = []
        for account in accounts:
            account_dict = navigation_helpers.get_account_dict(
                account, map_accounts_settings.get(account.id), include_archived_flag)
            account_dict['campaigns'] = campaings_data.get(account.id, [])

            data_accounts.append(account_dict)

        return data_accounts
