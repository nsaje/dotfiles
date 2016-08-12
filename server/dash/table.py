import datetime
import pytz

from django.conf import settings
from django.db.models import Q

from automation import campaign_stop

from dash.views import helpers
from dash import models
from dash import constants
from dash import bcm_helpers
from dash import stats_helper
from dash import publisher_helpers
from dash import validation_helpers
from dash import campaign_goals

import utils.pagination
from utils import exc
from utils.sort_helper import sort_results

import reports.api
import reports.api_helpers
import reports.api_contentads
import reports.api_touchpointconversions
import reports.api_publishers
import reports.constants
import reports.models
from reports.projections import BudgetProjections
import actionlog.sync


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


def get_reports_api_module(user):
    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        return reports.api_contentads

    return reports.api


def get_conversion_pixels_last_sync(conversion_pixels):
    conversion_pixels = conversion_pixels.extra(select={'last_sync_null': 'last_sync_dt IS NULL'},
                                                order_by=['-last_sync_null', 'last_sync_dt'])
    if len(conversion_pixels):
        return conversion_pixels[0].last_sync_dt

    return datetime.datetime.utcnow()


def _set_goal_meta_on_row(stat, performance, conversion_goals):
    for goal_status, goal_metric, goal_value, goal in performance:
        performance_item = {
            'emoticon': campaign_goals.STATUS_TO_EMOTICON_MAP[goal_status],
            'text': campaign_goals.format_campaign_goal(
                goal.type,
                goal_metric,
                goal.conversion_goal
            )
        }
        if goal_value:
            performance_item['text'] += ' (planned {})'.format(
                campaign_goals.format_value(goal.type, goal_value)
            )

        stat['performance']['list'].append(performance_item)

        colored_column = campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP.get(goal.type)
        if goal.type == constants.CampaignGoalKPI.CPA:
            colored_column = 'avg_cost_per_' + goal.conversion_goal.get_view_key(conversion_goals)
        if not colored_column:
            continue

        if goal_status == constants.CampaignGoalPerformance.SUPERPERFORMING:
            stat['styles'][colored_column] = constants.Emoticon.HAPPY
        elif goal_status == constants.CampaignGoalPerformance.UNDERPERFORMING:
            stat['styles'][colored_column] = constants.Emoticon.SAD


def set_rows_goals_performance(user, stats, start_date, end_date, campaigns):
    if not user.has_perm('zemauth.campaign_goal_performance'):
        return
    campaign_goals_map = {}
    campaign_id_map = {
        c.pk: c for c in campaigns
    }
    all_campaign_goals = campaign_goals.fetch_goals(
        [campaign.pk for campaign in campaigns], end_date
    )
    for goal in all_campaign_goals:
        campaign_goals_map.setdefault(goal.campaign_id, []).append(goal)

    for stat in stats:
        stat['performance'] = {'overall': None, 'list': []}
        stat['styles'] = {}
        if 'campaign' in stat:
            campaign = campaign_id_map[stat['campaign']]
        else:
            campaign = campaigns[0]
        goals = campaign_goals_map.get(campaign.pk)
        if not goals:
            continue
        conversion_goals = campaign.conversiongoal_set.all()
        performance = campaign_goals.get_goals_performance(
            user, {'campaign': campaign}, start_date, end_date,
            goals=goals, stats=stat, conversion_goals=conversion_goals
        )

        if not performance:
            continue

        # If set, first goal is always primary
        primary_goal = performance[0][3].primary and performance[0][0]

        if primary_goal:
            stat['performance']['overall'] = campaign_goals.STATUS_TO_EMOTICON_MAP[
                primary_goal
            ]

        _set_goal_meta_on_row(stat, performance, conversion_goals)


class AllAccountsSourcesTable(object):

    def __init__(self, user, id_, view_filter):
        self.user = user
        self.accounts = models.Account.objects.all()\
            .filter_by_user(user)\
            .filter_by_agencies(view_filter.filtered_agencies)\
            .filter_by_account_types(view_filter.filtered_account_types)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, self.accounts)
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.view_filter = view_filter
        self.reports_api = get_reports_api_module(user)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return self.reports_api.has_complete_postclick_metrics_accounts(
            start_date, end_date, self.accounts, self.view_filter.filtered_sources)

    def get_sources(self):
        return self.view_filter.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, user, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            breakdown=['source'],
            account=self.accounts,
            source=self.view_filter.filtered_sources
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            account=self.accounts,
            source=self.view_filter.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.GlobalSync(
                sources=self.view_filter.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def get_last_pixel_sync(self):
        return get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False))

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(
            accounts=self.accounts,
            sources=self.view_filter.filtered_sources)

    def get_data_status(self, user):
        return helpers.get_data_status(self.get_sources())


