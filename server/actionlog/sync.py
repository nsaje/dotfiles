import dash.models
import newrelic.agent

from datetime import datetime, timedelta  # use import from in order to be able to mock it in tests

import actionlog.models
import actionlog.constants

from actionlog import api, api_contentads
from actionlog.exceptions import InsertActionException
from utils.command_helpers import last_n_days
from . import zwei_actions

from django.conf import settings
from django.db import transaction


class BaseSync(object):

    def __init__(self, obj, sources=None):
        self.obj = obj
        if sources is None:
            sources = dash.models.Source.objects.all()
        self.sources = sources

    def _construct_last_sync_result(self, sync_key, include_maintenance=False, include_deprecated=False):

        ad_group_sources = self.get_ad_group_sources(include_maintenance=include_maintenance,
                                                     include_deprecated=include_deprecated)
        vals = ad_group_sources.values_list(sync_key, 'last_successful_sync_dt')

        per_key = {}
        for key, last_successful_sync_dt in vals:
            if key not in per_key:
                per_key[key] = []

            per_key[key].append(last_successful_sync_dt)

        sync_data = {}
        for key, syncs_list in per_key.iteritems():
            if None in syncs_list:
                sync_data[key] = None
                continue

            sync_data[key] = min(syncs_list)

        return sync_data

    @newrelic.agent.function_trace()
    def get_latest_success_by_child(self):
        return self._construct_last_sync_result(self.get_child_sync_key())

    @newrelic.agent.function_trace()
    def get_latest_source_success(self):
        return self._construct_last_sync_result('source_id',
                                                include_maintenance=True,
                                                include_deprecated=True)

    def trigger_all(self, request=None):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_all(request)

    def trigger_reports(self, request=None):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_reports(request)

    def trigger_status(self, request=None):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_status(request)

    def trigger_content_ad_status(self, request=None):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_content_ad_status(request)


class ISyncComposite(object):

    def get_components(self):
        raise NotImplementedError

    def get_ad_group_sources(self):
        raise NotImplementedError


class GlobalSync(BaseSync, ISyncComposite):

    @newrelic.agent.function_trace()
    def __init__(self, sources=None):
        if sources is None:
            sources = dash.models.Source.objects.all()
        self.sources = sources

    @newrelic.agent.function_trace()
    def get_components(self, maintenance=False, archived=False, deprecated=False):
        accounts = dash.models.Account.objects.all()
        if not archived:
            accounts = accounts.exclude_archived()

        for account in accounts:
            account_sync = AccountSync(account)
            if len(list(account_sync.get_components(maintenance=maintenance, deprecated=deprecated))) > 0:
                yield account_sync

    def get_ad_group_sources(self, include_maintenance=False, include_deprecated=False):
        ad_group_sources = dash.models.AdGroupSource.objects.\
            filter(ad_group__in=dash.models.AdGroup.objects.all().exclude_archived()).\
            filter(source__in=self.sources).\
            select_related('ad_group__campaign', 'source')

        if not include_maintenance:
            ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

        if not include_deprecated:
            ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

        return ad_group_sources

    def get_child_sync_key(self):
        return 'ad_group__campaign__account_id'


class AccountSync(BaseSync, ISyncComposite):

    @newrelic.agent.function_trace()
    def get_components(self, maintenance=False, archived=False, deprecated=False):
        campaigns = dash.models.Campaign.objects.filter(account=self.obj)
        if not archived:
            campaigns = campaigns.exclude_archived()

        for campaign in campaigns:
            campaign_sync = CampaignSync(campaign, sources=self.sources)
            if len(list(campaign_sync.get_components(maintenance=maintenance, deprecated=deprecated))) > 0:
                yield campaign_sync

    @newrelic.agent.function_trace()
    def get_ad_group_sources(self, include_maintenance=False, include_deprecated=False):
        campaigns = dash.models.Campaign.objects.filter(account=self.obj).exclude_archived()
        ad_groups = dash.models.AdGroup.objects\
                                       .filter(campaign__in=campaigns)\
                                       .exclude_archived()
        ad_group_sources = dash.models.AdGroupSource.objects\
                                                    .filter(ad_group__in=ad_groups)\
                                                    .filter(source__in=self.sources)\
                                                    .select_related('ad_group', 'source')

        if not include_maintenance:
            ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

        if not include_deprecated:
            ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

        return ad_group_sources

    def get_child_sync_key(self):
        return 'ad_group__campaign_id'


