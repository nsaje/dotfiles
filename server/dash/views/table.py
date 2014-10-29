import reports.api
import actionlog.sync
import pytz

import utils.pagination

from django.core import urlresolvers

from dash.views import helpers
from dash import models
from dash import budget
from dash import constants
from dash import api
from utils import api_common
from utils import statsd_helper
from utils import exc
from utils.sort_helper import sort_results


def sort_rows_by_order_and_archived(rows, order):
    archived_order = 'archived'
    if order.startswith('-'):
        archived_order = '-' + archived_order

    return sort_results(rows, [archived_order, order])


class AllAccountsSourcesTable(object):
    def __init__(self, user, id_):
        self.user = user
        self.accounts = models.Account.objects.get_for_user(user)
        self.inactive_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(account=self.accounts)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, self.accounts)

    def get_sources(self):
        source_ids = models.AdGroupSource.objects.\
            filter(ad_group__campaign__account__in=self.accounts).\
            exclude(id__in=[s.id for s in self.inactive_ad_group_sources]).\
            values('source_id').\
            distinct()

        source_ids = [s['source_id'] for s in source_ids]

        return models.Source.objects.filter(id__in=source_ids)

    def get_sources_settings(self):
        return models.AdGroupSourceSettings.objects.\
            distinct('ad_group_source').\
            filter(ad_group_source__ad_group__campaign__account=self.accounts).\
            exclude(ad_group_source__in=self.inactive_ad_group_sources).\
            order_by('ad_group_source', '-created_dt')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            account=self.accounts
        ), self.user)

        totals_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=self.accounts
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(account=self.accounts)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        return actionlog.sync.GlobalSync().get_latest_success_by_source()

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=self.accounts)


class AccountSourcesTable(object):
    def __init__(self, user, id_):
        self.user = user
        self.account = helpers.get_account(user, id_)
        self.inactive_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(account=self.account)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, [self.account])

    def get_sources(self):
        source_ids = models.AdGroupSource.objects.\
            filter(ad_group__campaign__account=self.account).\
            exclude(id__in=[s.id for s in self.inactive_ad_group_sources]).\
            values('source_id').\
            distinct()

        source_ids = [s['source_id'] for s in source_ids]

        return models.Source.objects.filter(id__in=source_ids)

    def get_sources_settings(self):
        return models.AdGroupSourceSettings.objects.\
            distinct('ad_group_source').\
            filter(ad_group_source__ad_group__campaign__account=self.account).\
            exclude(ad_group_source__in=self.inactive_ad_group_sources).\
            order_by('ad_group_source', '-created_dt')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            account=self.account
        ), self.user)

        totals_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=self.account
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(account=self.account)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        return actionlog.sync.AccountSync(self.account).get_latest_source_success(
            recompute=False)

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=[self.account])


class CampaignSourcesTable(object):
    def __init__(self, user, id_):
        self.user = user
        self.campaign = helpers.get_campaign(user, id_)
        self.inactive_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(campaign=self.campaign)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_campaigns(
            start_date, end_date, [self.campaign])

    def get_sources(self):
        source_ids = models.AdGroupSource.objects.\
            filter(ad_group__campaign=self.campaign).\
            exclude(id__in=[s.id for s in self.inactive_ad_group_sources]).\
            values('source_id').\
            distinct()

        source_ids = [s['source_id'] for s in source_ids]

        return models.Source.objects.filter(id__in=source_ids)

    def get_sources_settings(self):
        return models.AdGroupSourceSettings.objects.\
            distinct('ad_group_source').\
            filter(ad_group_source__ad_group__campaign=self.campaign).\
            exclude(ad_group_source__in=self.inactive_ad_group_sources).\
            order_by('ad_group_source', '-created_dt')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            campaign=self.campaign
        ), self.user)

        totals_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            campaign=self.campaign
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(campaign=self.campaign)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        return actionlog.sync.CampaignSync(self.campaign).get_latest_source_success(
            recompute=False)

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(campaigns=[self.campaign])


