import collections
import datetime
import pytz
from slugify import slugify
from django.conf import settings
from django.db.models import Q

from dash.views import helpers
from dash import models
from dash import budget
from dash import constants
from dash import api
from dash import stats_helper

import utils.pagination
from utils import exc
from utils.sort_helper import sort_results

import reports.api
import reports.api_helpers
import reports.api_contentads
import reports.api_touchpointconversions
import reports.api_publishers
import reports.constants
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


class AllAccountsSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.accounts = models.Account.objects.all().filter_by_user(user)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, self.accounts)
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources
        self.reports_api = get_reports_api_module(user)

    def has_complete_postclick_metrics(self, start_date, end_date):
        return self.reports_api.has_complete_postclick_metrics_accounts(
            start_date, end_date, self.accounts, self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, user, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            breakdown=['source'],
            account=self.accounts,
            source=self.filtered_sources
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(self.reports_api.query(
            start_date,
            end_date,
            account=self.accounts,
            source=self.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.GlobalSync(
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def get_last_pixel_sync(self):
        return get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False))

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=self.accounts, sources=self.filtered_sources)

    def get_data_status(self, user):
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(self.get_last_pixel_sync())

        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
            last_pixel_sync_message=last_pixel_sync_message,
        )


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
        return get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False, account_id=self.account.id))

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=[self.account], sources=self.filtered_sources)

    def get_data_status(self, user):
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(self.get_last_pixel_sync())

        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
            last_pixel_sync_message=last_pixel_sync_message,
        )


class CampaignSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.campaign = helpers.get_campaign(user, id_)
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
        return get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False, account_id=self.campaign.account_id))

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(campaigns=[self.campaign], sources=self.filtered_sources)

    def get_data_status(self, user):
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(self.get_last_pixel_sync())

        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
            last_pixel_sync_message=last_pixel_sync_message
        )


class AdGroupSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.ad_group = helpers.get_ad_group(user, id_)
        self.ad_group_settings = self.ad_group.get_current_settings()
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
        return get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False, account_id=self.ad_group.campaign.account_id))

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(ad_groups=[self.ad_group], sources=self.filtered_sources)

    def get_data_status(self, user):
        state_messages = None
        if user.has_perm('zemauth.set_ad_group_source_settings'):
            state_messages = helpers.get_ad_group_sources_state_messages(
                self.active_ad_group_sources,
                self.ad_group_settings,
                self.ad_group_sources_settings,
                self.ad_group_sources_states,
            )

        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(self.get_last_pixel_sync())

        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
            state_messages=state_messages,
            last_pixel_sync_message=last_pixel_sync_message
        )


class AdGroupSourcesTableUpdates(object):
    def get(self, user, last_change_dt, filtered_sources, ad_group_id_=None):
        if not user.has_perm('zemauth.set_ad_group_source_settings'):
            raise exc.ForbiddenError('Not allowed')

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
                    'autopilot_state': setting.autopilot_state
                }

            response['rows'] = rows

            response['totals'] = {
                'daily_budget': get_daily_budget_total(ad_group_sources, states, settings),
                'current_daily_budget': get_current_daily_budget_total(states)
            }

            response['notifications'] = notifications

            if user.has_perm('zemauth.data_status_column'):
                response['data_status'] = ad_group_sources_table.get_data_status(user)

        return response


class SourcesTable(object):
    def get(self, user, level_, filtered_sources, start_date, end_date, order, id_=None):
        ad_group_level = False
        kwargs = None
        if level_ == 'all_accounts':
            level_sources_table = AllAccountsSourcesTable(user, id_, filtered_sources)
            kwargs = { 'account': level_sources_table.accounts }
        elif level_ == 'accounts':
            level_sources_table = AccountSourcesTable(user, id_, filtered_sources)
            kwargs = { 'account': level_sources_table.account }
        elif level_ == 'campaigns':
            level_sources_table = CampaignSourcesTable(user, id_, filtered_sources)
            kwargs = { 'campaign': level_sources_table.campaign }
        elif level_ == 'ad_groups':
            ad_group_level = True
            level_sources_table = AdGroupSourcesTable(user, id_, filtered_sources)
            kwargs = { 'ad_group': level_sources_table.ad_group }
        if kwargs:
            e_yesterday_cost, e_yesterday_total_cost = self.get_yesterday_cost(level_sources_table, **kwargs)
            yesterday_cost, yesterday_total_cost = self.get_yesterday_cost(level_sources_table, actual=True, **kwargs)

        sources = level_sources_table.get_sources()
        sources_states = level_sources_table.ad_group_sources_states
        last_success_actions = level_sources_table.get_last_success_actions()
        last_pixel_sync = level_sources_table.get_last_pixel_sync()
        sources_data, totals_data = level_sources_table.get_stats(user, start_date, end_date)
        is_sync_in_progress = level_sources_table.is_sync_in_progress()

        ad_group_sources_settings = None
        if ad_group_level:
            ad_group_sources_settings = level_sources_table.ad_group_sources_settings

        operational_sources = [source.id for source in sources.filter(maintenance=False, deprecated=False)]
        last_success_actions_joined = helpers.join_last_success_with_pixel_sync(user, last_success_actions, last_pixel_sync)
        last_success_actions_operational = [v for k, v in last_success_actions_joined.iteritems() if k in operational_sources]
        last_sync = helpers.get_last_sync(last_success_actions_operational)

        incomplete_postclick_metrics = False
        if has_aggregate_postclick_permission(user):
            incomplete_postclick_metrics = \
                not level_sources_table.has_complete_postclick_metrics(
                    start_date, end_date)

        ad_group_sources = level_sources_table.active_ad_group_sources

        response = {
            'rows': self.get_rows(
                id_,
                level_sources_table,
                user,
                sources,
                ad_group_sources,
                sources_data,
                sources_states,
                ad_group_sources_settings,
                last_success_actions_joined,
                e_yesterday_cost,
                yesterday_cost,
                order=order,
                ad_group_level=ad_group_level,
            ),
            'totals': self.get_totals(
                ad_group_level,
                user,
                ad_group_sources,
                totals_data,
                sources_states,
                ad_group_sources_settings,
                e_yesterday_total_cost,
                yesterday_total_cost
            ),
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_operational),
            'is_sync_in_progress': is_sync_in_progress,
            'incomplete_postclick_metrics': incomplete_postclick_metrics,
        }

        if user.has_perm('zemauth.conversion_reports') and hasattr(level_sources_table, 'conversion_goals'):
            # only on ad group and campaign level
            response['conversion_goals'] = [
                {'id': cg.get_view_key(level_sources_table.conversion_goals), 'name': cg.name}
                for cg in level_sources_table.conversion_goals
            ]

        if user.has_perm('zemauth.data_status_column'):
            response['data_status'] = level_sources_table.get_data_status(user)

        if ad_group_level:
            if user.has_perm('zemauth.set_ad_group_source_settings'):
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
                   ad_group_sources,
                   totals_data,
                   sources_states,
                   sources_settings,
                   e_yesterday_cost,
                   yesterday_cost):
        result = {}
        helpers.copy_stats_to_row(totals_data, result)
        result['yesterday_cost'] = yesterday_cost

        if user.has_perm('zemauth.can_view_effective_costs'):
            result['e_yesterday_cost'] = e_yesterday_cost
        if user.has_perm('zemauth.can_view_effective_costs') and not user.has_perm('zemauth.can_view_actual_costs'):
            del result['yesterday_cost']

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
            order=None,
            ad_group_level=False):
        rows = []

        # map settings for quicker access
        sources_settings_dict = {agss.ad_group_source.source_id: agss for agss in (ad_group_sources_settings or [])}

        allowed_sources = None
        if ad_group_level:
            allowed_sources = {source.id for source in level_sources_table.ad_group.campaign.account.allowed_sources.all()}

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

            last_sync = last_actions.get(source.id)

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
                'yesterday_cost': yesterday_cost.get(source.id),
                'maintenance': source.maintenance,
                'archived': source.deprecated,
            }
            if user.has_perm('zemauth.can_view_effective_costs'):
                row['e_yesterday_cost'] = e_yesterday_cost.get(source.id)
            if user.has_perm('zemauth.can_view_effective_costs') and not user.has_perm('zemauth.can_view_actual_costs'):
                del row['yesterday_cost']

            helpers.copy_stats_to_row(source_data, row)

            bid_cpc_values = [s.cpc_cc for s in states if s.cpc_cc is not None]

            if ad_group_level:
                ad_group_source = None
                for item in ad_group_sources:
                    if item.source.id == source.id:
                        ad_group_source = item
                        break

                row['supply_dash_url'] = ad_group_source.get_supply_dash_url()
                row['supply_dash_disabled_message'] = self._get_supply_dash_disabled_message(ad_group_source)

                ad_group_settings = level_sources_table.ad_group_settings

                row['editable_fields'] = helpers.get_editable_fields(
                    ad_group_source,
                    ad_group_settings,
                    source_settings,
                    user,
                    allowed_sources,
                )

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

                if source_settings is not None:
                    row['autopilot_state'] = source_settings.autopilot_state

            elif len(bid_cpc_values) > 0:
                row['min_bid_cpc'] = float(min(bid_cpc_values))
                row['max_bid_cpc'] = float(max(bid_cpc_values))

            # add conversion fields
            for field, val in source_data.iteritems():
                if field.startswith('G[') and field.endswith('_conversionrate'):
                    row[field] = val

            rows.append(row)

        if order:
            order_list = [order]

            # status setting should also be sorted by autopilot state
            if 'status_setting' in order:
                order_list.append(('-' if order.startswith('-') else '') + 'autopilot_state')

            rows = sort_results(rows, order_list)

        return rows