class CampaignSync(BaseSync, ISyncComposite):

    @newrelic.agent.function_trace()
    def get_components(self, maintenance=False, archived=False, deprecated=False):
        ad_groups = dash.models.AdGroup.objects.filter(campaign=self.obj).prefetch_related('adgroupsource_set__source')
        if not archived:
            ad_groups = ad_groups.exclude_archived()

        for ad_group in ad_groups:
            ad_group_sync = AdGroupSync(ad_group, sources=self.sources)
            if len(list(ad_group_sync.get_components(maintenance=maintenance, deprecated=deprecated))) > 0:
                yield ad_group_sync

    @newrelic.agent.function_trace()
    def get_ad_group_sources(self, include_maintenance=False, include_deprecated=False):
        ad_groups = dash.models.AdGroup.objects.filter(campaign=self.obj).exclude_archived()
        ad_group_sources = dash.models.AdGroupSource.objects\
                                                    .filter(ad_group__in=ad_groups)\
                                                    .filter(source__in=self.sources)\
                                                    .select_related('ad_group', 'source')

        if not include_maintenance:
            ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

        if not include_deprecated:
            ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

        return ad_group_sources

    def get_child_sync_key(self):
        return 'ad_group_id'


class AdGroupSync(BaseSync, ISyncComposite):

    @newrelic.agent.function_trace()
    def __init__(self, obj, sources=None):
        super(AdGroupSync, self).__init__(obj, sources=sources)
        self.real_ad_group = self.obj

    @newrelic.agent.function_trace()
    def get_components(self, maintenance=False, archived=False, deprecated=False):
        source_ids = [s.id for s in self.sources]
        for ags in self.real_ad_group.adgroupsource_set.all():
            if ags.source.id not in source_ids:
                # source filtered
                continue

            if not maintenance and ags.source.maintenance:
                continue

            if not deprecated and ags.source.deprecated:
                continue

            yield AdGroupSourceSync(ags, sources=self.sources)

    @newrelic.agent.function_trace()
    def get_ad_group_sources(self, include_maintenance=False, include_deprecated=False):
        ad_group_sources = dash.models.AdGroupSource.objects\
                                                    .filter(ad_group=self.obj)\
                                                    .filter(source__in=self.sources)\
                                                    .select_related('ad_group', 'source')

        if not include_maintenance:
            ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

        if not include_deprecated:
            ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

        return ad_group_sources

    def get_child_sync_key(self):
        return 'id'


class AdGroupSourceSync(BaseSync):

    def get_latest_success_by_child(self):
        return {self.obj.id: self.obj.last_successful_sync_dt}

    def get_latest_source_success(self):
        return {self.obj.source_id: self.obj.last_successful_sync_dt}

    def trigger_all(self, request=None):
        self.trigger_status(request)
        self.trigger_reports(request)
        self.trigger_content_ad_status(request)

    def trigger_status(self, request=None):
        order = actionlog.models.ActionLogOrder.objects.create(
            order_type=actionlog.constants.ActionLogOrderType.FETCH_STATUS
        )
        try:
            action = api._init_fetch_status(self.obj, order, request=request)
        except InsertActionException:
            return

        zwei_actions.send(action)

    def trigger_content_ad_status(self, request=None):
        if not self.obj.can_manage_content_ads:
            return

        order = actionlog.models.ActionLogOrder.objects.create(
            order_type=actionlog.constants.ActionLogOrderType.GET_CONTENT_AD_STATUS
        )

        if not dash.models.ContentAdSource.objects.filter(
                content_ad__ad_group=self.obj.ad_group,
                source=self.obj.source).exists():
            return

        try:
            api_contentads.init_get_content_ad_status_action(self.obj, order, request)
        except InsertActionException:
            return

    def trigger_reports(self, request=None):
        dates = self.get_dates_to_sync_reports()
        self.trigger_reports_for_dates(dates, actionlog.constants.ActionLogOrderType.FETCH_REPORTS, request)

    def trigger_reports_for_dates(self, dates, order_type=None, request=None):
        actions = []
        with transaction.atomic():
            order = None
            if order_type is not None:
                order = actionlog.models.ActionLogOrder.objects.create(order_type=order_type)
            for date in dates:
                try:
                    action = api._init_fetch_reports(self.obj, date, order, request)
                except InsertActionException:
                    continue

                actions.append(action)

        zwei_actions.send(actions)

    def trigger_reports_by_publisher_for_dates(self, dates, order_type=None, request=None):
        actions = []
        with transaction.atomic():
            order = None
            if order_type is not None:
                order = actionlog.models.ActionLogOrder.objects.create(order_type=order_type)
            for date in dates:
                try:
                    action = api._init_fetch_reports_by_publisher(self.obj, date, order, request)
                except InsertActionException:
                    continue
                actions.append(action)

        zwei_actions.send(actions)

    def get_dates_to_sync_reports(self):
        start_dt = None
        latest_sync_dt = self.obj.last_successful_sync_dt
        if latest_sync_dt:
            start_dt = latest_sync_dt.date() - timedelta(days=settings.LAST_N_DAY_REPORTS - 1)
        else:
            return last_n_days(settings.LAST_N_DAY_REPORTS)
        dates = [start_dt]
        today = datetime.utcnow().date()
        while dates[-1] < today:
            dates.append(dates[-1] + timedelta(days=1))
        assert(dates[-1] == today)
        return reversed(dates)