class AdGroupSourcesTable(object):
    def __init__(self, user, id_):
        self.user = user
        self.ad_group = helpers.get_ad_group(user, id_)
        self.inactive_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(ad_group=self.ad_group)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_ad_groups(
            start_date, end_date, [self.ad_group])

    def get_sources(self):
        return models.Source.objects.\
            exclude(adgroupsource__in=self.inactive_ad_group_sources).\
            filter(adgroupsource__ad_group=self.ad_group)\
            .distinct('id')

    def get_sources_settings(self):
        return models.AdGroupSourceSettings.objects.\
            distinct('ad_group_source').\
            filter(ad_group_source__ad_group=self.ad_group).\
            exclude(ad_group_source__in=self.inactive_ad_group_sources).\
            order_by('ad_group_source', '-created_dt')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            ad_group=self.ad_group
        ), self.user)

        totals_stats = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ad_group=self.ad_group
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(ad_group=self.ad_group)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        return actionlog.sync.AdGroupSync(self.ad_group).get_latest_source_success(
            recompute=False)

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(ad_groups=[self.ad_group])


class SourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_get')
    def get(self, request, level_, id_=None):
        user = request.user

        if level_ == 'all_accounts':
            self.levelSourcesTable = AllAccountsSourcesTable(user, id_)
        elif level_ == 'accounts':
            self.levelSourcesTable = AccountSourcesTable(user, id_)
        elif level_ == 'campaigns':
            self.levelSourcesTable = CampaignSourcesTable(user, id_)
        elif level_ == 'ad_groups':
            self.levelSourcesTable = AdGroupSourcesTable(user, id_)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        sources = self.levelSourcesTable.get_sources()
        sources_settings = self.levelSourcesTable.get_sources_settings()
        last_success_actions = self.levelSourcesTable.get_last_success_actions()
        sources_data, totals_data = self.levelSourcesTable.get_stats(start_date, end_date)
        is_sync_in_progress = self.levelSourcesTable.is_sync_in_progress()

        yesterday_cost = {}
        yesterday_total_cost = None
        if user.has_perm('reports.yesterday_spend_view'):
            yesterday_cost, yesterday_total_cost = self.levelSourcesTable.\
                get_yesterday_cost()

        last_sync = None
        if last_success_actions.values() and None not in last_success_actions.values():
            last_sync = min(last_success_actions.values())

        incomplete_postclick_metrics = False
        if user.has_perm('zemauth.postclick_metrics'):
            incomplete_postclick_metrics = \
                not self.levelSourcesTable.has_complete_postclick_metrics(
                    start_date, end_date)

        return self.create_api_response({
            'rows': self.get_rows(
                id_,
                sources,
                sources_data,
                sources_settings,
                last_success_actions,
                yesterday_cost,
                order=request.GET.get('order', None),
                ad_group_level=level_ == 'ad_groups'
            ),
            'totals': self.get_totals(
                totals_data,
                sources_settings,
                yesterday_total_cost
            ),
            'last_sync': pytz.utc.localize(last_sync).isoformat(),  # needs time offset
            'is_sync_recent': helpers.is_sync_recent(last_sync),
            'is_sync_in_progress': is_sync_in_progress,
            'incomplete_postclick_metrics': incomplete_postclick_metrics,
        })

    def get_totals(self, totals_data, sources_settings, yesterday_cost):
        return {
            'daily_budget': self.get_daily_budget_total(sources_settings),
            'cost': totals_data['cost'],
            'cpc': totals_data['cpc'],
            'clicks': totals_data['clicks'],
            'impressions': totals_data['impressions'],
            'ctr': totals_data['ctr'],
            'yesterday_cost': yesterday_cost,

            'visits': totals_data.get('visits'),
            'pageviews': totals_data.get('pageviews'),
            'percent_new_users': totals_data.get('percent_new_users'),
            'bounce_rate': totals_data.get('bounce_rate'),
            'pv_per_visit': totals_data.get('pv_per_visit'),
            'avg_tos': totals_data.get('avg_tos'),
            'click_discrepancy': totals_data.get('click_discrepancy'),

            'goals': totals_data.get('goals', {})
        }

    def get_state(self, settings):
        if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE for s in settings):
            return constants.AdGroupSourceSettingsState.ACTIVE

        return constants.AdGroupSourceSettingsState.INACTIVE

    def get_daily_budget_total(self, sources_settings):
        budgets = [s.daily_budget_cc for s in sources_settings if
                   s.daily_budget_cc is not None and
                   s.state == constants.AdGroupSourceSettingsState.ACTIVE]

        return sum(budgets)

    def get_rows(
            self,
            id_,
            sources,
            sources_data,
            sources_settings,
            last_actions,
            yesterday_cost,
            order=None,
            ad_group_level=False):
        rows = []
        for source in sources:
            settings = [s for s in sources_settings if s.ad_group_source.source_id == source.id]

            # get source reports data
            source_data = {}
            for item in sources_data:
                if item['source'] == source.id:
                    source_data = item
                    break

            last_sync = last_actions.get(source.id)

            supply_dash_url = None
            if ad_group_level:
                supply_dash_url = urlresolvers.reverse('dash.views.views.supply_dash_redirect')
                supply_dash_url += '?ad_group_id={}&source_id={}'.format(id_, source.id)

                daily_budget = settings[0].daily_budget_cc if len(settings) else None
            else:
                daily_budget = self.get_daily_budget_total(settings)

            row = {
                'id': str(source.id),
                'name': source.name,
                'daily_budget': daily_budget,
                'status': self.get_state(settings),
                'cost': source_data.get('cost', None),
                'cpc': source_data.get('cpc', None),
                'clicks': source_data.get('clicks', None),
                'impressions': source_data.get('impressions', None),
                'ctr': source_data.get('ctr', None),

                'visits': source_data.get('visits', None),
                'pageviews': source_data.get('pageviews', None),
                'percent_new_users': source_data.get('percent_new_users', None),
                'bounce_rate': source_data.get('bounce_rate', None),
                'pv_per_visit': source_data.get('pv_per_visit', None),
                'avg_tos': source_data.get('avg_tos', None),
                'click_discrepancy': source_data.get('click_discrepancy', None),

                'last_sync': last_sync,
                'yesterday_cost': yesterday_cost.get(source.id),
                'supply_dash_url': supply_dash_url,

                'goals': source_data.get('goals', {})
            }

            bid_cpc_values = [s.cpc_cc for s in settings if s.cpc_cc is not None]

            if len(bid_cpc_values) > 0:
                row['min_bid_cpc'] = float(min(bid_cpc_values))
                row['max_bid_cpc'] = float(max(bid_cpc_values))

            if len(bid_cpc_values) == 1:
                row['bid_cpc'] = bid_cpc_values[0]

            # add conversion fields
            for field, val in source_data.iteritems():
                if field.startswith('G[') and field.endswith('_conversionrate'):
                    row[field] = val

            rows.append(row)

        if order:
            rows = sort_results(rows, [order])

        return rows


class AccountsAccountsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_accounts_table_get')
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        page = request.GET.get('page')
        size = request.GET.get('size')
        order = request.GET.get('order')

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and request.user.has_perm('zemauth.view_archived_entities')

        user = request.user

        accounts = models.Account.objects.get_for_user(user)
        account_ids = set(acc.id for acc in accounts)

        accounts_settings = models.AccountSettings.objects.\
            distinct('account').\
            filter(account__in=accounts).\
            order_by('account_id', '-created_dt')

        size = max(min(int(size or 5), 50), 1)
        if page:
            page = int(page)

        accounts_data = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['account'],
            account=accounts
        ), request.user)

        totals_data = reports.api.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=accounts
        ), request.user)

        all_accounts_budget = budget.GlobalBudget().get_total_by_account()
        account_budget = {aid: all_accounts_budget.get(aid, 0) for aid in account_ids}

        all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()
        account_total_spend = {aid: all_accounts_total_spend.get(aid, 0) for aid in account_ids}

        totals_data['budget'] = sum(account_budget.itervalues())
        totals_data['available_budget'] = totals_data['budget'] - sum(account_total_spend.values())

        last_success_actions = actionlog.sync.GlobalSync().get_latest_success_by_account()
        last_success_actions = {aid: val for aid, val in last_success_actions.items() if aid in account_ids}

        last_sync = None
        if last_success_actions.values() and None not in last_success_actions.values():
            last_sync = min(last_success_actions.values())

        rows = self.get_rows(
            accounts,
            accounts_settings,
            accounts_data,
            last_success_actions,
            account_budget,
            account_total_spend,
            has_view_archived_permission,
            show_archived,
            order=order,
        )

        rows, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(rows, page, size)

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_accounts(
                start_date, end_date, accounts
            ) if request.user.has_perm('zemauth.postclick_metrics') else False

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat(),  # needs time offset
            'is_sync_recent': helpers.is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(accounts=accounts),
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            },
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        })

    def get_rows(self, accounts, accounts_settings, accounts_data, last_actions, account_budget,
                 account_total_spend, has_view_archived_permission, show_archived, order=None):
        rows = []

        account_state = api.get_state_by_account()
        for account in accounts:
            aid = account.pk
            row = {
                'id': str(aid),
                'name': account.name
            }

            # get source reports data
            account_data = {}
            for item in accounts_data:
                if item['account'] == aid:
                    account_data = item
                    break

            archived = False
            for account_settings in accounts_settings:
                if account_settings.account.pk == account.pk:
                    archived = account_settings.archived
                    break

            if has_view_archived_permission and not show_archived and archived and\
               not (reports.api.row_has_traffic_data(account_data) or
                    reports.api.row_has_postclick_data(account_data)):
                continue

            state = account_state.get(aid, constants.AdGroupSettingsState.INACTIVE)
            row['status'] = state

            if has_view_archived_permission:
                row['archived'] = archived

            row['last_sync'] = last_actions.get(aid)
            if row['last_sync']:
                row['last_sync'] = row['last_sync']

            row.update(account_data)

            row['budget'] = account_budget[aid]

            row['available_budget'] = row['budget'] - account_total_spend[aid]

            rows.append(row)

        if order:
            if 'status' in order and has_view_archived_permission:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows


class AdGroupAdsTable(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_table_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        page = request.GET.get('page')
        size = request.GET.get('size')
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        size = max(min(int(size or 5), 50), 1)

        result = reports.api.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['article'],
            order=[order],
            ad_group=ad_group.id
        ), request.user)

        result_pg, current_page, num_pages, count, start_index, end_index = \
            utils.pagination.paginate(result, page, size)

        rows = result_pg

        totals_data = reports.api.filter_by_permissions(reports.api.query(start_date, end_date, ad_group=int(ad_group.id)), request.user)

        last_sync = actionlog.sync.AdGroupSync(ad_group).get_latest_success(
            recompute=False)

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_ad_groups(
                start_date, end_date, [ad_group]
            ) if request.user.has_perm('zemauth.postclick_metrics') else False

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat(),  # needs time offset
            'is_sync_recent': helpers.is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group]),
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            },
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        })


class CampaignAdGroupsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_ad_groups_table_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-cost'

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and request.user.has_perm('zemauth.view_archived_entities')

        stats = reports.api.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['ad_group'],
            order=[order],
            campaign=campaign
        ), request.user)

        ad_groups = campaign.adgroup_set.all()
        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group').\
            filter(ad_group__campaign=campaign).\
            order_by('ad_group', '-created_dt')

        totals_stats = reports.api.filter_by_permissions(
            reports.api.query(
                start_date,
                end_date,
                ad_group=ad_groups
            ),
            request.user
        )

        last_success_actions = {}
        for ad_group in ad_groups:
            ad_group_sync = actionlog.sync.AdGroupSync(ad_group)

            if not len(list(ad_group_sync.get_components())):
                continue

            last_success_actions[ad_group.pk] = ad_group_sync.get_latest_success(
                recompute=False)

        last_sync = actionlog.sync.CampaignSync(campaign).get_latest_success(
            recompute=False)

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date, end_date, [campaign]
            ) if request.user.has_perm('zemauth.postclick_metrics') else False

        return self.create_api_response({
            'rows': self.get_rows(
                ad_groups,
                ad_groups_settings,
                stats,
                last_success_actions,
                order,
                has_view_archived_permission,
                show_archived
            ),
            'totals': totals_stats,
            'last_sync': pytz.utc.localize(last_sync).isoformat(),
            'is_sync_recent': helpers.is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=[campaign]),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        })

    def get_rows(self, ad_groups, ad_groups_settings, stats, last_actions,
                 order, has_view_archived_permission, show_archived):
        rows = []
        for ad_group in ad_groups:
            row = {
                'name': ad_group.name,
                'ad_group': str(ad_group.pk)
            }

            ad_group_data = {}
            for stat in stats:
                if ad_group.pk == stat['ad_group']:
                    ad_group_data = stat
                    break

            state = models.AdGroupSettings.get_default_value('state')
            archived = False
            for ad_group_settings in ad_groups_settings:
                if ad_group.pk == ad_group_settings.ad_group_id:
                    archived = ad_group_settings.archived
                    if ad_group_settings.state is not None:
                        state = ad_group_settings.state

                    break

            if has_view_archived_permission and not show_archived and archived and\
               not (reports.api.row_has_traffic_data(ad_group_data) or
                    reports.api.row_has_postclick_data(ad_group_data)):
                continue

            row['state'] = state

            if has_view_archived_permission:
                row['archived'] = archived

            row.update(ad_group_data)

            last_sync = last_actions.get(ad_group.pk)

            row['last_sync'] = last_sync

            rows.append(row)

        if order:
            if 'state' in order and has_view_archived_permission:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows


class AccountCampaignsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_campaigns_table_get')
    def get(self, request, account_id):
        user = request.user

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and request.user.has_perm('zemauth.view_archived_entities')

        campaigns = models.Campaign.objects.get_for_user(user).\
            filter(account=account_id)

        campaigns_settings = models.CampaignSettings.objects.\
            distinct('campaign').\
            filter(campaign__in=campaigns).\
            order_by('campaign', '-created_dt')

        stats = reports.api.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['campaign'],
            order=[order],
            campaign=campaigns
        ), request.user)

        totals_stats = reports.api.filter_by_permissions(
            reports.api.query(start_date, end_date, campaign=campaigns),
            request.user
        )

        totals_stats['budget'] = sum(budget.CampaignBudget(campaign).get_total()
                                     for campaign in campaigns)
        total_spend = sum(budget.CampaignBudget(campaign).get_spend() \
                                     for campaign in campaigns)
        totals_stats['available_budget'] = totals_stats['budget'] - total_spend

        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group').\
            filter(ad_group__campaign__in=campaigns).\
            order_by('ad_group', '-created_dt')

        last_success_actions = {}
        for campaign in campaigns:
            campaign_sync = actionlog.sync.CampaignSync(campaign)
            if len(list(campaign_sync.get_components())) > 0:
                last_success_actions[campaign.pk] = campaign_sync.get_latest_success(recompute=False)

        last_sync = None
        if last_success_actions.values() and None not in last_success_actions.values():
            last_sync = min(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date, end_date, campaigns
            ) if request.user.has_perm('zemauth.postclick_metrics') else False

        return self.create_api_response({
            'rows': self.get_rows(
                campaigns,
                campaigns_settings,
                ad_groups_settings,
                stats,
                last_success_actions,
                order,
                has_view_archived_permission,
                show_archived
            ),
            'totals': totals_stats,
            'last_sync': pytz.utc.localize(last_sync).isoformat(),
            'is_sync_recent': helpers.is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=campaigns),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        })

    def get_rows(self, campaigns, campaigns_settings, ad_groups_settings, stats,
                 last_actions, order, has_view_archived_permission, show_archived):
        rows = []
        for campaign in campaigns:
            # If at least one ad group is active, then the campaign is considered
            # active.

            row = {
                'campaign': str(campaign.pk),
                'name': campaign.name,
            }

            campaign_stat = {}
            for stat in stats:
                if stat['campaign'] == campaign.pk:
                    campaign_stat = stat
                    break

            archived = False
            for campaign_settings in campaigns_settings:
                if campaign_settings.campaign.pk == campaign.pk:
                    archived = campaign_settings.archived
                    break

            if has_view_archived_permission and not show_archived and archived and\
               not (reports.api.row_has_traffic_data(campaign_stat) or
                    reports.api.row_has_postclick_data(campaign_stat)):
                continue

            state = constants.AdGroupSettingsState.INACTIVE
            for ad_group_settings in ad_groups_settings:
                if ad_group_settings.ad_group.campaign.pk == campaign.pk and \
                        ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
                    state = constants.AdGroupSettingsState.ACTIVE
                    break

            row['state'] = state

            if has_view_archived_permission:
                row['archived'] = archived

            last_sync = last_actions.get(campaign.pk)

            row['last_sync'] = last_sync

            row.update(campaign_stat)

            row['budget'] = budget.CampaignBudget(campaign).get_total()
            row['available_budget'] = row['budget'] - budget.CampaignBudget(campaign).get_spend()

            rows.append(row)

        if order:
            if 'state' in order and has_view_archived_permission:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows
