import datetime
import dash.models
import actionlog.models
import actionlog.constants

from actionlog.api import _init_fetch_status, _init_fetch_reports, InsertActionException
from utils.command_helpers import last_n_days
from . import zwei_actions

from django.conf import settings
from django.db import transaction


class BaseSync(object):

    def __init__(self, obj):
        self.obj = obj

    def get_latest_success_by_child(self, recompute=True, include_level_archived=False):
        return {
            child_sync.obj.id: _min_none(child_sync.get_latest_success_by_child(
                recompute,
            ).values()) for child_sync in self.get_components(archived=include_level_archived)
        }

    def get_latest_source_success(self, recompute=True, include_maintenance=False):
        child_syncs = self.get_components(maintenance=include_maintenance)
        child_source_sync_times_list = [
            child_sync.get_latest_source_success(recompute)
            for child_sync in child_syncs
        ]

        return self._merge_sync_times(child_source_sync_times_list)

    def trigger_all(self):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_all()

    def trigger_reports(self):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_reports()

    def trigger_status(self):
        child_syncs = self.get_components()
        for child_sync in child_syncs:
            child_sync.trigger_status()

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

    def __init__(self):
        pass

    def get_components(self, maintenance=False, archived=False):
        accounts = dash.models.Account.objects.all()
        if not archived:
            accounts = accounts.exclude_archived()

        for account in accounts:
            account_sync = AccountSync(account)
            if len(list(account_sync.get_components(maintenance=maintenance))) > 0:
                yield account_sync

    def get_latest_success_by_account(self):
        '''
        this function is a faster way to get last succcessful sync times
        on the account level
        '''
        qs = dash.models.AdGroupSource.objects.\
            filter(source__maintenance=False).\
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

    def get_latest_success_by_source(self, include_maintenance=False):
        '''
        this function is a faster way to get last succcessful sync times
        by source on globally
        '''
        qs = dash.models.AdGroupSource.objects.\
            filter(ad_group__in=dash.models.AdGroup.objects.all().exclude_archived()).\
            select_related('source').\
            values('source', 'last_successful_sync_dt')

        if not include_maintenance:
            qs = qs.filter(source__maintenance=False)

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
        now = datetime.datetime.now()
        for account in demo_accounts:
            result[account.id] = now
        return result


class AccountSync(BaseSync, ISyncComposite):

    def get_components(self, maintenance=False, archived=False):
        campaigns = dash.models.Campaign.objects.filter(account=self.obj)
        if not archived:
            campaigns = campaigns.exclude_archived()

        for campaign in campaigns:
            campaign_sync = CampaignSync(campaign)
            if len(list(campaign_sync.get_components(maintenance))) > 0:
                yield campaign_sync


class CampaignSync(BaseSync, ISyncComposite):

    def get_components(self, maintenance=False, archived=False):
        ad_groups = dash.models.AdGroup.objects.filter(campaign=self.obj)
        if not archived:
            ad_groups = ad_groups.exclude_archived()

        for ad_group in ad_groups:
            ad_group_sync = AdGroupSync(ad_group)
            if len(list(ad_group_sync.get_components(maintenance))) > 0:
                yield ad_group_sync


class AdGroupSync(BaseSync, ISyncComposite):

    def __init__(self, obj):
        super(AdGroupSync, self).__init__(obj)
        self.real_ad_group = self.obj
        if self.obj in dash.models.AdGroup.demo_objects.all():
            self.real_ad_group = dash.models.DemoAdGroupRealAdGroup.objects.get(demo_ad_group=self.obj).real_ad_group

    def get_components(self, maintenance=False, archived=False):
        qs = dash.models.AdGroupSource.objects.filter(ad_group=self.real_ad_group)
        if not maintenance:
            qs = qs.filter(source__maintenance=False)

        for ags in qs:
            yield AdGroupSourceSync(ags)


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
        return {self.obj.id: self._get_latest_success(recompute)}

    def get_latest_source_success(self, recompute=True, include_maintenance=False):
        return {self.obj.source_id: self._get_latest_success(recompute)}

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

    def trigger_all(self):
        self.trigger_status()
        self.trigger_reports()

    def trigger_status(self):
        order = actionlog.models.ActionLogOrder.objects.create(
            order_type=actionlog.constants.ActionLogOrderType.FETCH_STATUS
        )
        try:
            action = _init_fetch_status(self.obj, order)
        except InsertActionException:
            pass
        else:
            zwei_actions.send(action)

    def trigger_reports(self):
        dates = self.get_dates_to_sync_reports()
        self.trigger_reports_for_dates(dates, actionlog.constants.ActionLogOrderType.FETCH_REPORTS)

    def trigger_reports_for_dates(self, dates, order_type=None):
        actions = []
        with transaction.atomic():
            order = None
            if order_type is not None:
                order = actionlog.models.ActionLogOrder.objects.create(order_type=order_type)
            for date in dates:
                try:
                    action = _init_fetch_reports(self.obj, date, order)
                except InsertActionException:
                    continue

                actions.append(action)

        zwei_actions.send_multiple(actions)

    def get_dates_to_sync_reports(self):
        start_dt = None
        latest_report_sync_dt = self.get_latest_report_sync()
        if latest_report_sync_dt:
            start_dt = latest_report_sync_dt.date() - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS - 1)
        else:
            if self.obj.ad_group.created_dt is not None:
                start_dt = self.obj.ad_group.created_dt.date()
            else:
                return last_n_days(settings.LAST_N_DAY_REPORTS)
        dates = [start_dt]
        today = datetime.datetime.utcnow().date()
        while dates[-1] < today:
            dates.append(dates[-1] + datetime.timedelta(days=1))
        assert(dates[-1] == today)
        return reversed(dates)


def _min_none(values):
    if None in values:
        return None
    return min(values)
