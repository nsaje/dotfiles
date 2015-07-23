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

    @newrelic.agent.function_trace()
    def get_latest_success_by_child(self, recompute=True, include_level_archived=False):
        return {
            child_sync.obj.id: _min_none(child_sync.get_latest_success_by_child(
                recompute,
            ).values()) for child_sync in self.get_components(archived=include_level_archived)
        }

    @newrelic.agent.function_trace()
    def get_latest_source_success(self, recompute=True, include_maintenance=False, include_deprecated=False):
        child_syncs = self.get_components(maintenance=include_maintenance, deprecated=include_deprecated)
        child_source_sync_times_list = [
            child_sync.get_latest_source_success(recompute=recompute, include_maintenance=include_maintenance, include_deprecated=include_deprecated)
            for child_sync in child_syncs
        ]

        return self._merge_sync_times(child_source_sync_times_list)

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

    def _merge_sync_times(self, sync_times_list):
        merged_sync_times = {}
        for sync_times in sync_times_list:
            for key, value in sync_times.items():
                if key in merged_sync_times:
                    old_value = merged_sync_times[key]

                    if old_value is None or value is None:
                        value = None
                    else:
                        value = min(old_value, value)

                merged_sync_times[key] = value

        return merged_sync_times


class ISyncComposite(object):

    def get_components(self):
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

    def get_latest_success_by_account(self):
        '''
        this function is a faster way to get last succcessful sync times
        on the account level
        '''
        qs = dash.models.AdGroupSource.objects.\
            filter(source__maintenance=False).\
            filter(source__deprecated=False).\
            filter(source__in=self.sources).\
            filter(ad_group__in=dash.models.AdGroup.objects.all().exclude_archived()).\
            select_related('ad_group__campaign__account', 'source').\
            values('ad_group__campaign__account', 'last_successful_sync_dt')

        latest_success = {}
        for row in qs:
            aid = row['ad_group__campaign__account']
            if aid not in latest_success:
                latest_success[aid] = []
            latest_success[aid].append(row['last_successful_sync_dt'])
        result = {k: _min_none(v) for k, v in latest_success.iteritems()}
        result = self._add_demo_accounts_sync_times(result)
        return result

    @newrelic.agent.function_trace()
    def get_latest_success_by_source(self, include_maintenance=False, include_deprecated=False):
        '''
        this function is a faster way to get last succcessful sync times
        by source on globally
        '''
        qs = dash.models.AdGroupSource.objects.\
            filter(ad_group__in=dash.models.AdGroup.objects.all().exclude_archived()).\
            filter(source__in=self.sources).\
            select_related('source').\
            values('source', 'last_successful_sync_dt')

        if not include_maintenance:
            qs = qs.filter(source__maintenance=False)

        if not include_deprecated:
            qs = qs.filter(source__deprecated=False)

        latest_success = {}
        for row in qs:
            if row['source'] not in latest_success:
                latest_success[row['source']] = row['last_successful_sync_dt']
            else:
                latest_success[row['source']] = _min_none([
                    latest_success[row['source']], row['last_successful_sync_dt']
                ])

        return latest_success

    def _add_demo_accounts_sync_times(self, result):
        demo_accounts = dash.models.Account.demo_objects.all()
        utcnow = datetime.utcnow()
        for account in demo_accounts:
            result[account.id] = utcnow
        return result


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
    def _get_ad_group_sources(self, include_level_archived=False, include_maintenance=False, include_deprecated=False):
        campaigns = dash.models.Campaign.objects.filter(account=self.obj)
        if not include_level_archived:
            campaigns = campaigns.exclude_archived()

        ad_groups = dash.models.AdGroup.objects\
                                       .filter(campaign__in=campaigns)\
                                       .exclude_archived()
        ad_group_sources = dash.models.AdGroupSource.objects\
                                                    .filter(ad_group=ad_groups)\
                                                    .filter(source__in=self.sources)\
                                                    .select_related('ad_group', 'source')

        if not include_maintenance:
            ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

        if not include_deprecated:
            ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

        return ad_group_sources

    @newrelic.agent.function_trace()
    def get_latest_success_by_child(self, include_level_archived=False):
        result = {}

        ad_group_sources = self._get_ad_group_sources(include_level_archived=include_level_archived)
        vals = ad_group_sources.values_list('ad_group__campaign_id', 'last_successful_sync_dt')
        for campaign_id, last_successful_sync_dt in vals:
            if campaign_id not in result:
                result[campaign_id] = last_successful_sync_dt

            result[campaign_id] = _min_none(
                [result[campaign_id], last_successful_sync_dt]
            )

        if self.obj.id in dash.models.Account.demo_objects.all().values_list('id', flat=True):
            for campaign in self.obj.campaign_set.all():
                if campaign.id not in result:
                    result[campaign.id] = datetime.utcnow()

        return result

    @newrelic.agent.function_trace()
    def get_latest_source_success(self, include_maintenance=False, include_deprecated=False):
        result = {}

        ad_group_sources = self._get_ad_group_sources(include_maintenance=include_maintenance,
                                                      include_deprecated=include_deprecated)
        vals = ad_group_sources.values_list('source_id', 'last_successful_sync_dt')
        for source_id, last_successful_sync_dt in vals:
            if source_id not in result:
                result[source_id] = last_successful_sync_dt

            result[source_id] = _min_none(
                [result[source_id], last_successful_sync_dt]
            )

        if self.obj.id in dash.models.Account.demo_objects.all().values_list('id', flat=True):
            for source in self.sources:
                if source.id not in result:
                    result[source.id] = datetime.utcnow()

        return result


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


