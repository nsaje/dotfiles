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


def compute_daily_budget_total(data):
    budgets = [s.daily_budget_cc for s in data if
               s is not None and s.daily_budget_cc is not None and
               s.state == constants.AdGroupSourceSettingsState.ACTIVE]

    return sum(budgets)


def get_current_daily_budget_total(states):
    return compute_daily_budget_total(states)


def get_daily_budget_total(ad_group_sources, states, settings):
    data = []

    for ad_group_source in ad_group_sources:
        # get settings
        ad_group_source_settings = [s for s in settings if s.ad_group_source.id == ad_group_source.id]
        obj = ad_group_source_settings[0] if len(ad_group_source_settings) else None

        if obj is None or obj.daily_budget_cc is None:
            # if no settings, get state
            ad_group_source_states = [s for s in states if s.ad_group_source.id == ad_group_source.id]
            obj = ad_group_source_states[0] if len(ad_group_source_states) else None

        data.append(obj)

    return compute_daily_budget_total(data)


def has_aggregate_postclick_permission(user):
    return (user.has_perm('zemauth.aggregate_postclick_acquisition') or
            user.has_perm('zemauth.aggregate_postclick_engagement'))


class AllAccountsSourcesTable(object):
    def __init__(self, user, id_):
        self.user = user
        self.accounts = models.Account.objects.all().filter_by_user(user)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, self.accounts)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, self.accounts)

    def get_sources(self):
        return models.Source.objects.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_sources_states(self):
        return models.AdGroupSourceState.objects.\
            distinct('ad_group_source_id').\
            filter(ad_group_source__in=self.active_ad_group_sources).\
            order_by('ad_group_source_id', '-created_dt')

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
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, [self.account])

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, [self.account])

    def get_sources(self):
        return models.Source.objects.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_sources_states(self):
        return models.AdGroupSourceState.objects.\
            distinct('ad_group_source_id').\
            filter(ad_group_source__in=self.active_ad_group_sources).\
            order_by('ad_group_source_id', '-created_dt')

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
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Campaign, [self.campaign])

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_campaigns(
            start_date, end_date, [self.campaign])

    def get_sources(self):
        return models.Source.objects.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_sources_states(self):
        return models.AdGroupSourceState.objects.\
            distinct('ad_group_source_id').\
            filter(ad_group_source__in=self.active_ad_group_sources).\
            order_by('ad_group_source_id', '-created_dt')

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
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [self.ad_group])

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_ad_groups(
            start_date, end_date, [self.ad_group])

    def get_sources(self):
        return models.Source.objects.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_sources_states(self):
        return models.AdGroupSourceState.objects.\
            distinct('ad_group_source_id').\
            filter(ad_group_source__in=self.active_ad_group_sources).\
            order_by('ad_group_source_id', '-created_dt')

    def get_sources_settings(self):
        return models.AdGroupSourceSettings.objects.\
            distinct('ad_group_source_id').\
            filter(ad_group_source__in=self.active_ad_group_sources).\
            order_by('ad_group_source_id', '-created_dt')

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


