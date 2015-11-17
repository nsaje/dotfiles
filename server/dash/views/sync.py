import logging
from threading import Thread

import actionlog.sync

from dash.views import helpers
from dash import models
from utils import api_common
from utils import statsd_helper


logger = logging.getLogger(__name__)


class TriggerAccountSyncThread(Thread):
    """ Used to trigger sync for all accounts asynchronously. """
    def __init__(self, accounts, sources, request, *args, **kwargs):
        self.accounts = accounts
        self.sources = sources
        self.request = request
        super(TriggerAccountSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for account in self.accounts:
                actionlog.sync.AccountSync(account, sources=self.sources).trigger_all(self.request)
        except Exception:
            logger.exception('Exception in TriggerAccountSyncThread')


class TriggerCampaignSyncThread(Thread):
    """ Used to trigger sync for ad_group's ad groups asynchronously. """
    def __init__(self, campaigns, sources, request, *args, **kwargs):
        self.campaigns = campaigns
        self.sources = sources
        self.request = request
        super(TriggerCampaignSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for campaign in self.campaigns:
                actionlog.sync.CampaignSync(campaign, sources=self.sources).trigger_all(self.request)
        except Exception:
            logger.exception('Exception in TriggerCampaignSyncThread')


class TriggerAdGroupSyncThread(Thread):
    """ Used to trigger sync for all campaign's ad groups asynchronously. """
    def __init__(self, ad_group, sources, request, *args, **kwargs):
        self.ad_group = ad_group
        self.sources = sources
        self.request = request
        super(TriggerAdGroupSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            actionlog.sync.AdGroupSync(self.ad_group, sources=self.sources).trigger_all(self.request)
        except Exception:
            logger.exception('Exception in TriggerAdGroupSyncThread')


class AccountSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_sync_get')
    def get(self, request):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        accounts = models.Account.objects.all().filter_by_user(request.user)
        if not actionlog.api.is_sync_in_progress(accounts=accounts, sources=filtered_sources):
            # trigger account sync asynchronously and immediately return
            TriggerAccountSyncThread(accounts, filtered_sources, request).start()

        return self.create_api_response({})


class AccountSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_is_sync_in_progress')
    def get(self, request):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        accounts = models.Account.objects.all().filter_by_user(request.user)

        in_progress = actionlog.api.is_sync_in_progress(accounts=accounts, sources=filtered_sources)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class CampaignSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_sync_get')
    def get(self, request):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        if account_id:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        if not actionlog.api.is_sync_in_progress(campaigns=campaigns, sources=filtered_sources):
            # trigger account sync asynchronously and immediately return
            TriggerCampaignSyncThread(campaigns, filtered_sources, request).start()

        return self.create_api_response({})


class CampaignSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_is_sync_in_progress')
    def get(self, request):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        if account_id:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        in_progress = actionlog.api.is_sync_in_progress(campaigns=campaigns, sources=filtered_sources)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class AdGroupSync(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_sync')
    def get(self, request, ad_group_id):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        if not actionlog.api.is_sync_in_progress(ad_groups=[ad_group], sources=filtered_sources):
            # trigger ad group sync asynchronously and immediately return
            TriggerAdGroupSyncThread(ad_group, filtered_sources, request).start()

        return self.create_api_response({})


class AdGroupCheckSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_is_sync_in_progress')
    def get(self, request, ad_group_id):
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        in_progress = actionlog.api.is_sync_in_progress(ad_groups=[ad_group], sources=filtered_sources)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class AdGroupPublisherBlacklistCheckSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_is_sync_in_progress')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        in_progress = actionlog.api.is_publisher_blacklist_sync_in_progress(ad_group)

        return self.create_api_response({'is_sync_in_progress': in_progress})