class AccountSourcesTable(object):

    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.account = helpers.get_account(user, id_)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, [self.account])
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources
        self.reports_api = get_reports_api_module(user)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return self.reports_api.has_complete_postclick_metrics_accounts(
            start_date, end_date, [self.account], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, user, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            breakdown=['source'],
            account=self.account,
            source=self.filtered_sources
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            account=self.account,
            source=self.filtered_sources
        ), self.user)

        return sources_stats, totals_stats

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.AccountSync(
                self.account,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def get_last_pixel_sync(self):
        return None

    def is_sync_in_progress(self):
        return False

    def get_data_status(self, user):
        return helpers.get_data_status(self.get_sources())


class CampaignSourcesTable(object):

    def __init__(self, user, id_, filtered_sources):
        self.user = user
        helpers.get_campaign(user, id_)
        self.campaign = models.Campaign.objects.filter(id=int(id_)).\
            select_related('account').\
            prefetch_related('adgroup_set').\
            prefetch_related('conversiongoal_set').get()

        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Campaign, [self.campaign])
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources
        self.reports_api = get_reports_api_module(user)
        self.conversion_goals = self.campaign.conversiongoal_set.all()

    def has_complete_postclick_metrics(self, start_date, end_date):
        return self.reports_api.has_complete_postclick_metrics_campaigns(
            start_date, end_date, [self.campaign], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, user, start_date, end_date):
        sources_stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=['source'],
            conversion_goals=self.campaign.conversiongoal_set.all(),
            constraints={'campaign': self.campaign, 'source': self.filtered_sources}
        )

        totals_stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            conversion_goals=self.campaign.conversiongoal_set.all(),
            constraints={'campaign': self.campaign, 'source': self.filtered_sources}
        )

        return sources_stats, totals_stats

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.CampaignSync(
                self.campaign,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def get_last_pixel_sync(self):
        return None

    def is_sync_in_progress(self):
        return False

    def get_data_status(self, user):
        return helpers.get_data_status(self.get_sources())


class AdGroupSourcesTable(object):

    def __init__(self, user, id_, filtered_sources):
        self.user = user
        helpers.get_ad_group(user, id_)
        self.ad_group = models.AdGroup.objects.filter(id=int(id_)).\
            select_related('campaign').\
            prefetch_related('campaign__conversiongoal_set').get()
        self.ad_group_settings = self.ad_group.get_current_settings()
        self.campaign_settings = self.ad_group.campaign.get_current_settings()
        self.source_campaign_stop_check = campaign_stop.can_enable_media_sources(
            self.ad_group,
            self.ad_group.campaign,
            self.campaign_settings,
        )
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [self.ad_group])
        self.ad_group_sources_settings = helpers.get_ad_group_sources_settings(self.active_ad_group_sources)
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources
        self.reports_api = get_reports_api_module(user)
        self.conversion_goals = self.ad_group.campaign.conversiongoal_set.all()

    def has_complete_postclick_metrics(self, start_date, end_date):
        return self.reports_api.has_complete_postclick_metrics_ad_groups(
            start_date, end_date, [self.ad_group], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, user, start_date, end_date):
        sources_stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=['source'],
            conversion_goals=self.ad_group.campaign.conversiongoal_set.all(),
            constraints={'ad_group': self.ad_group, 'source': self.filtered_sources}
        )

        totals_stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            conversion_goals=self.ad_group.campaign.conversiongoal_set.all(),
            constraints={'ad_group': self.ad_group, 'source': self.filtered_sources}
        )

        return sources_stats, totals_stats

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.AdGroupSync(
                self.ad_group,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def get_last_pixel_sync(self):
        return None

    def is_sync_in_progress(self):
        return False

    def get_data_status(self, user):
        return helpers.get_data_status(self.get_sources())


class AdGroupSourcesTableUpdates(object):

    def get(self, user, last_change_dt, filtered_sources, ad_group_id_=None):
        ad_group_sources_table = AdGroupSourcesTable(user, ad_group_id_, filtered_sources)
        ad_group_sources = ad_group_sources_table.active_ad_group_sources

        new_last_change_dt, changed_ad_group_sources = helpers.get_ad_group_sources_last_change_dt(
            ad_group_sources,
            ad_group_sources_table.ad_group_sources_settings,
            ad_group_sources_table.ad_group_sources_states,
            last_change_dt=last_change_dt
        )

        notifications = helpers.get_ad_group_sources_notifications(ad_group_sources,
                                                                   ad_group_sources_table.ad_group_settings,
                                                                   ad_group_sources_table.ad_group_sources_settings,
                                                                   ad_group_sources_table.ad_group_sources_states)

        response = {
            'last_change': new_last_change_dt,
            'in_progress': any(n['in_progress'] for n in notifications.values())
        }

        if new_last_change_dt is not None:
            states = ad_group_sources_table.ad_group_sources_states
            settings = ad_group_sources_table.ad_group_sources_settings

            rows = {}
            for ad_group_source in changed_ad_group_sources:
                source_states = [s for s in states if s.ad_group_source.id == ad_group_source.id]
                source_settings = [s for s in settings if s.ad_group_source.id == ad_group_source.id]

                state = source_states[0] if len(source_states) else None
                setting = source_settings[0] if len(source_settings) else None

                status = state.state if state is not None else None
                status_setting = status
                if ad_group_source.source.can_update_state() and\
                   setting is not None and\
                   setting.state is not None:
                    status_setting = setting.state

                current_daily_budget = state.daily_budget_cc if state is not None else None
                daily_budget = current_daily_budget
                if (ad_group_source.source.can_update_daily_budget_automatic() or
                        ad_group_source.source.can_update_daily_budget_manual()) and\
                        setting is not None and\
                        setting.daily_budget_cc is not None:
                    daily_budget = setting.daily_budget_cc

                current_bid_cpc = state.cpc_cc if state is not None else None
                bid_cpc = current_bid_cpc
                if ad_group_source.source.can_update_cpc() and\
                   setting is not None and\
                   setting.cpc_cc is not None:
                    bid_cpc = setting.cpc_cc

                rows[ad_group_source.source_id] = {
                    'status_setting': status_setting,
                    'status': status,
                    'bid_cpc': bid_cpc,
                    'current_bid_cpc': current_bid_cpc,
                    'daily_budget': daily_budget,
                    'current_daily_budget': current_daily_budget,
                }

            response['rows'] = rows

            response['totals'] = {
                'daily_budget': get_daily_budget_total(ad_group_sources, states, settings),
                'current_daily_budget': get_current_daily_budget_total(states)
            }

            response['notifications'] = notifications

            # if user.has_perm('zemauth.data_status_column'):
            #     response['data_status'] = ad_group_sources_table.get_data_status(user)

        return response


class SourcesTable(object):

    def get(self, user, level_, view_filter, start_date, end_date, order, id_=None):
        ad_group_level = False
        kwargs = None
        filtered_sources = view_filter.filtered_sources
        if level_ == 'all_accounts':
            level_sources_table = AllAccountsSourcesTable(user, id_, view_filter)
            kwargs = {'account': level_sources_table.accounts}
        elif level_ == 'accounts':
            level_sources_table = AccountSourcesTable(user, id_, filtered_sources)
            kwargs = {'account': level_sources_table.account}
        elif level_ == 'campaigns':
            level_sources_table = CampaignSourcesTable(user, id_, filtered_sources)
            kwargs = {'campaign': level_sources_table.campaign}
        elif level_ == 'ad_groups':
            ad_group_level = True
            level_sources_table = AdGroupSourcesTable(user, id_, filtered_sources)
            kwargs = {'ad_group': level_sources_table.ad_group}
        if kwargs:
            e_yesterday_cost, e_yesterday_total_cost = self.get_yesterday_cost(level_sources_table, **kwargs)
            yesterday_cost, yesterday_total_cost = self.get_yesterday_cost(level_sources_table, actual=True, **kwargs)

        sources = level_sources_table.get_sources()
        sources_states = level_sources_table.ad_group_sources_states
        sources_data, totals_data = level_sources_table.get_stats(user, start_date, end_date)

        ad_group_sources_settings = None
        if ad_group_level:
            ad_group_sources_settings = level_sources_table.ad_group_sources_settings

        ad_group_sources = level_sources_table.active_ad_group_sources

        if level_ not in ('all_accounts', 'accounts', ):
            campaign = kwargs.get('campaign') or kwargs['ad_group'].campaign
            set_rows_goals_performance(user, sources_data, start_date, end_date, [campaign])

        rows = self.get_rows(
            id_,
            level_,
            level_sources_table,
            user,
            sources,
            ad_group_sources,
            sources_data,
            sources_states,
            ad_group_sources_settings,
            None,  # last_success_actions_joined,
            e_yesterday_cost,
            yesterday_cost,
            ad_group_level=ad_group_level,
        )

        totals = self.get_totals(
            ad_group_level,
            user,
            level_,
            ad_group_sources,
            totals_data,
            sources_states,
            ad_group_sources_settings,
            e_yesterday_total_cost,
            yesterday_total_cost
        )

        if user.has_perm('zemauth.campaign_goal_optimization') and\
                level_ in ('ad_groups', 'campaigns'):
            if level_ == 'ad_groups':
                campaign = level_sources_table.ad_group.campaign
            elif level_ == 'campaigns':
                campaign = level_sources_table.campaign

            rows = campaign_goals.create_goals(campaign, rows)
            totals = campaign_goals.create_goal_totals(campaign, totals)

        if order:
            rows = sort_results(rows, [order])

        response = {
            'rows': rows,
            'totals': totals,
            'last_sync': None,  # pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': True,  # helpers.is_sync_recent(last_success_actions_operational),
            'is_sync_in_progress': False,  # is_sync_in_progress,
            'incomplete_postclick_metrics': False,  # incomplete_postclick_metrics,
        }

        conversion_goals_lst = []
        if hasattr(level_sources_table, 'conversion_goals'):
            conversion_goals_lst = [
                {'id': cg.get_view_key(level_sources_table.conversion_goals), 'name': cg.name}
                for cg in level_sources_table.conversion_goals
            ]
            # only on ad group and campaign level
            response['conversion_goals'] = conversion_goals_lst

        if ad_group_level:
            response['last_change'] = helpers.get_ad_group_sources_last_change_dt(
                ad_group_sources,
                ad_group_sources_settings,
                sources_states
            )[0]
            response['notifications'] = helpers.get_ad_group_sources_notifications(
                ad_group_sources,
                level_sources_table.ad_group_settings,
                ad_group_sources_settings,
                sources_states
            )
            response['ad_group_autopilot_state'] = level_sources_table.ad_group_settings.autopilot_state

            response['enabling_autopilot_sources_allowed'] = helpers.enabling_autopilot_sources_allowed(
                level_sources_table.ad_group_settings)

        if user.has_perm('zemauth.campaign_goal_optimization') and\
                level_ in ('ad_groups', 'campaigns'):
            if level_ == 'ad_groups':
                campaign = level_sources_table.ad_group.campaign
            elif level_ == 'campaigns':
                campaign = level_sources_table.campaign
            response['campaign_goals'] = campaign_goals.get_campaign_goals(
                campaign, conversion_goals_lst
            )

        return response

    def get_yesterday_cost(self, table, actual=False, **kwargs):
        if actual:
            yesterday_cost = table.reports_api.get_actual_yesterday_cost(kwargs)
        else:
            yesterday_cost = table.reports_api.get_yesterday_cost(kwargs)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())
        return yesterday_cost, yesterday_total_cost

    def get_totals(self,
                   ad_group_level,
                   user,
                   level_,
                   ad_group_sources,
                   totals_data,
                   sources_states,
                   sources_settings,
                   e_yesterday_cost,
                   yesterday_cost):
        result = {}
        helpers.copy_stats_to_row(totals_data, result)

        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            result['e_yesterday_cost'] = e_yesterday_cost

        if user.has_perm('zemauth.can_view_actual_costs'):
            result['yesterday_cost'] = yesterday_cost

        if ad_group_level:
            result['daily_budget'] = get_daily_budget_total(ad_group_sources, sources_states, sources_settings)
            result['current_daily_budget'] = get_current_daily_budget_total(sources_states)
        else:
            result['daily_budget'] = get_current_daily_budget_total(sources_states)

        return result

    def get_state(self, states):
        if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE for s in states):
            return constants.AdGroupSourceSettingsState.ACTIVE

        return constants.AdGroupSourceSettingsState.INACTIVE

    def _get_supply_dash_disabled_message(self, ad_group_source):
        if not ad_group_source.source.has_3rd_party_dashboard():
            return "This media source doesn't have a dashboard of its own. " \
                   "All campaign management is done through Zemanta One dashboard."
        elif ad_group_source.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
            return "Dashboard of this media source is not yet available because the " \
                   "media source is still being set up for this ad group."

        return None

    def get_rows(
            self,
            id_,
            level_,
            level_sources_table,
            user,
            sources,
            ad_group_sources,
            sources_data,
            sources_states,
            ad_group_sources_settings,
            last_actions,
            e_yesterday_cost,
            yesterday_cost,
            ad_group_level=False):
        rows = []

        # map settings for quicker access
        sources_settings_dict = {agss.ad_group_source.source_id: agss for agss in (ad_group_sources_settings or [])}

        allowed_sources = None
        if ad_group_level:
            allowed_sources = {
                source.id for source in level_sources_table.ad_group.campaign.account.allowed_sources.all()}

        for i, source in enumerate(sources):
            states = [s for s in sources_states if s.ad_group_source.source_id == source.id]

            source_settings = None
            if ad_group_level and sources_settings_dict:
                source_settings = sources_settings_dict.get(source.id)

            # get source reports data
            source_data = {}
            for item in sources_data:
                if item['source'] == source.id:
                    source_data = item
                    break

            if source.deprecated and\
               not level_sources_table.reports_api.row_has_traffic_data(source_data) and\
               not level_sources_table.reports_api.row_has_postclick_data(source_data) and\
               not reports.api.row_has_conversion_goal_data(source_data):
                continue  # deprecated sources without data don't have to be shown

            last_sync = last_actions and last_actions.get(source.id)

            if ad_group_level:
                daily_budget = states[0].daily_budget_cc if len(states) else None
            else:
                daily_budget = get_current_daily_budget_total(states)

            row = {
                'id': str(source.id),
                'name': source.name,
                'daily_budget': daily_budget,
                'status': self.get_state(states),
                'last_sync': last_sync,
                'maintenance': source.maintenance,
                'archived': source.deprecated,
            }

            if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['e_yesterday_cost'] = e_yesterday_cost.get(source.id)

            if user.has_perm('zemauth.can_view_actual_costs'):
                row['yesterday_cost'] = yesterday_cost.get(source.id)

            helpers.copy_stats_to_row(source_data, row)

            if ad_group_level:
                bid_cpc_value = states[0].cpc_cc if len(states) == 1 else None
                ad_group_source = None
                for item in ad_group_sources:
                    if item.source.id == source.id:
                        ad_group_source = item
                        break

                row['supply_dash_url'] = ad_group_source.get_supply_dash_url()
                row['supply_dash_disabled_message'] = self._get_supply_dash_disabled_message(ad_group_source)

                ad_group_settings = level_sources_table.ad_group_settings
                campaign_settings = level_sources_table.campaign_settings
                can_enable_source = level_sources_table.source_campaign_stop_check.get(ad_group_source.id, True)

                row['editable_fields'] = helpers.get_editable_fields(
                    level_sources_table.ad_group,
                    ad_group_source,
                    ad_group_settings,
                    source_settings,
                    campaign_settings,
                    user,
                    allowed_sources,
                    can_enable_source,
                )

                if source_settings is not None \
                   and source_settings.state is not None:
                    row['status_setting'] = source_settings.state
                else:
                    row['status_setting'] = row['status']

                if 'bid_cpc' in row['editable_fields'] \
                   and source_settings is not None \
                   and source_settings.cpc_cc is not None:
                    row['bid_cpc'] = source_settings.cpc_cc
                else:
                    row['bid_cpc'] = bid_cpc_value

                if 'daily_budget' in row['editable_fields'] \
                   and source_settings is not None \
                   and source_settings.daily_budget_cc is not None:
                    row['daily_budget'] = source_settings.daily_budget_cc
                else:
                    row['daily_budget'] = states[0].daily_budget_cc if len(states) else None

                row['current_bid_cpc'] = bid_cpc_value
                row['current_daily_budget'] = states[0].daily_budget_cc if len(states) else None
            else:
                bid_cpc_values = [s.cpc_cc for s in states if s.cpc_cc is not None and
                                  s.state == constants.AdGroupSourceSettingsState.ACTIVE]
                row['min_bid_cpc'] = None
                row['max_bid_cpc'] = None
                if len(bid_cpc_values) > 0:
                    row['min_bid_cpc'] = float(min(bid_cpc_values))
                    row['max_bid_cpc'] = float(max(bid_cpc_values))

            # add conversion fields
            for field, val in source_data.iteritems():
                if field.startswith('G[') and field.endswith('_conversionrate'):
                    row[field] = val

            rows.append(row)

        return rows