class AccountsAccountsTable(object):
    def get(self, user, filtered_sources, start_date, end_date, order, page, size, show_archived):
        # Permission check
        if not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        has_view_archived_permission = user.has_perm('zemauth.view_archived_entities')
        show_archived = show_archived == 'true' and\
            user.has_perm('zemauth.view_archived_entities')

        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        account_ids = set(acc.id for acc in accounts)

        accounts_settings = models.AccountSettings.objects\
            .filter(account__in=accounts)\
            .group_current_settings()

        size = max(min(int(size or 5), 4294967295), 1)
        if page:
            page = int(page)

        reports_api = get_reports_api_module(user)
        accounts_data = reports.api_helpers.filter_by_permissions(reports_api.query(
            start_date,
            end_date,
            breakdown=['account'],
            account=accounts,
            source=filtered_sources
        ), user)

        totals_data = reports.api_helpers.filter_by_permissions(reports_api.query(
            start_date,
            end_date,
            account=accounts,
            source=filtered_sources
        ), user)

        all_accounts_budget = budget.GlobalBudget().get_total_by_account()
        account_budget = {aid: all_accounts_budget.get(aid, 0) for aid in account_ids}

        all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()
        account_total_spend = {aid: all_accounts_total_spend.get(aid, 0) for aid in account_ids}

        totals_data['budget'] = sum(account_budget.itervalues())
        totals_data['available_budget'] = totals_data['budget'] - sum(account_total_spend.values())
        totals_data['unspent_budget'] = totals_data['budget'] - (totals_data.get('cost') or 0)

        last_success_actions = actionlog.sync.GlobalSync(sources=filtered_sources).get_latest_success_by_child()
        last_success_actions = {aid: val for aid, val in last_success_actions.items() if aid in account_ids}

        last_pixel_sync = get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False))
        last_success_actions_joined = helpers.join_last_success_with_pixel_sync(user, last_success_actions, last_pixel_sync)

        last_sync_joined = helpers.get_last_sync(last_success_actions_joined.values())

        accounts_status_dict = self.get_per_account_status_dict(accounts, filtered_sources)

        rows = self.get_rows(
            accounts,
            accounts_settings,
            accounts_status_dict,
            accounts_data,
            last_success_actions_joined,
            account_budget,
            account_total_spend,
            has_view_archived_permission,
            show_archived,
            order=order,
        )

        rows, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(rows, page, size)

        incomplete_postclick_metrics = \
            not reports_api.has_complete_postclick_metrics_accounts(
                start_date,
                end_date,
                accounts,
                filtered_sources
            ) if has_aggregate_postclick_permission(user) else False

        response = {
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync_joined).isoformat() if last_sync_joined is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(accounts=accounts, sources=filtered_sources),
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
        }

        if user.has_perm('zemauth.data_status_column'):
            response['data_status'] = self.get_data_status(
                user,
                accounts,
                last_success_actions,
                last_pixel_sync
            )

        return response

    def get_per_account_status_dict(self, accounts, filtered_sources):
        """
        Returns per account running status based on ad group sources state
        settings and ad group settings state.
        """

        ad_groups = models.AdGroup.objects.filter(campaign__account_id__in=accounts)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        """ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')"""

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, [], 'campaign__account_id')

    def get_data_status(self, user, accounts, last_success_actions, last_pixel_sync):
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(last_pixel_sync)

        return helpers.get_data_status(
            accounts,
            helpers.get_last_sync_messages(accounts, last_success_actions),
            last_pixel_sync_message=last_pixel_sync_message
        )

    def get_rows(self, accounts, accounts_settings, accounts_status_dict, accounts_data, last_actions, account_budget,
                 account_total_spend, has_view_archived_permission, show_archived, order=None):
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

            if has_view_archived_permission and not show_archived and archived and\
               not reports.api.row_has_traffic_data(account_data) and\
               not reports.api.row_has_postclick_data(account_data) and\
               not reports.api.row_has_conversion_goal_data(account_data):
                continue

            row['status'] = accounts_status_dict[account.id]

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


class AdGroupAdsTable(object):
    def get(self, user, ad_group_id, filtered_sources, start_date, end_date, order, page, size):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        size = max(min(int(size or 5), 4294967295), 1)

        result = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['article'],
            order=[order],
            ad_group=ad_group.id,
            source=filtered_sources,
        ), user)

        result_pg, current_page, num_pages, count, start_index, end_index = \
            utils.pagination.paginate(result, page, size)

        rows = result_pg

        if ad_group in models.AdGroup.demo_objects.all():
            for i, row in enumerate(rows):
                row['url'] = 'http://www.example.com/{}/{}'.format(slugify(ad_group.name), i)

        totals_data = reports.api_helpers.filter_by_permissions(
            reports.api.query(
                start_date,
                end_date,
                ad_group=int(ad_group.id),
                source=filtered_sources,
            ), user)

        ad_group_sync = actionlog.sync.AdGroupSync(ad_group, sources=filtered_sources)
        last_success_actions = ad_group_sync.get_latest_success_by_child()

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_ad_groups(
                start_date,
                end_date,
                [ad_group],
                filtered_sources,
            ) if (user.has_perm('zemauth.content_ads_postclick_acquisition') or
                  user.has_perm('zemauth.content_ads_postclick_engagement')) else False

        return {
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group], sources=filtered_sources),
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
        }


class AdGroupAdsPlusTableUpdates(object):
    def get(self, user, ad_group_id, filtered_sources, last_change_dt):
        ad_group = helpers.get_ad_group(user, ad_group_id)

        if not ad_group.content_ads_tab_with_cms and not user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        new_last_change_dt = helpers.get_content_ad_last_change_dt(ad_group, filtered_sources, last_change_dt)
        changed_content_ads = helpers.get_changed_content_ads(ad_group, filtered_sources, last_change_dt)

        ad_group_sources_states = models.AdGroupSourceState.objects\
            .filter(
                ad_group_source__ad_group=ad_group,
                ad_group_source__source=filtered_sources,
            )\
            .group_current_states()\
            .select_related('ad_group_source')

        rows = {}
        for content_ad in changed_content_ads:
            content_ad_sources = content_ad.contentadsource_set.filter(source=filtered_sources)

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

        if user.has_perm('zemauth.data_status_column'):
            response_dict['data_status'] = helpers.get_content_ad_data_status(
                ad_group,
                changed_content_ads,
            )

        return response_dict