class AdGroupSync(BaseSync, ISyncComposite):

    @newrelic.agent.function_trace()
    def __init__(self, obj, sources=None):
        super(AdGroupSync, self).__init__(obj, sources=sources)
        self.real_ad_group = self.obj
        if self.obj in dash.models.AdGroup.demo_objects.all():
            self.real_ad_group = dash.models.DemoAdGroupRealAdGroup\
                                            .objects\
                                            .select_related('real_ad_group')\
                                            .prefetch_related('real_ad_group__adgroupsource_set__source')\
                                            .get(demo_ad_group=self.obj)\
                                            .real_ad_group

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


class AdGroupSourceSync(BaseSync):

    def _get_latest_success(self, recompute=True):
        if recompute:
            status_sync_dt = self.get_latest_status_sync()
            if not status_sync_dt:
                return None
            report_sync_dt = self.get_latest_report_sync()
            if not report_sync_dt:
                return None
            return min(status_sync_dt, report_sync_dt)
        else:
            return self.obj.last_successful_sync_dt

    def get_latest_success_by_child(self, recompute=True, include_level_archive=False):
        return {self.obj.id: self._get_latest_success(recompute=recompute)}

    @newrelic.agent.function_trace()
    def get_latest_source_success(self, recompute=True, include_maintenance=False, include_deprecated=False):
        return {self.obj.source_id: self._get_latest_success(recompute=recompute)}

    def get_latest_report_sync(self):
        # the query below works like this:
        # - we look at actionlogs with action=get_rtepors
        # - we group the actions in the actionlog by order_id
        # - we count how many successes there are and compare it to the total number of rows (therefore the CAST)
        # - finally we join with the actionlog_actionlogorder table to get the 'created_dt'
        sql = '''
        SELECT ord.id, ord.created_dt, ord.order_type, action, order_id, n_success, tot
        FROM (
            SELECT action, order_id,
                SUM(CAST(state=2 AS INTEGER)) AS n_success, count(*) AS tot
            FROM actionlog_actionlog
            WHERE action=%s
            AND ad_group_source_id=%s
            GROUP BY action, order_id
        ) AS foo,
        actionlog_actionlogorder AS ord
        WHERE n_success = tot
        AND ord.id = order_id
        AND ord.order_type = %s
        ORDER BY ord.created_dt DESC
        LIMIT 1
        '''
        params = [
            actionlog.constants.Action.FETCH_REPORTS,
            self.obj.id,
            actionlog.constants.ActionLogOrderType.FETCH_REPORTS
        ]
        results = actionlog.models.ActionLogOrder.objects.raw(sql, params)

        if list(results):
            return results[0].created_dt
        else:
            return None

    def get_latest_status_sync(self):
        try:
            action = actionlog.models.ActionLog.objects.filter(
                ad_group_source=self.obj,
                action=actionlog.constants.Action.FETCH_CAMPAIGN_STATUS,
                action_type=actionlog.constants.ActionType.AUTOMATIC,
                state=actionlog.constants.ActionState.SUCCESS
            ).latest('created_dt')
            return action.created_dt
        except:
            return None

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

        zwei_actions.send_multiple(actions)

    def get_dates_to_sync_reports(self):
        start_dt = None
        latest_sync_dt = self._get_latest_success(recompute=False)
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


def _min_none(values):
    if None in values:
        return None
    return min(values)