class AccountsAccountsTable(object):

    def get(self, user, view_filter, start_date, end_date, order, page, size, show_archived):
        # Permission check
        if not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        show_archived = show_archived == 'true'

        has_view_managers_permission = user.has_perm('zemauth.can_see_managers_in_accounts_table')

        accounts = models.Account.objects.all()\
            .filter_by_user(user)\
            .filter_by_sources(view_filter.filtered_sources)\
            .filter_by_agencies(view_filter.filtered_agencies)\
            .filter_by_account_types(view_filter.filtered_account_types)

        accounts_settings = models.AccountSettings.objects\
            .filter(account__in=accounts)\
            .group_current_settings()\
            .select_related('default_account_manager', 'default_sales_representative')

        size = max(min(int(size or 5), 4294967295), 1)
        if page:
            page = int(page)

        reports_api = get_reports_api_module(user)
        accounts_data = reports.api_helpers.filter_by_permissions(reports_api.query(
            start_date,
            end_date,
            breakdown=['account'],
            account=accounts,
            source=view_filter.filtered_sources
        ), user)

        totals_data = reports.api_helpers.filter_by_permissions(reports_api.query(
            start_date,
            end_date,
            account=accounts,
            source=view_filter.filtered_sources
        ), user)

        account_budget, account_total_spend = self.get_budgets(accounts)

        projections = BudgetProjections(
            start_date, end_date, 'account', accounts=accounts,
            campaign_id__in=models.Campaign.objects.filter(account__in=accounts)
        )
        if user.has_perm('zemauth.can_see_projections') and user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            totals_data['pacing'] = projections.total('pacing')
            totals_data['allocated_budgets'] = projections.total('allocated_media_budget')
            totals_data['spend_projection'] = projections.total('media_spend_projection')
            totals_data['license_fee_projection'] = projections.total('license_fee_projection')

        if user.has_perm('zemauth.can_view_flat_fees') and user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            totals_data['flat_fee'] = projections.total('flat_fee')
            totals_data['total_fee'] = projections.total('total_fee')
            if user.has_perm('zemauth.can_see_projections'):
                totals_data['total_fee_projection'] = projections.total('total_fee_projection')

        accounts_status_dict = self.get_per_account_running_status_dict(accounts, view_filter.filtered_sources)

        rows = self.get_rows(
            user,
            accounts,
            accounts_settings,
            accounts_status_dict,
            accounts_data,
            None,  # last_success_actions_joined,
            account_budget,
            projections,
            account_total_spend,
            show_archived,
            has_view_managers_permission,
            order=order,
        )

        rows, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(rows, page, size)

        # incomplete_postclick_metrics = \
        #     not reports_api.has_complete_postclick_metrics_accounts(
        #         start_date,
        #         end_date,
        #         accounts,
        #         view_filter.filtered_sources
        #     ) if has_aggregate_postclick_permission(user) else False

        response = {
            'rows': rows,
            'totals': totals_data,
            'last_sync': None,
            'is_sync_recent': True,  # helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': False,
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size,
            },
            'incomplete_postclick_metrics': False,
        }

        return response

    def get_per_account_running_status_dict(self, accounts, filtered_sources):
        """
        Returns per account running status based on ad group sources state
        settings and ad group settings state.
        """

        ad_groups = models.AdGroup.objects.filter(campaign__account_id__in=accounts)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign__account_id')

    def get_data_status(self, user, accounts, last_success_actions, last_pixel_sync):
        return helpers.get_data_status(accounts)

    def get_budgets(self, accounts):
        account_budget, account_total_spend = bcm_helpers.get_account_media_budget_data(
            set(acc.pk for acc in accounts)
        )
        account_total_spend.update(account_budget)
        account_budget.update(account_total_spend)

        return account_budget, account_total_spend

    def get_rows(self, user, accounts, accounts_settings, accounts_status_dict, accounts_data, last_actions,
                 account_budget, projections, account_total_spend,
                 show_archived, has_view_managers_permission, order=None):
        rows = []

        # map settings for quicker access
        accounts_settings_dict = {acs.account_id: acs for acs in accounts_settings}

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
            account_settings = accounts_settings_dict.get(account.id)
            if account_settings:
                archived = account_settings.archived

            if not show_archived and archived:
                continue

            if has_view_managers_permission:
                row['default_account_manager'] = None
                row['default_sales_representative'] = None
                if account_settings:
                    row['default_account_manager'] = helpers.get_user_full_name_or_email(
                        account_settings.default_account_manager, default_value=None)
                    row['default_sales_representative'] = helpers.get_user_full_name_or_email(
                        account_settings.default_sales_representative, default_value=None)

            if user.has_perm('zemauth.can_see_account_type') and account_settings:
                row['account_type'] = constants.AccountType.get_text(account_settings.account_type)

            row['status'] = accounts_status_dict[account.id]
            row['archived'] = archived

            row['last_sync'] = last_actions and last_actions.get(aid)
            if row['last_sync']:
                row['last_sync'] = row['last_sync']

            if user.has_perm('zemauth.can_view_account_agency_information'):
                row['agency'] = account.agency.name if account.agency else ''

            row.update(account_data)

            if user.has_perm('zemauth.can_see_projections') and\
               user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['pacing'] = projections.row(account.id, 'pacing')
                row['allocated_budgets'] = projections.row(account.id, 'allocated_media_budget')
                row['spend_projection'] = projections.row(account.id, 'media_spend_projection')
                row['license_fee_projection'] = projections.row(account.id, 'license_fee_projection')

            if user.has_perm('zemauth.can_view_flat_fees') and\
               user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['flat_fee'] = projections.row(account.id, 'flat_fee')
                row['total_fee'] = projections.row(account.id, 'total_fee')
                if user.has_perm('zemauth.can_see_projections'):
                    row['total_fee_projection'] = projections.row(account.id, 'total_fee_projection')

            rows.append(row)

        if order:
            if 'status' in order:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows


class AdGroupAdsTableUpdates(object):

    def get(self, user, ad_group_id, filtered_sources, last_change_dt):
        helpers.get_ad_group(user, ad_group_id)
        ad_group = models.AdGroup.objects.filter(id=int(ad_group_id)).\
            select_related('campaign').\
            prefetch_related('campaign__conversiongoal_set').get()

        new_last_change_dt = helpers.get_content_ad_last_change_dt(ad_group, filtered_sources, last_change_dt)
        changed_content_ads = helpers.get_changed_content_ads(ad_group, filtered_sources, last_change_dt)

        ad_group_sources_states = ad_group.get_sources_state()

        rows = {}
        for content_ad in changed_content_ads:
            content_ad_sources = content_ad.contentadsource_set.filter(source__in=filtered_sources)

            submission_status = helpers.get_content_ad_submission_status(
                user,
                ad_group_sources_states,
                content_ad_sources
            )

            rows[str(content_ad.id)] = {
                'status_setting': content_ad.state,
                'submission_status': submission_status
            }

        notifications = helpers.get_content_ad_notifications(ad_group)

        response_dict = {
            'rows': rows,
            'notifications': notifications,
            'last_change': new_last_change_dt,
            'in_progress': any(n['in_progress'] for n in notifications.values())
        }

        return response_dict


class AdGroupAdsTable(object):

    def get(self, user, ad_group_id, filtered_sources, start_date, end_date, order, page, size, show_archived):

        helpers.get_ad_group(user, ad_group_id)
        ad_group = models.AdGroup.objects.filter(id=int(ad_group_id)).\
            select_related('campaign').\
            prefetch_related('campaign__conversiongoal_set').get()

        size = max(min(int(size or 5), 4294967295), 1)

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        content_ads = models.ContentAd.objects.filter(
            ad_group=ad_group).filter_by_sources(filtered_sources).select_related('batch')

        stats = stats_helper.get_content_ad_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=['content_ad'],
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            constraints={'ad_group': ad_group, 'source': filtered_sources}
        )

        show_archived = show_archived == 'true'

        set_rows_goals_performance(user, stats, start_date, end_date, [ad_group.campaign])

        rows = self._get_rows(
            content_ads,
            stats,
            ad_group,
            show_archived,
            user
        )

        batch_ids = set([row['batch_id'] for row in rows])
        batches = models.UploadBatch.objects.filter(
            id__in=tuple(batch_ids),
            status=constants.UploadBatchStatus.DONE,
        ).order_by('-created_dt')

        if 'status_setting' in order:
            rows = sort_rows_by_order_and_archived(rows, order)
        else:
            rows = sort_results(rows, [order])

        page_rows, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(
            rows, page, size)

        rows = self._add_submission_status_to_rows(user, page_rows, filtered_sources, ad_group)

        total_stats = stats_helper.get_content_ad_stats_with_conversions(
            user,
            start_date,
            end_date,
            conversion_goals=conversion_goals,
            ignore_diff_rows=True,
            constraints={'ad_group': ad_group, 'source': filtered_sources}
        )

        total_row = self._get_total_row(user, total_stats)

        if user.has_perm('zemauth.campaign_goal_optimization'):
            campaign = ad_group.campaign
            rows = campaign_goals.create_goals(campaign, rows)
            total_row = campaign_goals.create_goal_totals(campaign, total_row)

        rows = self.sort_rows(rows, order)

        response = {
            'rows': rows,
            'batches': [{'id': batch.id, 'name': batch.name} for batch in batches],
            'totals': total_row,
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            },
            'notifications': helpers.get_content_ad_notifications(ad_group),
            'last_change': helpers.get_content_ad_last_change_dt(ad_group, filtered_sources),
            'last_sync': None,  # pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': True,  # helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': False,  # actionlog.api.is_sync_in_progress([ad_group], sources=filtered_sources),
            'incomplete_postclick_metrics': False,  # incomplete_postclick_metrics,
        }

        conversion_goals_lst = [{'id': cg.get_view_key(conversion_goals), 'name': cg.name}
                                for cg in conversion_goals]
        response['conversion_goals'] = conversion_goals_lst

        if user.has_perm('zemauth.campaign_goal_optimization'):
            campaign = ad_group.campaign
            response['campaign_goals'] = campaign_goals.get_campaign_goals(
                campaign, conversion_goals_lst
            )

        return response

    def sort_rows(self, rows, order):
        if order:
            if 'state' in order:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows

    def _get_total_row(self, user, stats):
        totals = {}
        helpers.copy_stats_to_row(stats, totals)
        return totals

    def _get_url(self, ad_group, content_ad, is_demo):
        if is_demo:
            return 'http://www.example.com/{}/{}'.format(ad_group.name, content_ad.id)

        return content_ad.url

    def _get_redirector_url(self, content_ad, is_demo):
        if is_demo:
            return None

        return settings.R1_BLANK_REDIRECT_URL.format(
            redirect_id=content_ad.redirect_id,
            content_ad_id=content_ad.id
        )

    def _get_rows(self, content_ads, stats, ad_group, show_archived, user):
        stats = {s['content_ad']: s for s in stats}
        rows = []

        is_demo = ad_group in models.AdGroup.demo_objects.all()

        for content_ad in content_ads:
            stat = stats.get(content_ad.id, {})

            archived = content_ad.archived
            if not show_archived and archived:
                continue

            url = self._get_url(ad_group, content_ad, is_demo)
            redirector_url = self._get_redirector_url(content_ad, is_demo)

            row = {
                'id': str(content_ad.id),
                'title': content_ad.title,
                'url': url,
                'redirector_url': redirector_url,
                'batch_name': content_ad.batch.name,
                'batch_id': content_ad.batch.id,
                'upload_time': content_ad.batch.created_dt,
                'display_url': content_ad.display_url,
                'brand_name': content_ad.brand_name,
                'description': content_ad.description,
                'call_to_action': content_ad.call_to_action,
                'label': content_ad.label,
                'image_urls': {
                    'square': content_ad.get_image_url(160, 160),
                    'landscape': content_ad.get_image_url(256, 160)
                },
                'image_hash': content_ad.image_hash,
                'status_setting': content_ad.state,
            }
            helpers.copy_stats_to_row(stat, row)

            row['archived'] = archived

            rows.append(row)

        return rows

    def _add_submission_status_to_rows(self, user, rows, filtered_sources, ad_group):
        all_content_ad_sources = models.ContentAdSource.objects.filter(
            source__in=filtered_sources,
            content_ad_id__in=[row['id'] for row in rows]
        ).select_related('content_ad__ad_group').select_related('source')

        ad_group_sources_states = ad_group.get_sources_state()

        for row in rows:
            content_ad_id = int(row['id'])

            content_ad_sources = [cas for cas in all_content_ad_sources if cas.content_ad_id == content_ad_id]

            submission_status = helpers.get_content_ad_submission_status(
                user,
                ad_group_sources_states,
                content_ad_sources
            )

            row.update({
                'submission_status': submission_status,
                'editable_fields': {
                    'status_setting': {
                        'enabled': True,
                        'message': None,
                    }
                },
            })

        return rows


class CampaignAdGroupsTable(object):

    def get(self, user, campaign_id, filtered_sources, start_date, end_date, order, show_archived):
        helpers.get_campaign(user, campaign_id)
        campaign = models.Campaign.objects.filter(id=int(campaign_id)).\
            select_related('account').\
            prefetch_related('adgroup_set').\
            prefetch_related('conversiongoal_set').get()

        show_archived = show_archived == 'true'

        reports_api = get_reports_api_module(user)

        stats = stats_helper.get_stats_with_conversions(
            user,
            start_date=start_date,
            end_date=end_date,
            breakdown=['ad_group'],
            conversion_goals=campaign.conversiongoal_set.all(),
            constraints={'campaign': campaign, 'source': filtered_sources}
        )

        ad_groups = campaign.adgroup_set.all().filter_by_sources(filtered_sources)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__campaign=campaign)\
                                                   .group_current_settings()

        totals_stats = stats_helper.get_stats_with_conversions(
            user,
            start_date=start_date,
            end_date=end_date,
            conversion_goals=campaign.conversiongoal_set.all(),
            constraints={'ad_group': ad_groups, 'source': filtered_sources}
        )

        ad_groups_status_dict = self.get_per_ad_group_running_status_dict(
            ad_groups, ad_groups_settings, filtered_sources)

        e_yesterday_cost, e_yesterday_total_cost = self.get_yesterday_cost(reports_api, campaign, filtered_sources)
        yesterday_cost, yesterday_total_cost = self.get_yesterday_cost(
            reports_api, campaign, filtered_sources, actual=True)

        set_rows_goals_performance(user, stats, start_date, end_date, [campaign])

        rows = self.get_rows(
            user,
            campaign,
            ad_groups,
            ad_groups_settings,
            ad_groups_status_dict,
            stats,
            None,  # last_success_actions_joined,
            show_archived,
            e_yesterday_cost,
            yesterday_cost,
        )

        totals = self.get_totals(
            user,
            totals_stats,
            e_yesterday_total_cost,
            yesterday_total_cost
        )

        if user.has_perm('zemauth.campaign_goal_optimization'):
            rows = campaign_goals.create_goals(campaign, rows)
            totals = campaign_goals.create_goal_totals(campaign, totals)

        rows = self.sort_rows(rows, order)

        response = {
            'rows': rows,
            'totals': totals,
            'last_sync': None,  # pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': True,  # helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': False,  # actionlog.api.is_sync_in_progress(
            #     campaigns=[campaign],
            #     sources=filtered_sources
            # ),
            'order': order,
            'incomplete_postclick_metrics': False,  # incomplete_postclick_metrics
        }

        conversion_goals = campaign.conversiongoal_set.all()
        conversion_goals_lst = [{'id': cg.get_view_key(conversion_goals), 'name': cg.name}
                                for cg in conversion_goals]
        response['conversion_goals'] = conversion_goals_lst

        # if user.has_perm('zemauth.data_status_column'):
        #     response['data_status'] = self.get_data_status(
        #         user,
        #         ad_groups,
        #         last_success_actions,
        #         last_pixel_sync
        #     )

        if user.has_perm('zemauth.campaign_goal_optimization'):
            response['campaign_goals'] = campaign_goals.get_campaign_goals(
                campaign, conversion_goals_lst
            )

        return response

    def get_per_ad_group_running_status_dict(self, ad_groups, ad_groups_settings, filtered_sources):
        ad_groups_sources_settings = models.AdGroupSourceSettings.objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, ad_groups_sources_settings, 'id')

    def get_yesterday_cost(self, reports_api, campaign, filtered_sources, actual=False):
        constraints = {'campaign': campaign, 'source': filtered_sources}
        breakdown = ['ad_group']

        if actual:
            yesterday_cost = reports_api.get_actual_yesterday_cost(constraints, breakdown)
        else:
            yesterday_cost = reports_api.get_yesterday_cost(constraints, breakdown)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())
        return yesterday_cost, yesterday_total_cost

    def get_data_status(self, user, ad_groups, last_success_actions, last_pixel_sync):
        return helpers.get_data_status(ad_groups)

    def get_rows(self, user, campaign, ad_groups, ad_groups_settings, ad_groups_status_dict, stats, last_actions,
                 show_archived, e_yesterday_cost, yesterday_cost):
        rows = []

        # map settings for quicker access
        ad_group_settings_dict = {ags.ad_group_id: ags for ags in ad_groups_settings}

        campaign_settings = campaign.get_current_settings()
        campaign_stop_check = campaign_stop.can_enable_ad_groups(campaign, campaign_settings)

        for ad_group in ad_groups:
            row = {
                'name': ad_group.name,
                'ad_group': str(ad_group.id),
            }

            ad_group_data = {}
            for stat in stats:
                if ad_group.pk == stat['ad_group']:
                    ad_group_data = stat
                    break

            ad_group_settings = ad_group_settings_dict.get(ad_group.id)
            archived = ad_group_settings.archived if ad_group_settings else False

            if not show_archived and archived:
                continue

            row['state'] = ad_groups_status_dict[ad_group.id]
            row['archived'] = archived

            row.update(ad_group_data)

            if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['e_yesterday_cost'] = e_yesterday_cost.get(ad_group.id)

            if user.has_perm('zemauth.can_view_actual_costs'):
                row['yesterday_cost'] = yesterday_cost.get(ad_group.id)

            last_sync = last_actions and last_actions.get(ad_group.pk)

            row['last_sync'] = last_sync
            row['editable_fields'] = self.get_editable_fields(
                ad_group, campaign, row, campaign_stop_check.get(ad_group.id, True))

            rows.append(row)

        return rows

    def get_totals(self, user, totals_data, e_yesterday_cost, yesterday_cost):
        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            totals_data['e_yesterday_cost'] = e_yesterday_cost

        if user.has_perm('zemauth.can_view_actual_costs'):
            totals_data['yesterday_cost'] = yesterday_cost

        return totals_data

    def sort_rows(self, rows, order):
        if order:
            if 'state' in order:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows

    def get_editable_fields(self, ad_group, campaign, row, can_enable_ad_group):
        state = {
            'enabled': True,
            'message': None
        }
        if not can_enable_ad_group:
            state['enabled'] = False
            state['message'] = 'Please add additional budget to your campaign to make changes.'
        elif row['state'] == constants.AdGroupSettingsState.INACTIVE \
                and not validation_helpers.ad_group_has_available_budget(ad_group):
            state['enabled'] = False
            state['message'] = 'Cannot enable ad group without available budget.'

        return {'state': state}