class AdGroupAdsPlusTable(object):
    def get(self, user, ad_group_id, filtered_sources, start_date, end_date, order, page, size, show_archived):

        ad_group = helpers.get_ad_group(user, ad_group_id)
        if not ad_group.content_ads_tab_with_cms and not user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

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

        has_view_archived_permission = user.has_perm('zemauth.view_archived_entities')
        show_archived = show_archived == 'true' and\
            user.has_perm('zemauth.view_archived_entities')

        rows = self._get_rows(content_ads, stats, ad_group, has_view_archived_permission, show_archived)

        batches = []
        if user.has_perm('zemauth.content_ads_bulk_actions'):
            batch_ids = set([row['batch_id'] for row in rows])
            batches = models.UploadBatch.objects.filter(
                id__in=tuple(batch_ids),
                status=constants.UploadBatchStatus.DONE,
            ).order_by('-created_dt')

        if 'status_setting' in order and user.has_perm('zemauth.view_archived_entities'):
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

        ad_group_sync = actionlog.sync.AdGroupSync(ad_group, sources=filtered_sources)
        last_success_actions = ad_group_sync.get_latest_success_by_child()

        last_pixel_sync = get_conversion_pixels_last_sync(
            models.ConversionPixel.objects.filter(archived=False, account_id=ad_group.campaign.account_id))
        last_success_actions_joined = helpers.join_last_success_with_pixel_sync(user, last_success_actions, last_pixel_sync)

        last_sync = helpers.get_last_sync(last_success_actions_joined.values())

        incomplete_postclick_metrics = \
            not reports.api_contentads.has_complete_postclick_metrics_ad_groups(
                start_date,
                end_date,
                [ad_group],
                filtered_sources,
            ) if (user.has_perm('zemauth.content_ads_postclick_acquisition') or
                  user.has_perm('zemauth.content_ads_postclick_engagement')) else False

        response_dict = {
            'rows': rows,
            'batches': [{'id': batch.id, 'name': batch.name} for batch in batches],
            'totals': self._get_total_row(total_stats),
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
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group], sources=filtered_sources),
            'incomplete_postclick_metrics': incomplete_postclick_metrics,
        }

        if user.has_perm('zemauth.conversion_reports'):
            response_dict['conversion_goals'] = [{'id': cg.get_view_key(conversion_goals), 'name': cg.name}
                                                 for cg in conversion_goals]

        if user.has_perm('zemauth.data_status_column'):
            shown_content_ads = models.ContentAd.objects.filter(id__in=[row['id'] for row in rows])
            response_dict['data_status'] = helpers.get_content_ad_data_status(
                ad_group,
                shown_content_ads,
            )

        return response_dict

    def _get_total_row(self, stats):
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

    def _get_rows(self, content_ads, stats, ad_group, has_view_archived_permission, show_archived):
        stats = {s['content_ad']: s for s in stats}
        rows = []

        is_demo = ad_group in models.AdGroup.demo_objects.all()

        for content_ad in content_ads:
            stat = stats.get(content_ad.id, {})

            archived = content_ad.archived
            if has_view_archived_permission and not show_archived and archived and\
               not reports.api.row_has_traffic_data(stat) and\
               not reports.api.row_has_postclick_data(stat) and\
               not reports.api.row_has_conversion_goal_data(stat):
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
                'image_urls': {
                    'square': content_ad.get_image_url(160, 160),
                    'landscape': content_ad.get_image_url(256, 160)
                },
                'status_setting': content_ad.state,
            }
            helpers.copy_stats_to_row(stat, row)

            if has_view_archived_permission:
                row['archived'] = archived

            rows.append(row)

        return rows

    def _add_submission_status_to_rows(self, user, rows, filtered_sources, ad_group):
        all_content_ad_sources = models.ContentAdSource.objects.filter(
            source=filtered_sources,
            content_ad_id__in=[row['id'] for row in rows]
        ).select_related('content_ad__ad_group').select_related('source')

        ad_group_sources_states = models.AdGroupSourceState.objects\
            .filter(
                ad_group_source__ad_group=ad_group,
                ad_group_source__source=filtered_sources,
            )\
            .group_current_states()\
            .select_related('ad_group_source')

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
        campaign = helpers.get_campaign(user, campaign_id)

        has_view_archived_permission = user.has_perm('zemauth.view_archived_entities')
        show_archived = show_archived == 'true' and\
            user.has_perm('zemauth.view_archived_entities')

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

        campaign_sync = actionlog.sync.CampaignSync(campaign, sources=filtered_sources)
        last_success_actions = campaign_sync.get_latest_success_by_child()

        last_pixel_sync = get_conversion_pixels_last_sync(models.ConversionPixel.objects.filter(archived=False, account_id=campaign.account_id))
        last_success_actions_joined = helpers.join_last_success_with_pixel_sync(user, last_success_actions, last_pixel_sync)

        last_sync = helpers.get_last_sync(last_success_actions_joined.values())

        incomplete_postclick_metrics = \
            not reports_api.has_complete_postclick_metrics_campaigns(
                start_date,
                end_date,
                [campaign],
                filtered_sources
            ) if has_aggregate_postclick_permission(user) else False

        ad_groups_status_dict = self.get_per_ad_group_status_dict(ad_groups, ad_groups_settings, filtered_sources)

        e_yesterday_cost, e_yesterday_total_cost = self.get_yesterday_cost(reports_api, campaign)
        yesterday_cost, yesterday_total_cost = self.get_yesterday_cost(reports_api, campaign, actual=True)

        response = {
            'rows': self.get_rows(
                user,
                ad_groups,
                ad_groups_settings,
                ad_groups_status_dict,
                stats,
                last_success_actions_joined,
                order,
                has_view_archived_permission,
                show_archived,
                e_yesterday_cost,
                yesterday_cost,
            ),
            'totals': self.get_totals(user, totals_stats, e_yesterday_total_cost, yesterday_total_cost),
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=[campaign],
                sources=filtered_sources
            ),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        }

        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = campaign.conversiongoal_set.all()
            response['conversion_goals'] = [{'id': cg.get_view_key(conversion_goals), 'name': cg.name}
                                            for cg in conversion_goals]

        if user.has_perm('zemauth.data_status_column'):
            response['data_status'] = self.get_data_status(
                user,
                ad_groups,
                last_success_actions,
                last_pixel_sync
            )

        return response

    def get_per_ad_group_status_dict(self, ad_groups, ad_groups_settings, filtered_sources):
        """ad_groups_sources_settings = models.AdGroupSourceSettings.objects\
                                           .filter(ad_group_source__ad_group=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')"""

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, [], 'id')

    def get_yesterday_cost(self, reports_api, campaign, actual=False):
        constraints = dict(campaign=campaign)
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
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(last_pixel_sync)

        return helpers.get_data_status(
            ad_groups,
            helpers.get_last_sync_messages(ad_groups, last_success_actions),
            last_pixel_sync_message=last_pixel_sync_message
        )

    def get_rows(self, user, ad_groups, ad_groups_settings, ad_groups_status_dict, stats, last_actions,
                 order, has_view_archived_permission, show_archived, e_yesterday_cost, yesterday_cost):
        rows = []

        # map settings for quicker access
        ad_group_settings_dict = {ags.ad_group_id: ags for ags in ad_groups_settings}

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

            reports_api = get_reports_api_module(user)
            if has_view_archived_permission and not show_archived and archived and\
               not reports_api.row_has_traffic_data(ad_group_data) and\
               not reports_api.row_has_postclick_data(ad_group_data) and\
               not reports.api.row_has_conversion_goal_data(ad_group_data):
                continue

            row['state'] = ad_groups_status_dict[ad_group.id]

            if has_view_archived_permission:
                row['archived'] = archived

            row.update(ad_group_data)

            if user.has_perm('zemauth.can_view_effective_costs'):
                row['e_yesterday_cost'] = e_yesterday_cost.get(ad_group.id)
            if not user.has_perm('zemauth.can_view_effective_costs') or user.has_perm('zemauth.can_view_actual_costs'):
                row['yesterday_cost'] = yesterday_cost.get(ad_group.id)

            last_sync = last_actions.get(ad_group.pk)

            row['last_sync'] = last_sync

            rows.append(row)

        if order:
            if 'state' in order and has_view_archived_permission:
                rows = sort_rows_by_order_and_archived(rows, order)
            else:
                rows = sort_results(rows, [order])

        return rows

    def get_totals(self, user, totals_data, e_yesterday_cost, yesterday_cost):
        if user.has_perm('zemauth.can_view_effective_costs'):
            totals_data['e_yesterday_cost'] = e_yesterday_cost
        if not user.has_perm('zemauth.can_view_effective_costs') or user.has_perm('zemauth.can_view_actual_costs'):
            totals_data['yesterday_cost'] = yesterday_cost

        return totals_data