class AdGroupSourcesTableUpdates(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_notifications_get')
    def get(self, request, ad_group_id_=None):
        if not request.user.has_perm('zemauth.set_ad_group_source_settings'):
            return exc.ForbiddenError('Not allowed')

        last_change_dt = helpers.parse_datetime(request.GET.get('last_change_dt'))

        ad_group_sources_table = AdGroupSourcesTable(request.user, ad_group_id_)
        ad_group_sources = ad_group_sources_table.active_ad_group_sources

        new_last_change_dt, changed_ad_group_sources = helpers.get_ad_group_sources_last_change_dt(
            ad_group_sources,
            last_change_dt
        )

        notifications = helpers.get_ad_group_sources_notifications(ad_group_sources)

        response = {
            'last_change': new_last_change_dt,
            'in_progress': any(n['in_progress'] for n in notifications.values())
        }

        if new_last_change_dt is not None:
            states = ad_group_sources_table.get_sources_states()
            settings = ad_group_sources_table.get_sources_settings()

            rows = {}
            for ad_group_source in changed_ad_group_sources:
                source_states = [s for s in states if s.ad_group_source.id == ad_group_source.id]
                source_settings = [s for s in settings if s.ad_group_source.id == ad_group_source.id]

                state = source_states[0]
                if len(source_settings):
                    setting = source_settings[0]
                else:
                    # use state if there is no settings for this ad group source
                    setting = state

                updates = {
                    'status_setting': setting.state,
                    'status': state.state,
                    'bid_cpc': setting.cpc_cc,
                    'current_bid_cpc': state.cpc_cc,
                    'daily_budget': setting.daily_budget_cc,
                    'current_daily_budget': state.daily_budget_cc,
                }

                if not notifications.get(ad_group_source.source_id, {}).get('in_progress')\
                        and request.user.has_perm('zemauth.data_status_column'):
                    # only send data_status if there is no updates in progress
                    updates['data_status'] = (
                        setting.state == state.state
                        and setting.cpc_cc == state.cpc_cc
                        and setting.daily_budget_cc == state.daily_budget_cc
                    )

                rows[ad_group_source.source_id] = updates

            response['rows'] = rows

            response['totals'] = {
                'daily_budget': get_daily_budget_total(ad_group_sources, states, settings),
                'current_daily_budget': get_current_daily_budget_total(states)
            }

            response['notifications'] = notifications

            if request.user.has_perm('zemauth.data_status_column'):
                response['data_status_messages'] = helpers.get_ad_group_sources_data_status_messages(
                    ad_group_sources)

        return self.create_api_response(response)


class SourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_get')
    def get(self, request, level_, id_=None):
        user = request.user

        ad_group_level = False
        if level_ == 'all_accounts':
            self.level_sources_table = AllAccountsSourcesTable(user, id_)
        elif level_ == 'accounts':
            self.level_sources_table = AccountSourcesTable(user, id_)
        elif level_ == 'campaigns':
            self.level_sources_table = CampaignSourcesTable(user, id_)
        elif level_ == 'ad_groups':
            ad_group_level = True
            self.level_sources_table = AdGroupSourcesTable(user, id_)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        sources = self.level_sources_table.get_sources()
        sources_states = self.level_sources_table.get_sources_states()
        last_success_actions = self.level_sources_table.get_last_success_actions()
        sources_data, totals_data = self.level_sources_table.get_stats(start_date, end_date)
        is_sync_in_progress = self.level_sources_table.is_sync_in_progress()

        ad_group_sources_settings = None
        if ad_group_level:
            ad_group_sources_settings = self.level_sources_table.get_sources_settings()

        yesterday_cost = {}
        yesterday_total_cost = None
        if user.has_perm('reports.yesterday_spend_view'):
            yesterday_cost, yesterday_total_cost = self.level_sources_table.\
                get_yesterday_cost()

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = False
        if has_aggregate_postclick_permission(user):
            incomplete_postclick_metrics = \
                not self.level_sources_table.has_complete_postclick_metrics(
                    start_date, end_date)

        ad_group_sources = self.level_sources_table.active_ad_group_sources

        response = {
            'rows': self.get_rows(
                id_,
                user,
                sources,
                sources_data,
                sources_states,
                ad_group_sources_settings,
                last_success_actions,
                yesterday_cost,
                order=request.GET.get('order', None),
                ad_group_level=ad_group_level,
            ),
            'totals': self.get_totals(
                ad_group_level,
                user,
                ad_group_sources,
                totals_data,
                sources_states,
                ad_group_sources_settings,
                yesterday_total_cost
            ),
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
            'is_sync_in_progress': is_sync_in_progress,
            'incomplete_postclick_metrics': incomplete_postclick_metrics,
        }

        if ad_group_level and user.has_perm('zemauth.set_ad_group_source_settings'):
            response['last_change'] = helpers.get_ad_group_sources_last_change_dt(ad_group_sources)[0]
            response['notifications'] = helpers.get_ad_group_sources_notifications(ad_group_sources)

            if user.has_perm('zemauth.data_status_column'):
                response['data_status_messages'] = helpers.get_ad_group_sources_data_status_messages(
                    ad_group_sources)

        return self.create_api_response(response)

    def get_totals(self, ad_group_level, user, ad_group_sources, totals_data, sources_states, sources_settings, yesterday_cost):
        result = {
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

        if ad_group_level and user.has_perm('zemauth.set_ad_group_source_settings'):
            result['daily_budget'] = get_daily_budget_total(ad_group_sources, sources_states, sources_settings)
            result['current_daily_budget'] = get_current_daily_budget_total(sources_states)
        else:
            result['daily_budget'] = get_current_daily_budget_total(sources_states)

        return result

    def get_state(self, states):
        if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE for s in states):
            return constants.AdGroupSourceSettingsState.ACTIVE

        return constants.AdGroupSourceSettingsState.INACTIVE

    def get_rows(
            self,
            id_,
            user,
            sources,
            sources_data,
            sources_states,
            ad_group_sources_settings,
            last_actions,
            yesterday_cost,
            order=None,
            ad_group_level=False):
        rows = []
        for source in sources:
            states = [s for s in sources_states if s.ad_group_source.source_id == source.id]

            source_settings = None
            if ad_group_level and ad_group_sources_settings:
                for s in ad_group_sources_settings:
                    if s.ad_group_source.source_id == source.id:
                        source_settings = s
                        break

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

                daily_budget = states[0].daily_budget_cc if len(states) else None
            else:
                daily_budget = get_current_daily_budget_total(states)

            row = {
                'id': str(source.id),
                'name': source.name,
                'daily_budget': daily_budget,
                'status': self.get_state(states),
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

                'goals': source_data.get('goals', {}),

                'maintenance': source.maintenance
            }

            bid_cpc_values = [s.cpc_cc for s in states if s.cpc_cc is not None]

            if ad_group_level:
                row['editable_fields'] = []
                if user.has_perm('zemauth.set_ad_group_source_settings'):
                    if source.can_update_state():
                        row['editable_fields'].append('status_setting')

                    if source.can_update_cpc():
                        row['editable_fields'].append('bid_cpc')

                    if source.can_update_daily_budget():
                        row['editable_fields'].append('daily_budget')

                if user.has_perm('zemauth.set_ad_group_source_settings')\
                and source_settings is not None \
                and source_settings.state is not None:
                    row['status_setting'] = source_settings.state
                else:
                    row['status_setting'] = row['status']

                if user.has_perm('zemauth.set_ad_group_source_settings') \
                and 'bid_cpc' in row['editable_fields'] \
                and source_settings is not None \
                and source_settings.cpc_cc is not None:
                    row['bid_cpc'] = source_settings.cpc_cc
                else:
                    row['bid_cpc'] = bid_cpc_values[0] if len(bid_cpc_values) == 1 else None

                if user.has_perm('zemauth.set_ad_group_source_settings') \
                and 'daily_budget' in row['editable_fields'] \
                and source_settings is not None \
                and source_settings.daily_budget_cc is not None:
                    row['daily_budget'] = source_settings.daily_budget_cc
                else:
                    row['daily_budget'] = states[0].daily_budget_cc if len(states) else None

                if user.has_perm('zemauth.see_current_ad_group_source_state'):
                    row['current_bid_cpc'] = bid_cpc_values[0] if len(bid_cpc_values) == 1 else None
                    row['current_daily_budget'] = states[0].daily_budget_cc if len(states) else None

                if user.has_perms(['zemauth.set_ad_group_source_settings', 'zemauth.data_status_column']):
                    row['data_status'] = (
                        row['current_bid_cpc'] == row['bid_cpc']
                        and row['current_daily_budget'] == row['daily_budget']
                        and row['status'] == row['status_setting'])

            elif len(bid_cpc_values) > 0:
                row['min_bid_cpc'] = float(min(bid_cpc_values))
                row['max_bid_cpc'] = float(max(bid_cpc_values))

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

        accounts = models.Account.objects.all().filter_by_user(user)
        account_ids = set(acc.id for acc in accounts)

        accounts_settings = models.AccountSettings.objects.\
            distinct('account_id').\
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
        totals_data['unspent_budget'] = totals_data['budget'] - (totals_data.get('cost') or 0)

        last_success_actions = actionlog.sync.GlobalSync().get_latest_success_by_account()
        last_success_actions = {aid: val for aid, val in last_success_actions.items() if aid in account_ids}

        last_sync = helpers.get_last_sync(last_success_actions.values())

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
            ) if has_aggregate_postclick_permission(request.user) else False

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
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
            row['unspent_budget'] = row['budget'] - (row.get('cost') or 0)

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

        if ad_group in models.AdGroup.demo_objects.all():
            for i, row in enumerate(rows):
                row['url'] = 'http://www.example.com/{}/{}'.format(ad_group.name, i)

        totals_data = reports.api.filter_by_permissions(
            reports.api.query(start_date, end_date, ad_group=int(ad_group.id)), request.user)

        ad_group_sync = actionlog.sync.AdGroupSync(ad_group)
        last_success_actions = ad_group_sync.get_latest_success_by_child(recompute=False)

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_ad_groups(
                start_date, end_date, [ad_group]
            ) if (request.user.has_perm('zemauth.content_ads_postclick_acquisition') or
                  request.user.has_perm('zemauth.content_ads_postclick_engagement')) else False

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
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
            distinct('ad_group_id').\
            filter(ad_group__campaign=campaign).\
            order_by('ad_group_id', '-created_dt')

        totals_stats = reports.api.filter_by_permissions(
            reports.api.query(
                start_date,
                end_date,
                ad_group=ad_groups
            ),
            request.user
        )

        campaign_sync = actionlog.sync.CampaignSync(campaign)
        last_success_actions = campaign_sync.get_latest_success_by_child(recompute=False)

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date, end_date, [campaign]
            ) if has_aggregate_postclick_permission(request.user) else False

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
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
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
        account = helpers.get_account(user, account_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and request.user.has_perm('zemauth.view_archived_entities')

        campaigns = models.Campaign.objects.all().filter_by_user(user).\
            filter(account=account_id)

        campaigns_settings = models.CampaignSettings.objects.\
            distinct('campaign_id').\
            filter(campaign__in=campaigns).\
            order_by('campaign_id', '-created_dt')

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
        totals_stats['unspent_budget'] = totals_stats['budget'] - (totals_stats.get('cost') or 0)

        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group_id').\
            filter(ad_group__campaign__in=campaigns).\
            order_by('ad_group_id', '-created_dt')

        account_sync = actionlog.sync.AccountSync(account)
        last_success_actions = account_sync.get_latest_success_by_child(recompute=False)

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date, end_date, campaigns
            ) if has_aggregate_postclick_permission(request.user) else False

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
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
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
            row['unspent_budget'] = row['budget'] - (row.get('cost') or 0)

            rows.append(row)

        if order:
            if 'state' in order and has_view_archived_permission:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows
