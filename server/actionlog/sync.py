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

    def get_latest_success(self, recompute=True):
        child_syncs = self.get_components()
        child_sync_times = [child_sync.get_latest_success(recompute) for child_sync in child_syncs]
        if not child_sync_times:
            return None
        if None in child_sync_times:
            return None
        return min(child_sync_times)

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


class ISyncComposite(object):

    def get_components(self):
        raise NotImplementedError


class GlobalSync(BaseSync, ISyncComposite):

    def __init__(self):
        pass

    def get_components(self):
        for account in dash.models.Account.objects.all():
            account_sync = AccountSync(account)
            if len(list(account_sync.get_components())) > 0:
                yield account_sync


class AccountSync(BaseSync, ISyncComposite):

    def get_components(self):
        for campaign in dash.models.Campaign.objects.filter(account=self.obj):
            campaign_sync = CampaignSync(campaign)
            if len(list(campaign_sync.get_components())) > 0:
                yield campaign_sync


class CampaignSync(BaseSync, ISyncComposite):

    def get_components(self):
        for ad_group in dash.models.AdGroup.objects.filter(campaign=self.obj):
            ad_group_sync = AdGroupSync(ad_group)
            if len(list(ad_group_sync.get_components())) > 0:
                yield ad_group_sync


class AdGroupSync(BaseSync, ISyncComposite):

    def get_components(self):
        for ags in dash.models.AdGroupSource.objects.filter(ad_group=self.obj, source__maintenance=False):
            yield AdGroupSourceSync(ags)


class AdGroupSourceSync(BaseSync):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source

    def get_latest_success(self, recompute=True):
        if recompute:
            status_sync_dt = self.get_latest_status_sync()
            if not status_sync_dt:
                return None
            report_sync_dt = self.get_latest_report_sync()
            if not report_sync_dt:
                return None
            return min(status_sync_dt, report_sync_dt)
        else:
            return self.ad_group_source.last_successful_sync_dt

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
            self.ad_group_source.id,
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
                ad_group_source=self.ad_group_source,
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
            action = _init_fetch_status(self.ad_group_source, order)
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
                    action = _init_fetch_reports(self.ad_group_source, date, order)
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
            if self.ad_group_source.ad_group.created_dt is not None:
                start_dt = self.ad_group_source.ad_group.created_dt.date()
            else:
                return last_n_days(settings.LAST_N_DAY_REPORTS)
        dates = [start_dt]
        today = datetime.datetime.utcnow().date()
        while dates[-1] < today:
            dates.append(dates[-1] + datetime.timedelta(days=1))
        assert(dates[-1] == today)
        return reversed(dates)