class AccountCampaignsTable(object):
    def get(self, user, account_id, filtered_sources, start_date, end_date, order, show_archived):
        account = helpers.get_account(user, account_id)

        has_view_archived_permission = user.has_perm('zemauth.view_archived_entities')
        show_archived = show_archived == 'true' and\
            user.has_perm('zemauth.view_archived_entities')

        campaigns = models.Campaign.objects.all().filter_by_user(user).\
            filter(account=account_id).filter_by_sources(filtered_sources)

        campaigns_settings = models.CampaignSettings.objects\
            .filter(campaign__in=campaigns)\
            .group_current_settings()

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

        totals_stats['budget'] = sum(budget.CampaignBudget(campaign).get_total()
                                     for campaign in campaigns)
        total_spend = sum(budget.CampaignBudget(campaign).get_spend()
                          for campaign in campaigns)
        totals_stats['available_budget'] = totals_stats['budget'] - total_spend
        totals_stats['unspent_budget'] = totals_stats['budget'] - (totals_stats.get('cost') or 0)

        account_sync = actionlog.sync.AccountSync(account, sources=filtered_sources)
        last_success_actions = account_sync.get_latest_success_by_child()

        last_pixel_sync = get_conversion_pixels_last_sync(
            models.ConversionPixel.objects.filter(archived=False, account_id=account.id))
        last_success_actions_joined = helpers.join_last_success_with_pixel_sync(
            user, last_success_actions, last_pixel_sync)

        last_sync = helpers.get_last_sync(last_success_actions_joined.values())

        incomplete_postclick_metrics = \
            not reports_api.has_complete_postclick_metrics_campaigns(
                start_date,
                end_date,
                campaigns,
                filtered_sources,
            ) if has_aggregate_postclick_permission(user) else False

        campaign_status_dict = self.get_per_campaign_status_dict(campaigns, filtered_sources)

        response = {
            'rows': self.get_rows(
                user,
                campaigns,
                campaigns_settings,
                campaign_status_dict,
                stats,
                last_success_actions_joined,
                order,
                has_view_archived_permission,
                show_archived
            ),
            'totals': totals_stats,
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_joined.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=campaigns,
                sources=filtered_sources
            ),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        }

        if user.has_perm('zemauth.data_status_column'):
            response['data_status'] = self.get_data_status(
                user,
                campaigns,
                last_success_actions,
                last_pixel_sync
            )

        return response

    def get_per_campaign_status_dict(self, campaigns, filtered_sources):
        """
        Returns per campaign status, based on ad group sources settings and ad group settings.
        """
        ad_groups = models.AdGroup.objects.filter(campaign__in=campaigns)
        ad_groups_settings = models.AdGroupSettings.objects\
                                                   .filter(ad_group__in=ad_groups)\
                                                   .group_current_settings()

        """ad_groups_sources_settings = models.AdGroupSourceSettings\
                                           .objects\
                                           .filter(ad_group_source__ad_group__in=ad_groups)\
                                           .filter_by_sources(filtered_sources)\
                                           .group_current_settings()\
                                           .select_related('ad_group_source')"""

        return helpers.get_ad_group_state_by_sources_running_status(
            ad_groups, ad_groups_settings, [], 'campaign_id')

    def get_data_status(self, user, campaigns, last_success_actions, last_pixel_sync):
        last_pixel_sync_message = None
        if user.has_perm('zemauth.conversion_reports'):
            last_pixel_sync_message = helpers.get_last_pixel_sync_message(last_pixel_sync)

        return helpers.get_data_status(
            campaigns,
            helpers.get_last_sync_messages(campaigns, last_success_actions),
            last_pixel_sync_message=last_pixel_sync_message
        )

    def get_rows(self, user, campaigns, campaigns_settings, campaign_status_dict, stats,
                 last_actions, order, has_view_archived_permission, show_archived):
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
            if has_view_archived_permission and not show_archived and archived and\
               not reports_api.row_has_traffic_data(campaign_stat) and\
               not reports_api.row_has_postclick_data(campaign_stat) and\
               not reports.api.row_has_conversion_goal_data(campaign_stat):
                continue

            row['state'] = campaign_status_dict[campaign.id]

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