class AccountCampaignsTable(object):

    def get(self, user, account_id, filtered_sources, start_date, end_date, order, show_archived):
        account = helpers.get_account(user, account_id)

        has_view_managers_permission = user.has_perm('zemauth.can_see_managers_in_campaigns_table')
        show_archived = show_archived == 'true'

        campaigns = models.Campaign.objects.all().filter_by_user(user).\
            filter(account=account_id).filter_by_sources(filtered_sources).\
            prefetch_related('conversiongoal_set')

        campaigns_settings = models.CampaignSettings.objects\
            .filter(campaign__in=campaigns)\
            .group_current_settings()\
            .select_related('campaign_manager')

        reports_api = get_reports_api_module(user)
        stats = reports.api_helpers.filter_by_permissions(reports_api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['campaign'],
            campaign=campaigns,
            source=filtered_sources,
        ), user)

        totals_stats = reports.api_helpers.filter_by_permissions(
            reports_api.query(
                start_date,
                end_date,
                campaign=campaigns,
                source=filtered_sources,
            ), user)

        campaign_budget, campaign_spend = bcm_helpers.get_campaign_media_budget_data(
            c.pk for c in campaigns
        )

        # account_sync = actionlog.sync.AccountSync(account, sources=filtered_sources)
        # last_success_actions = account_sync.get_latest_success_by_child()

        # last_pixel_sync = get_conversion_pixels_last_sync(
        #     models.ConversionPixel.objects.filter(archived=False, account_id=account.id))
        # last_success_actions_joined = helpers.join_last_success_with_pixel_sync(
        #     user, last_success_actions, last_pixel_sync)

        # last_sync = helpers.get_last_sync(last_success_actions_joined.values())

        # incomplete_postclick_metrics = \
        #     not reports_api.has_complete_postclick_metrics_campaigns(
        #         start_date,
        #         end_date,
        #         campaigns,
        #         filtered_sources,
        #     ) if has_aggregate_postclick_permission(user) else False

        campaign_status_dict = self.get_per_campaign_running_status_dict(campaigns, filtered_sources)

        set_rows_goals_performance(user, stats, start_date, end_date, campaigns)

        projections = BudgetProjections(
            start_date, end_date, 'campaign',
            campaign_id__in=campaigns
        )
        if user.has_perm('zemauth.can_see_projections') and user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            totals_stats['pacing'] = projections.total('pacing')
            totals_stats['allocated_budgets'] = projections.total('allocated_media_budget')
            totals_stats['spend_projection'] = projections.total('media_spend_projection')
            totals_stats['license_fee_projection'] = projections.total('license_fee_projection')

        response = {
            'rows': self.get_rows(
                user,
                account,
                campaigns,
                campaigns_settings,
                campaign_status_dict,
                stats,
                None,  # last_success_actions_joined,
                order,
                has_view_managers_permission,
                show_archived,
                campaign_budget,
                campaign_spend,
                projections
            ),
            'totals': totals_stats,
            'last_sync': None,  # pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': True,  # helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': False,  # actionlog.api.is_sync_in_progress(
            #   campaigns=campaigns,
            #   sources=filtered_sources
            # ),
            'order': order,
            'incomplete_postclick_metrics': False,  # incomplete_postclick_metrics
        }

        # if user.has_perm('zemauth.data_status_column'):
        #     response['data_status'] = self.get_data_status(
        #         user,
        #         campaigns,
        #         last_success_actions,
        #         last_pixel_sync
        #     )

        return response

    def get_per_campaign_running_status_dict(self, campaigns, filtered_sources):
        """
        Returns per campaign status, based on ad group sources settings and ad group settings.
        """
        ad_groups = models.AdGroup.objects.filter(campaign__in=campaigns)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, ad_groups_sources_settings, 'campaign_id')

    def get_data_status(self, user, campaigns, last_success_actions, last_pixel_sync):
        return helpers.get_data_status(campaigns)

    def get_rows(self, user, account, campaigns, campaigns_settings, campaign_status_dict, stats,
                 last_actions, order, has_view_managers_permission, show_archived,
                 campaign_budget, campaign_spend, projections):
        rows = []

        # map settings for quicker access
        campaign_settings_dict = {cs.campaign_id: cs for cs in campaigns_settings}

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

            campaign_settings = campaign_settings_dict.get(campaign.id)
            archived = campaign_settings.archived if campaign_settings else False

            reports_api = get_reports_api_module(user)
            if not show_archived and archived:
                continue

            row['state'] = campaign_status_dict[campaign.id]

            if has_view_managers_permission:
                row['campaign_manager'] = None
                if campaign_settings:
                    row['campaign_manager'] = helpers.get_user_full_name_or_email(
                        campaign_settings.campaign_manager, default_value=None)

            row['archived'] = archived

            last_sync = last_actions and last_actions.get(campaign.pk)

            row['last_sync'] = last_sync

            row.update(campaign_stat)

            if user.has_perm('zemauth.can_see_projections') and\
               user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['pacing'] = projections.row(campaign.pk, 'pacing')
                row['allocated_budgets'] = projections.row(campaign.pk, 'allocated_media_budget')
                row['spend_projection'] = projections.row(campaign.pk, 'media_spend_projection')
                row['license_fee_projection'] = projections.row(campaign.pk, 'license_fee_projection')

            rows.append(row)

        if order:
            if 'state' in order:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows


class PublishersTable(object):

    def get(self, user, level_, filtered_sources, show_blacklisted_publishers, start_date, end_date, order, page, size, id_=None):
        if not user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        helpers.get_ad_group(user, id_)
        adgroup = models.AdGroup.objects.filter(id=int(id_)).\
            select_related('campaign').\
            prefetch_related('campaign__conversiongoal_set').get()

        constraints = {'ad_group': adgroup.id}

        size = max(min(int(size or 5), 4294967295), 1)

        # Translation table for "exchange" in b1 to name of the source in One
        # At the same time keys of this array are what we're filtering exchanges to
        map_exchange_to_source_name = {}

        # bidder_slug is unique, so no issues with taking all of the sources
        for s in filtered_sources:
            if s.bidder_slug:
                exchange_name = s.bidder_slug
            else:
                exchange_name = s.name.lower()
            map_exchange_to_source_name[exchange_name] = s.name

        # this is a really bad practice, but used extensively in models.py
        # it should be factored out at the same time as that
        if set(models.Source.objects.all()) != set(filtered_sources):
            constraints['exchange'] = map_exchange_to_source_name.keys()

        conversion_goals = adgroup.campaign.conversiongoal_set.all()
        publishers_data, totals_data = self._query_filtered_publishers(
            user,
            show_blacklisted_publishers,
            start_date,
            end_date,
            adgroup,
            constraints,
            conversion_goals
        )

        set_rows_goals_performance(user, publishers_data, start_date, end_date, [adgroup.campaign])

        if order:
            publishers_data = sort_results(publishers_data, [order])

        # since we're not dealing with a QuerySet this kind of pagination is braindead, but we'll polish later
        publishers_data, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(
            publishers_data, page, size)

        # self._annotate_publishers(publishers_data
        self._annotate_publishers(publishers_data, user, adgroup)
        self._mark_missing_data(publishers_data, totals_data)

        count_ob_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            account_id=adgroup.campaign.account_id,
            source__source_type__type=constants.SourceType.OUTBRAIN
        ).count()

        rows = self.get_rows(
            user,
            map_exchange_to_source_name,
            publishers_data=publishers_data,
        )

        totals = self.get_totals(
            user,
            totals_data,
        )

        if user.has_perm('zemauth.campaign_goal_optimization'):
            campaign = adgroup.campaign
            rows = campaign_goals.create_goals(campaign, rows)
            totals = campaign_goals.create_goal_totals(campaign, totals)

        response = {
            'rows': rows,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            },
            'totals': totals,
            'order': order,
            'ob_blacklisted_count': count_ob_blacklisted_publishers,
        }

        conversion_goals_lst = [
            {'id': cg.get_view_key(conversion_goals), 'name': cg.name}
            for cg in conversion_goals
        ]
        response['conversion_goals'] = conversion_goals_lst

        if user.has_perm('zemauth.campaign_goal_optimization'):
            campaign = adgroup.campaign
            response['campaign_goals'] = campaign_goals.get_campaign_goals(
                campaign, conversion_goals_lst
            )

        return response

    def _construct_pub_bl_queryset(self, publishers_data, adgroup):
        source_cache_by_slug = {
            'outbrain': models.Source.objects.get(tracking_slug=constants.SourceType.OUTBRAIN)
        }

        pub_blacklist_qs = models.PublisherBlacklist.objects.none()
        for publisher_data in publishers_data:
            publisher_data['status'] = constants.PublisherStatus.ENABLED
            publisher_data['blacklisted'] = 'Active'
            domain = publisher_data['domain']
            source_slug = publisher_data['exchange'].lower()

            if source_slug not in source_cache_by_slug:
                source_cache_by_slug[source_slug] =\
                    models.Source.objects.filter(bidder_slug=source_slug).first()

            if source_cache_by_slug[source_slug] is None:
                continue

            pub_blacklist_qs |= models.PublisherBlacklist.objects.filter(
                Q(
                    name=domain,
                    source=source_cache_by_slug[source_slug]
                ) | Q(
                    Q(ad_group=adgroup) |
                    Q(campaign=adgroup.campaign) |
                    Q(account=adgroup.campaign.account)
                )
            )

            pub_blacklist_qs |= models.PublisherBlacklist.objects.filter(
                name=domain,
                everywhere=True
            )
        return pub_blacklist_qs, source_cache_by_slug

    def _mark_missing_data(self, publishers_data, publishers_totals):
        for publisher_data in publishers_data:
            publisher_exchange = (publisher_data['exchange'] or '').lower()

            if publisher_exchange == constants.SourceType.OUTBRAIN:
                # OB does not report back impressions for publishers
                publisher_data['impressions'] = None

    def _annotate_publishers(self, publishers_data, user, adgroup):
        pub_blacklist_qs, source_cache_by_slug = self._construct_pub_bl_queryset(publishers_data, adgroup)

        # OB currently has a limit of 10 blocked publishers per marketer
        count_ob_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            account=adgroup.campaign.account,
            source__source_type__type=constants.SourceType.OUTBRAIN
        ).count()

        for publisher_data in publishers_data:
            publisher_exchange = publisher_data['exchange'].lower()
            publisher_domain = publisher_data['domain']
            publisher_source = source_cache_by_slug.get(publisher_exchange) or publisher_exchange

            publisher_data['can_blacklist_publisher'] =\
                self._can_blacklist_publisher(
                    user,
                    publisher_data,
                    count_ob_blacklisted_publishers,
                    source_cache_by_slug
            )

            if source_cache_by_slug.get(publisher_exchange) is None:
                continue

            for blacklisted_pub in pub_blacklist_qs:
                globally_blacklisted = publisher_domain == blacklisted_pub.name and\
                    blacklisted_pub.everywhere

                pub_source_match = publisher_domain == blacklisted_pub.name and\
                    publisher_source.id == blacklisted_pub.source_id

                blacklisted_on_some_level = (
                    blacklisted_pub.account_id == adgroup.campaign.account_id or
                    blacklisted_pub.campaign_id == adgroup.campaign_id or
                    blacklisted_pub.ad_group_id == adgroup.id
                )

                if pub_source_match and blacklisted_on_some_level or globally_blacklisted:
                    publisher_data['status'] = blacklisted_pub.status
                    if blacklisted_pub.status == constants.PublisherStatus.BLACKLISTED:
                        publisher_data['blacklisted'] = 'Blacklisted'
                    elif blacklisted_pub.status == constants.PublisherStatus.PENDING:
                        publisher_data['blacklisted'] = 'Pending'
                    level = blacklisted_pub.get_blacklist_level()
                    publisher_data['blacklisted_level'] = level
                    publisher_data['blacklisted_level_description'] = constants.PublisherBlacklistLevel.verbose(level)
                    if blacklisted_pub.external_id is not None:
                        publisher_data['external_id'] = blacklisted_pub.external_id

    def _can_blacklist_publisher(self, user, publisher_data, count_ob_blacklisted_publishers, source_cache_by_slug):
        publisher_exchange = publisher_data['exchange'].lower()
        publisher_source = source_cache_by_slug.get(publisher_exchange) or publisher_exchange

        known_source = source_cache_by_slug.get(publisher_exchange) is not None

        publisher_data['source_id'] = publisher_source.id if known_source else -1

        # there's a separate permission for Outbrain blacklisting which
        # might get removed in the future
        can_blacklist_outbrain_publisher = known_source and publisher_source.source_type.type == constants.SourceType.OUTBRAIN and\
            user.has_perm('zemauth.can_modify_outbrain_account_publisher_blacklist_status') and\
            count_ob_blacklisted_publishers < constants.MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS_PER_ACCOUNT

        if known_source and publisher_source.can_modify_publisher_blacklist_automatically() and\
                (publisher_source.source_type.type != constants.SourceType.OUTBRAIN or
                    can_blacklist_outbrain_publisher):
            return True
        else:
            return False

    def _query_filtered_publishers(self, user, show_blacklisted_publishers, start_date, end_date, adgroup, constraints,
                                   conversion_goals):

        if show_blacklisted_publishers in (
                constants.PublisherBlacklistFilter.SHOW_ACTIVE, constants.PublisherBlacklistFilter.SHOW_BLACKLISTED,):
            if show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ACTIVE:
                query_func = reports.api_publishers.query_active_publishers
            else:
                query_func = reports.api_publishers.query_blacklisted_publishers
            adg_blacklisted_publishers = publisher_helpers.prepare_publishers_for_rs_query(adgroup)
        else:
            query_func = reports.api_publishers.query
            adg_blacklisted_publishers = None

        publishers_data = stats_helper.get_publishers_data_and_conversion_goals(
            user,
            query_func,
            start_date,
            end_date,
            constraints,
            conversion_goals,
            publisher_breakdown_fields=['domain', 'exchange'],
            touchpoint_breakdown_fields=['publisher', 'source'],
            show_blacklisted_publishers=show_blacklisted_publishers,
            adg_blacklisted_publishers=adg_blacklisted_publishers,
        )
        totals_data = stats_helper.get_publishers_data_and_conversion_goals(
            user,
            query_func,
            start_date,
            end_date,
            constraints,
            conversion_goals,
            show_blacklisted_publishers=show_blacklisted_publishers,
            adg_blacklisted_publishers=adg_blacklisted_publishers,
        )

        return publishers_data, totals_data[0]

    def get_totals(self,
                   user,
                   totals_data):
        result = {
            'cpc': totals_data.get('cpc', 0),
            'cpm': totals_data.get('cpm', 0),
            'clicks': totals_data.get('clicks', 0),
            'impressions': totals_data.get('impressions', 0),
            'ctr': totals_data.get('ctr', 0),
        }
        if user.has_perm('zemauth.view_pubs_postclick_acquisition'):
            result['visits'] = totals_data.get('visits', None)
            result['click_discrepancy'] = totals_data.get('click_discrepancy', None)
            result['pageviews'] = totals_data.get('pageviews', None)

        result['new_visits'] = totals_data.get('new_visits', None)
        result['percent_new_users'] = totals_data.get('percent_new_users', None)
        result['bounced_visits'] = totals_data.get('bounced_visits', None)
        result['non_bounced_visits'] = totals_data.get('non_bounced_visits', None)
        result['bounce_rate'] = totals_data.get('bounce_rate', None)
        result['pv_per_visit'] = totals_data.get('pv_per_visit', None)
        result['avg_tos'] = totals_data.get('avg_tos', None)
        result['new_users'] = totals_data.get('new_users', None)
        result['unique_users'] = totals_data.get('unique_users', None)
        result['returning_users'] = totals_data.get('returning_users', None)

        result['avg_cost_per_minute'] = totals_data.get('avg_cost_per_minute', None)
        result['avg_cost_per_pageview'] = totals_data.get('avg_cost_per_pageview', None)
        result['avg_cost_per_visit'] = totals_data.get('avg_cost_per_visit', None)
        result['avg_cost_per_non_bounced_visit'] = totals_data.get('avg_cost_per_non_bounced_visit', None)
        result['avg_cost_for_new_visitor'] = totals_data.get('avg_cost_for_new_visitor', None)

        result['billing_cost'] = totals_data.get('billing_cost', 0)
        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            result['e_data_cost'] = totals_data.get('e_data_cost', 0)
            result['e_media_cost'] = totals_data.get('e_media_cost', 0)
            result['license_fee'] = totals_data.get('license_fee', 0)

        if user.has_perm('zemauth.can_view_agency_margin'):
            result['margin'] = totals_data.get('margin', 0)
            result['agency_total'] = totals_data.get('agency_total', 0)

        if user.has_perm('zemauth.can_view_actual_costs'):
            result['media_cost'] = totals_data.get('media_cost', 0)
            result['data_cost'] = totals_data.get('data_cost', 0)

        for key in [k for k in totals_data.keys() if k.startswith('conversion_goal_')]:
            result[key] = totals_data[key]

        return result

    def get_rows(self, user, map_exchange_to_source_name, publishers_data):
        rows = []
        for publisher_data in publishers_data:
            exchange = publisher_data.get('exchange', None)
            source_name = map_exchange_to_source_name.get(exchange, exchange)
            domain = publisher_data.get('domain', None)

            if publisher_helpers.is_publisher_domain(domain):
                domain_link = "http://" + domain
            else:
                domain_link = ""

            row = {
                'can_blacklist_publisher': publisher_data['can_blacklist_publisher'],
                'domain': domain,
                'domain_link': domain_link,
                'status': publisher_data['status'],
                'blacklisted': publisher_data['blacklisted'],
                'exchange': source_name,
                'source_id': publisher_data['source_id'],
                'external_id': publisher_data.get('external_id'),

                'cpc': publisher_data.get('cpc', 0),
                'clicks': publisher_data.get('clicks', None),
                'impressions': publisher_data.get('impressions', None),
                'ctr': publisher_data.get('ctr', None),
                'cpm': publisher_data.get('cpm', None)
            }

            if user.has_perm('zemauth.view_pubs_postclick_acquisition'):
                row['visits'] = publisher_data.get('visits', None)
                row['click_discrepancy'] = publisher_data.get('click_discrepancy', None)
                row['pageviews'] = publisher_data.get('pageviews', None)

            row['new_visits'] = publisher_data.get('new_visits', None)
            row['percent_new_users'] = publisher_data.get('percent_new_users', None)
            row['bounced_visits'] = publisher_data.get('bounced_visits', None)
            row['non_bounced_visits'] = publisher_data.get('non_bounced_visits', None)
            row['bounce_rate'] = publisher_data.get('bounce_rate', None)
            row['pv_per_visit'] = publisher_data.get('pv_per_visit', None)
            row['avg_tos'] = publisher_data.get('avg_tos', None)
            row['new_users'] = publisher_data.get('new_users', None)
            row['unique_users'] = publisher_data.get('unique_users', None)
            row['returning_users'] = publisher_data.get('returning_users', None)

            row['avg_cost_per_minute'] = publisher_data.get('avg_cost_per_minute', None)
            row['avg_cost_per_pageview'] = publisher_data.get('avg_cost_per_pageview', None)
            row['avg_cost_per_visit'] = publisher_data.get('avg_cost_per_visit', None)
            row['avg_cost_per_non_bounced_visit'] = publisher_data.get('avg_cost_per_non_bounced_visit', None)
            row['avg_cost_for_new_visitor'] = publisher_data.get('avg_cost_for_new_visitor', None)

            row['billing_cost'] = publisher_data.get('billing_cost', 0)
            if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
                row['e_data_cost'] = publisher_data.get('e_data_cost', 0)
                row['e_media_cost'] = publisher_data.get('e_media_cost', 0)
                row['license_fee'] = publisher_data.get('license_fee', 0)

            if user.has_perm('zemauth.can_view_agency_margin'):
                row['margin'] = publisher_data.get('margin', 0)
                row['agency_total'] = publisher_data.get('agency_total', 0)

            if user.has_perm('zemauth.can_view_actual_costs'):
                row['media_cost'] = publisher_data.get('media_cost', 0)
                row['data_cost'] = publisher_data.get('data_cost', 0)

            for key in [k for k in publisher_data.keys() if k.startswith('conversion_goal_')]:
                row[key] = publisher_data[key]
                if (source_name or '').lower() == constants.SourceType.OUTBRAIN:
                    # We have no conversion data for OB
                    row[key] = None

            if 'performance' in publisher_data:
                row['performance'] = publisher_data['performance']
                row['styles'] = publisher_data.get('styles')

            if publisher_data.get('blacklisted_level'):
                row['blacklisted_level'] = publisher_data['blacklisted_level']
                row['blacklisted_level_description'] = publisher_data['blacklisted_level_description']

            rows.append(row)

        return rows
