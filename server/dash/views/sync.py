import threading
import logging

import actionlog.sync

from dash.views import helpers
from dash import models
from utils import api_common
from utils import statsd_helper


logger = logging.getLogger(__name__)


class TriggerAccountSyncThread(threading.Thread):
    """ Used to trigger sync for all accounts asynchronously. """
    def __init__(self, accounts, *args, **kwargs):
        self.accounts = accounts
        super(TriggerAccountSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for account in self.accounts:
                actionlog.sync.AccountSync(account).trigger_all()
        except Exception:
            logger.exception('Exception in TriggerAccountSyncThread')


class TriggerCampaignSyncThread(threading.Thread):
    """ Used to trigger sync for ad_group's ad groups asynchronously. """
    def __init__(self, campaigns, *args, **kwargs):
        self.campaigns = campaigns
        super(TriggerCampaignSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for campaign in self.campaigns:
                actionlog.sync.CampaignSync(campaign).trigger_all()
        except Exception:
            logger.exception('Exception in TriggerCampaignSyncThread')


class TriggerAdGroupSyncThread(threading.Thread):
    """ Used to trigger sync for all campaign's ad groups asynchronously. """
    def __init__(self, ad_group, *args, **kwargs):
        self.ad_group = ad_group
        super(TriggerAdGroupSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            actionlog.sync.AdGroupSync(self.ad_group).trigger_all()
        except Exception:
            logger.exception('Exception in TriggerAdGroupSyncThread')


class AccountSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_sync_get')
    def get(self, request):
        accounts = models.Account.objects.all().filter_by_user(request.user)
        if not actionlog.api.is_sync_in_progress(accounts=accounts):
            # trigger account sync asynchronously and immediately return
            TriggerAccountSyncThread(accounts).start()

        return self.create_api_response({})


class AccountSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_is_sync_in_progress')
    def get(self, request):
        accounts = models.Account.objects.all().filter_by_user(request.user)

        in_progress = actionlog.api.is_sync_in_progress(accounts=accounts)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class CampaignSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_sync_get')
    def get(self, request):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')

        if account_id:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        if not actionlog.api.is_sync_in_progress(campaigns=campaigns):
            # trigger account sync asynchronously and immediately return
            TriggerCampaignSyncThread(campaigns).start()

        return self.create_api_response({})


class CampaignSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_is_sync_in_progress')
    def get(self, request):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')

        if account_id:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.all().filter_by_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        in_progress = actionlog.api.is_sync_in_progress(campaigns=campaigns)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class AdGroupSync(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_sync')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        if not actionlog.api.is_sync_in_progress(ad_groups=[ad_group]):
            # trigger ad group sync asynchronously and immediately return
            TriggerAdGroupSyncThread(ad_group).start()

        return self.create_api_response({})


class AdGroupCheckSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_is_sync_in_progress')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        in_progress = actionlog.api.is_sync_in_progress(ad_groups=[ad_group])

        return self.create_api_response({'is_sync_in_progress': in_progress})