class PublishersTable(object):

    MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS = 10

    def get(self, user, level_, filtered_sources, show_blacklisted_publishers, start_date, end_date, order, page, size, id_=None):
        if not user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        adgroup = helpers.get_ad_group(user, id_)
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

        publishers_data, totals_data = self._query_filtered_publishers(
            show_blacklisted_publishers,
            start_date,
            end_date,
            adgroup,
            constraints,
            order
        )

        # since we're not dealing with a QuerySet this kind of pagination is braindead, but we'll polish later
        publishers_data, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(publishers_data, page, size)

        source_cache_by_slug = {
            'outbrain': models.Source.objects.get(tracking_slug=constants.SourceType.OUTBRAIN)
        }

        pub_blacklist_qs = models.PublisherBlacklist.objects.none()
        for publisher_data in publishers_data:
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
        # OB currently has a limit of 10 blocked publishers per marketer
        count_ob_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            account=adgroup.campaign.account,
            source__source_type__type=constants.SourceType.OUTBRAIN
        ).count()

        for publisher_data in publishers_data:
            publisher_exchange = publisher_data['exchange'].lower()
            publisher_domain = publisher_data['domain']
            publisher_source = source_cache_by_slug.get(publisher_exchange) or publisher_exchange

            known_source = source_cache_by_slug.get(publisher_exchange) is not None

            publisher_data['source_id'] = publisher_source.id if known_source else -1

            # there's a separate permission for Outbrain blacklisting which
            # might get removed in the future
            can_blacklist_outbrain_publisher = known_source and publisher_source.source_type.type == constants.SourceType.OUTBRAIN and\
                user.has_perm('zemauth.can_modify_outbrain_account_publisher_blacklist_status') and\
                count_ob_blacklisted_publishers < PublishersTable.MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS

            if publisher_source.can_modify_publisher_blacklist_automatically() and\
                    known_source and\
                    (publisher_source.source_type.type != constants.SourceType.OUTBRAIN or
                     can_blacklist_outbrain_publisher):
                publisher_data['can_blacklist_publisher'] = True
            else:
                publisher_data['can_blacklist_publisher'] = False

            if source_cache_by_slug.get(publisher_exchange) is None:
                continue

            for blacklisted_pub in pub_blacklist_qs:
                globally_blacklisted = publisher_domain == blacklisted_pub.name and\
                    blacklisted_pub.everywhere

                if publisher_domain == blacklisted_pub.name and\
                        publisher_source == blacklisted_pub.source and\
                        (blacklisted_pub.account == adgroup.campaign.account or
                         blacklisted_pub.campaign == adgroup.campaign or
                         blacklisted_pub.ad_group == adgroup) or\
                        globally_blacklisted:
                    if blacklisted_pub.status == constants.PublisherStatus.BLACKLISTED:
                        publisher_data['blacklisted'] = 'Blacklisted'
                    elif blacklisted_pub.status == constants.PublisherStatus.PENDING:
                        publisher_data['blacklisted'] = 'Pending'
                    level = blacklisted_pub.get_blacklist_level()
                    publisher_data['blacklisted_level'] = level
                    publisher_data['blacklisted_level_description'] = constants.PublisherBlacklistLevel.verbose(level)
                    if blacklisted_pub.external_id is not None:
                        publisher_data['external_id'] = blacklisted_pub.external_id

        response = {
            'rows': self.get_rows(
                user,
                map_exchange_to_source_name,
                publishers_data=publishers_data,
            ),
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            },
            'totals': self.get_totals(
                user,
                totals_data,
            ),
            'order': order,
        }
        return response

    def _query_filtered_publishers(self, show_blacklisted_publishers, start_date, end_date, adgroup, constraints, order):
        if not show_blacklisted_publishers or\
                show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ALL:
            publishers_data = reports.api_publishers.query(
                start_date, end_date,
                breakdown_fields=['domain', 'exchange'],
                order_fields=[order],
                constraints=constraints,
            )
            totals_data = reports.api_publishers.query(
                start_date, end_date,
                constraints=constraints,
            )
        elif show_blacklisted_publishers in (
            constants.PublisherBlacklistFilter.SHOW_ACTIVE,
            constants.PublisherBlacklistFilter.SHOW_BLACKLISTED,):

            # fetch blacklisted status from db
            adg_pub_blacklist_qs = models.PublisherBlacklist.objects.filter(
                Q(ad_group=adgroup) |
                Q(campaign=adgroup.campaign) |
                Q(account=adgroup.campaign.account)
            )
            adg_blacklisted_publishers = adg_pub_blacklist_qs.values('name', 'ad_group__id', 'source__tracking_slug')
            adg_blacklisted_publishers = map(lambda entry: {
                'domain': entry['name'],
                'adgroup_id': adgroup.id,
                'exchange': entry['source__tracking_slug'].replace('b1_', ''),
            }, adg_blacklisted_publishers)

            # include global, campaign and account stats if they exist
            global_pub_blacklist_qs = models.PublisherBlacklist.objects.filter(
                everywhere=True
            )
            adg_blacklisted_publishers.extend(map(lambda pub_bl: {
                    'domain': pub_bl.name,
                }, global_pub_blacklist_qs)
            )

            query_func = None
            if show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ACTIVE:
                query_func = reports.api_publishers.query_active_publishers
            else:
                query_func = reports.api_publishers.query_blacklisted_publishers

            publishers_data = query_func(
                start_date, end_date,
                breakdown_fields=['domain', 'exchange'],
                order_fields=[order],
                constraints=constraints,
                blacklist=adg_blacklisted_publishers
            )
            totals_data = query_func(
                start_date, end_date,
                constraints=constraints,
                blacklist=adg_blacklisted_publishers
            )
        return publishers_data, totals_data

    def get_totals(self,
                   user,
                   totals_data):
        result = {
            'cost': totals_data.get('cost', 0),
            'cpc': totals_data.get('cpc', 0),
            'clicks': totals_data.get('clicks', 0),
            'impressions': totals_data.get('impressions', 0),
            'ctr': totals_data.get('ctr', 0),
        }
        if user.has_perm('zemauth.can_view_effective_costs'):
            del result['cost']
            result['e_data_cost'] = totals_data.get('e_data_cost', 0)
            result['e_media_cost'] = totals_data.get('e_media_cost', 0)
            result['billing_cost'] = totals_data.get('billing_cost', 0)
            result['license_fee'] = totals_data.get('license_fee', 0)
        if user.has_perm('zemauth.can_view_actual_costs'):
            result['total_cost'] = totals_data.get('total_cost', 0)
            result['media_cost'] = totals_data.get('media_cost', 0)
            result['data_cost'] = totals_data.get('data_cost', 0)
        return result

    def get_rows(self, user, map_exchange_to_source_name, publishers_data):

        rows = []
        for publisher_data in publishers_data:
            exchange = publisher_data.get('exchange', None)
            source_name = map_exchange_to_source_name.get(exchange, exchange)
            domain = publisher_data.get('domain', None)
            if domain:
                domain_link = "http://" + domain
            else:
                domain_link = ""

            row = {
                'can_blacklist_publisher': publisher_data['can_blacklist_publisher'],
                'domain': domain,
                'domain_link': domain_link,
                'blacklisted': publisher_data['blacklisted'],
                'exchange': source_name,
                'source_id': publisher_data['source_id'],
                'external_id': publisher_data.get('external_id'),

                'cost': publisher_data.get('cost', 0),
                'license_fee': publisher_data.get('license_fee', 0),
                'cpc': publisher_data.get('cpc', 0),
                'clicks': publisher_data.get('clicks', None),
                'impressions': publisher_data.get('impressions', None),
                'ctr': publisher_data.get('ctr', None),
            }

            if user.has_perm('zemauth.can_view_effective_costs'):
                del row['cost']
                row['e_data_cost'] = publisher_data.get('e_data_cost', 0)
                row['e_media_cost'] = publisher_data.get('e_media_cost', 0)
                row['billing_cost'] = publisher_data.get('billing_cost', 0)
            if user.has_perm('zemauth.can_view_actual_costs'):
                row['total_cost'] = publisher_data.get('total_cost', 0)
                row['media_cost'] = publisher_data.get('media_cost', 0)
                row['data_cost'] = publisher_data.get('data_cost', 0)


            if publisher_data.get('blacklisted_level'):
                row['blacklisted_level'] = publisher_data['blacklisted_level']
                row['blacklisted_level_description'] = publisher_data['blacklisted_level_description']

            rows.append(row)

        return rows
