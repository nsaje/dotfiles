import datetime

import pytz
from slugify import slugify
from django.core import urlresolvers
from django.conf import settings
import newrelic.agent

from dash.views import helpers
from dash import models
from dash import budget
from dash import constants
from dash import api

import utils.pagination
from utils import api_common
from utils import statsd_helper
from utils import exc
from utils.sort_helper import sort_results

import reports.api
import reports.api_helpers
import reports.api_contentads
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


class AllAccountsSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.accounts = models.Account.objects.all().filter_by_user(user)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, self.accounts)
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, self.accounts, self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            account=self.accounts,
            source=self.filtered_sources
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=self.accounts,
            source=self.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(account=self.accounts)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.GlobalSync(
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=self.accounts, sources=self.filtered_sources)

    def get_data_status(self):
        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
        )


class AccountSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.account = helpers.get_account(user, id_)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Account, [self.account])
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_accounts(
            start_date, end_date, [self.account], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            account=self.account,
            source=self.filtered_sources
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=self.account,
            source=self.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(account=self.account)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.AccountSync(
                self.account,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(accounts=[self.account], sources=self.filtered_sources)

    def get_data_status(self):
        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
        )


class CampaignSourcesTable(object):
    def __init__(self, user, id_, filtered_sources):
        self.user = user
        self.campaign = helpers.get_campaign(user, id_)
        self.active_ad_group_sources = helpers.get_active_ad_group_sources(models.Campaign, [self.campaign])
        self.ad_group_sources_states = helpers.get_ad_group_sources_states(self.active_ad_group_sources)
        self.filtered_sources = filtered_sources

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_campaigns(
            start_date, end_date, [self.campaign], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            campaign=self.campaign,
            source=self.filtered_sources,
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            campaign=self.campaign,
            source=self.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(campaign=self.campaign)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.CampaignSync(
                self.campaign,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(campaigns=[self.campaign], sources=self.filtered_sources)

    def get_data_status(self):
        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
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

    def has_complete_postclick_metrics(self, start_date, end_date):
        return reports.api.has_complete_postclick_metrics_ad_groups(
            start_date, end_date, [self.ad_group], self.filtered_sources)

    def get_sources(self):
        return self.filtered_sources.filter(adgroupsource__in=self.active_ad_group_sources).distinct('id')

    def get_stats(self, start_date, end_date):
        sources_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['source'],
            ad_group=self.ad_group,
            source=self.filtered_sources,
        ), self.user)

        totals_stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ad_group=self.ad_group,
            source=self.filtered_sources,
        ), self.user)

        return sources_stats, totals_stats

    def get_yesterday_cost(self):
        yesterday_cost = reports.api.get_yesterday_cost(ad_group=self.ad_group)
        yesterday_total_cost = None
        if yesterday_cost:
            yesterday_total_cost = sum(yesterday_cost.values())

        return yesterday_cost, yesterday_total_cost

    def get_last_success_actions(self):
        if not hasattr(self, '_last_success_actions'):
            self._last_success_actions = actionlog.sync.AdGroupSync(
                self.ad_group,
                sources=self.filtered_sources
            ).get_latest_source_success()
        return self._last_success_actions

    def is_sync_in_progress(self):
        return actionlog.api.is_sync_in_progress(ad_groups=[self.ad_group], sources=self.filtered_sources)

    def get_data_status(self, include_state_messages=False):
        state_messages = None
        if include_state_messages:
            state_messages = helpers.get_ad_group_sources_state_messages(
                self.active_ad_group_sources,
                self.ad_group_settings,
                self.ad_group_sources_settings,
                self.ad_group_sources_states,
            )

        return helpers.get_data_status(
            self.get_sources(),
            helpers.get_last_sync_messages(self.get_sources(), self.get_last_success_actions()),
            state_messages
        )


class AdGroupSourcesTableUpdates(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_notifications_get')
    def get(self, request, ad_group_id_=None):
        if not request.user.has_perm('zemauth.set_ad_group_source_settings'):
            return exc.ForbiddenError('Not allowed')

        last_change_dt = helpers.parse_datetime(request.GET.get('last_change_dt'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        ad_group_sources_table = AdGroupSourcesTable(request.user, ad_group_id_, filtered_sources)
        ad_group_sources = ad_group_sources_table.active_ad_group_sources
        sources = ad_group_sources_table.get_sources()
        last_success_actions = ad_group_sources_table.get_last_success_actions()

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

            if request.user.has_perm('zemauth.data_status_column'):
                response['data_status'] = helpers.get_data_status(
                    sources,
                    helpers.get_last_sync_messages(sources, last_success_actions),
                    helpers.get_ad_group_sources_state_messages(ad_group_sources,
                                                                ad_group_sources_table.ad_group_settings,
                                                                ad_group_sources_table.ad_group_sources_settings,
                                                                ad_group_sources_table.ad_group_sources_states)
                )

        return self.create_api_response(response)


class SourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_get')
    @newrelic.agent.function_trace()
    def get(self, request, level_, id_=None):
        newrelic.agent.set_transaction_name('dash.views.table:SourcesTable#%s' % (level_))

        user = request.user
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        ad_group_level = False
        if level_ == 'all_accounts':
            level_sources_table = AllAccountsSourcesTable(user, id_, filtered_sources)
        elif level_ == 'accounts':
            level_sources_table = AccountSourcesTable(user, id_, filtered_sources)
        elif level_ == 'campaigns':
            level_sources_table = CampaignSourcesTable(user, id_, filtered_sources)
        elif level_ == 'ad_groups':
            ad_group_level = True
            level_sources_table = AdGroupSourcesTable(user, id_, filtered_sources)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        sources = level_sources_table.get_sources()
        sources_states = level_sources_table.ad_group_sources_states
        last_success_actions = level_sources_table.get_last_success_actions()
        sources_data, totals_data = level_sources_table.get_stats(start_date, end_date)
        is_sync_in_progress = level_sources_table.is_sync_in_progress()

        ad_group_sources_settings = None
        if ad_group_level:
            ad_group_sources_settings = level_sources_table.ad_group_sources_settings

        yesterday_cost = {}
        yesterday_total_cost = None
        if user.has_perm('reports.yesterday_spend_view'):
            yesterday_cost, yesterday_total_cost = level_sources_table.\
                get_yesterday_cost()

        operational_sources = [source.id for source in sources.filter(maintenance=False, deprecated=False)]
        last_success_actions_operational = [v for k, v in last_success_actions.iteritems() if k in operational_sources]
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
            'is_sync_recent': helpers.is_sync_recent(last_success_actions_operational),
            'is_sync_in_progress': is_sync_in_progress,
            'incomplete_postclick_metrics': incomplete_postclick_metrics,
        }

        if user.has_perm('zemauth.data_status_column'):
            if ad_group_level:
                response['data_status'] = level_sources_table.get_data_status(
                    include_state_messages=user.has_perm('zemauth.set_ad_group_source_settings') and ad_group_level,
                )
            else:
                response['data_status'] = level_sources_table.get_data_status()

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

        return self.create_api_response(response)

    @newrelic.agent.function_trace()
    def get_totals(self,
                   ad_group_level,
                   user,
                   ad_group_sources,
                   totals_data,
                   sources_states,
                   sources_settings,
                   yesterday_cost):
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

    def _is_end_date_past(self, ad_group_settings):
        end_utc_datetime = ad_group_settings.get_utc_end_datetime()

        if end_utc_datetime is None:  # user will stop adgroup manually
            return False

        # if end date is in the past then we can't edit cpc and budget
        return end_utc_datetime < datetime.datetime.utcnow()

    def _get_editable_fields(self, ad_group_source, ad_group_settings, ad_group_source_settings, user):
        editable_fields = {}

        if not user.has_perm('zemauth.set_ad_group_source_settings'):
            return editable_fields

        editable_fields['status_setting'] = self._get_editable_fields_status_setting(ad_group_source, ad_group_settings,
                                                                                     ad_group_source_settings)
        editable_fields['bid_cpc'] = self._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)
        editable_fields['daily_budget'] = self._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)

        return editable_fields

    def _get_editable_fields_bid_cpc(self, ad_group_source, ad_group_settings):
        enabled = True
        message = None

        if not ad_group_source.source.can_update_cpc() or self._is_end_date_past(ad_group_settings):
            enabled = False
            message = self._get_bid_cpc_daily_budget_disabled_message(ad_group_source, ad_group_settings)

        return {
            'enabled': enabled,
            'message': message
        }

    def _get_editable_fields_daily_budget(self, ad_group_source, ad_group_settings):
        enabled = True
        message = None

        if not ad_group_source.source.can_update_daily_budget_automatic() and\
           not ad_group_source.source.can_update_daily_budget_manual() or\
           self._is_end_date_past(ad_group_settings):
            enabled = False
            message = self._get_bid_cpc_daily_budget_disabled_message(ad_group_source, ad_group_settings)

        return {
            'enabled': enabled,
            'message': message
        }

    def _get_editable_fields_status_setting(self, ad_group_source, ad_group_settings, ad_group_source_settings):
        message = None

        if not ad_group_source.source.can_update_state() or (
           ad_group_source.ad_group.content_ads_tab_with_cms and not ad_group_source.can_manage_content_ads):
            message = self._get_status_setting_disabled_message(ad_group_source)
        elif ad_group_source_settings is not None and\
                ad_group_source_settings.state == constants.AdGroupSourceSettingsState.INACTIVE:
            message = self._get_status_setting_disabled_message_for_target_regions(
                ad_group_source, ad_group_settings, ad_group_source_settings)

        return {
            'enabled': message is None,
            'message': message
        }

    def _get_status_setting_disabled_message(self, ad_group_source):
        if ad_group_source.source.maintenance:
            return 'This source is currently in maintenance mode.'

        if ad_group_source.ad_group.content_ads_tab_with_cms and not ad_group_source.can_manage_content_ads:
            return 'Please contact support to enable this source.'

        return 'This source must be managed manually.'

    def _get_status_setting_disabled_message_for_target_regions(self, ad_group_source, ad_group_settings,
                                                                ad_group_source_settings):

        source = ad_group_source.source
        if not source.source_type.supports_dma_targeting() and ad_group_settings.targets_dma():
            return 'This source can not be enabled because it does not support DMA targeting.'
        else:
            targets_countries = ad_group_settings.targets_countries()
            targets_dma = ad_group_settings.targets_dma()

            activation_settings = models.AdGroupSourceSettings.objects.filter(
                ad_group_source=ad_group_source, state=constants.AdGroupSourceSettingsState.ACTIVE)

            # disable when waiting for manual actions for target_regions after campaign creation
            # message this only when the source is about to be enabled for the first time
            if api.can_modify_selected_target_regions_manually(source, targets_countries, targets_dma) and\
               actionlog.api.is_waiting_for_manual_set_target_regions_action(ad_group_source) and\
               not activation_settings.exists():

                message = ('This source needs to set {} targeting manually,'
                           'please contact support to enable this source.')

                return message.format('DMA' if source.can_modify_dma_targeting_manual() else 'country')

        return None

    def _get_bid_cpc_daily_budget_disabled_message(self, ad_group_source, ad_group_settings):
        if ad_group_source.source.maintenance:
            return 'This value cannot be edited because the media source is currently in maintenance.'

        if self._is_end_date_past(ad_group_settings):
            return 'The ad group has end date set in the past. No modifications to media source parameters are possible.'

        return 'This media source doesn\'t support setting this value through the dashboard.'

    def _get_supply_dash_disabled_message(self, ad_group_source):
        if not ad_group_source.source.has_3rd_party_dashboard():
            return "This media source doesn't have a dashboard of its own. " \
                   "All campaign management is done through Zemanta One dashboard."
        elif ad_group_source.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
            return "Dashboard of this media source is not yet available because the " \
                   "media source is still being set up for this ad group."

        return None

    def _get_supply_dash_url(self, ad_group_source):
        if not ad_group_source.source.has_3rd_party_dashboard() or\
               ad_group_source.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
            return None

        return '{}?ad_group_id={}&source_id={}'.format(
            urlresolvers.reverse('dash.views.views.supply_dash_redirect'),
            ad_group_source.ad_group.id,
            ad_group_source.source.id
        )

    @newrelic.agent.function_trace()
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
            yesterday_cost,
            order=None,
            ad_group_level=False):
        rows = []
        for i, source in enumerate(sources):
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

            if source.deprecated and not reports.api.row_has_traffic_data(source_data) and not reports.api.row_has_postclick_data(source_data):
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

                'goals': source_data.get('goals', {}),

                'maintenance': source.maintenance,
                'archived': source.deprecated,
            }

            bid_cpc_values = [s.cpc_cc for s in states if s.cpc_cc is not None]

            if ad_group_level:
                ad_group_source = None
                for item in ad_group_sources:
                    if item.source.id == source.id:
                        ad_group_source = item
                        break

                row['supply_dash_url'] = self._get_supply_dash_url(ad_group_source)
                row['supply_dash_disabled_message'] = self._get_supply_dash_disabled_message(ad_group_source)

                ad_group_settings = level_sources_table.ad_group_settings

                row['editable_fields'] = self._get_editable_fields(ad_group_source, ad_group_settings,
                                                                   source_settings, user)

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

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        page = request.GET.get('page')
        size = request.GET.get('size')
        order = request.GET.get('order')

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')

        user = request.user

        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        account_ids = set(acc.id for acc in accounts)

        accounts_settings = models.AccountSettings.objects.\
            distinct('account_id').\
            filter(account__in=accounts).\
            order_by('account_id', '-created_dt')

        size = max(min(int(size or 5), 4294967295), 1)
        if page:
            page = int(page)

        accounts_data = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            ['account'],
            account=accounts,
            source=filtered_sources,
        ), request.user)

        totals_data = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date,
            end_date,
            account=accounts,
            source=filtered_sources,
        ), request.user)

        all_accounts_budget = budget.GlobalBudget().get_total_by_account()
        account_budget = {aid: all_accounts_budget.get(aid, 0) for aid in account_ids}

        all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()
        account_total_spend = {aid: all_accounts_total_spend.get(aid, 0) for aid in account_ids}

        totals_data['budget'] = sum(account_budget.itervalues())
        totals_data['available_budget'] = totals_data['budget'] - sum(account_total_spend.values())
        totals_data['unspent_budget'] = totals_data['budget'] - (totals_data.get('cost') or 0)

        last_success_actions = actionlog.sync.GlobalSync(sources=filtered_sources).get_latest_success_by_child()
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
                start_date,
                end_date,
                accounts,
                filtered_sources
            ) if has_aggregate_postclick_permission(request.user) else False

        response = {
            'rows': rows,
            'totals': totals_data,
            'last_sync': pytz.utc.localize(last_sync).isoformat() if last_sync is not None else None,
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
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
                accounts,
                last_success_actions,
            )

        return self.create_api_response(response)

    def get_data_status(self, accounts, last_success_actions):
        return helpers.get_data_status(
            accounts,
            helpers.get_last_sync_messages(accounts, last_success_actions),
        )

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
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        size = max(min(int(size or 5), 4294967295), 1)

        result = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['article'],
            order=[order],
            ad_group=ad_group.id,
            source=filtered_sources,
        ), request.user)

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
            ), request.user)

        ad_group_sync = actionlog.sync.AdGroupSync(ad_group, sources=filtered_sources)
        last_success_actions = ad_group_sync.get_latest_success_by_child()

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_ad_groups(
                start_date,
                end_date,
                [ad_group],
                filtered_sources,
            ) if (request.user.has_perm('zemauth.content_ads_postclick_acquisition') or
                  request.user.has_perm('zemauth.content_ads_postclick_engagement')) else False

        return self.create_api_response({
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
        })


class AdGroupAdsPlusTableUpdates(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_table_updates_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        user = request.user

        if not ad_group.content_ads_tab_with_cms and not request.user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        last_change_dt = helpers.parse_datetime(request.GET.get('last_change'))

        new_last_change_dt = helpers.get_content_ad_last_change_dt(ad_group, filtered_sources, last_change_dt)
        changed_content_ads = helpers.get_changed_content_ads(ad_group, filtered_sources, last_change_dt)

        ad_group_sources_states = models.AdGroupSourceState.objects.distinct('ad_group_source_id')\
            .filter(
                ad_group_source__ad_group=ad_group,
                ad_group_source__source=filtered_sources,
            )\
            .order_by('ad_group_source_id', '-created_dt')\
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

        return self.create_api_response(response_dict)


class AdGroupAdsPlusTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_table_get')
    def get(self, request, ad_group_id):
        user = request.user
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        if not ad_group.content_ads_tab_with_cms and not request.user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        page = request.GET.get('page')
        order = request.GET.get('order') or 'cost'
        size = request.GET.get('size')
        size = max(min(int(size or 5), 4294967295), 1)

        content_ads = models.ContentAd.objects.filter(
            ad_group=ad_group).filter_by_sources(filtered_sources).select_related('batch')

        stats = reports.api_helpers.filter_by_permissions(reports.api_contentads.query(
            start_date,
            end_date,
            breakdown=['content_ad'],
            ad_group=ad_group,
            source=filtered_sources,
        ), request.user)

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')

        rows = self._get_rows(content_ads, stats, ad_group,
                              has_view_archived_permission,
                              show_archived)

        batches = []
        if request.user.has_perm('zemauth.content_ads_bulk_actions'):
            batch_ids = set([row['batch_id'] for row in rows])
            batches = models.UploadBatch.objects.filter(
                id__in=tuple(batch_ids),
                status=constants.UploadBatchStatus.DONE,
            ).order_by('-created_dt')

        rows = sort_results(rows, [order])
        page_rows, current_page, num_pages, count, start_index, end_index = utils.pagination.paginate(
            rows, page, size)

        rows = self._add_status_to_rows(user, page_rows, filtered_sources, ad_group)

        total_stats = reports.api_helpers.filter_by_permissions(reports.api_contentads.query(
            start_date,
            end_date,
            ad_group=ad_group,
            source=filtered_sources,
        ), request.user)

        ad_group_sync = actionlog.sync.AdGroupSync(ad_group, sources=filtered_sources)
        last_success_actions = ad_group_sync.get_latest_success_by_child()
        last_sync = helpers.get_last_sync(last_success_actions.values())

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
            'is_sync_recent': helpers.is_sync_recent(last_success_actions.values()),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group], sources=filtered_sources),
        }

        if user.has_perm('zemauth.data_status_column'):
            shown_content_ads = models.ContentAd.objects.filter(id__in=[row['id'] for row in rows])
            response_dict['data_status'] = helpers.get_content_ad_data_status(
                ad_group,
                shown_content_ads,
            )

        return self.create_api_response(response_dict)

    @newrelic.agent.function_trace()
    def _get_total_row(self, stats):
        return {
            'impressions': stats['impressions'],
            'clicks': stats['clicks'],
            'cost': stats['cost'],
            'cpc': stats['cpc'],
            'ctr': stats['ctr']
        }

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

    @newrelic.agent.function_trace()
    def _get_rows(self, content_ads, stats, ad_group, has_view_archived_permission, show_archived):
        stats = {s['content_ad']: s for s in stats}
        rows = []

        is_demo = ad_group in models.AdGroup.demo_objects.all()

        for content_ad in content_ads:
            stat = stats.get(content_ad.id, {})

            archived = content_ad.archived
            if has_view_archived_permission and not show_archived and archived and\
               not (reports.api.row_has_traffic_data(stat) or
                    reports.api.row_has_postclick_data(stat)):
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
                'impressions': stat.get('impressions'),
                'clicks': stat.get('clicks'),
                'cost': stat.get('cost'),
                'cpc': stat.get('cpc'),
                'ctr': stat.get('ctr')
            }

            if has_view_archived_permission:
                row['archived'] = archived

            rows.append(row)

        return rows

    @newrelic.agent.function_trace()
    def _add_status_to_rows(self, user, rows, filtered_sources, ad_group):
        all_content_ad_sources = models.ContentAdSource.objects.filter(
            source=filtered_sources,
            content_ad_id__in=[row['id'] for row in rows]
        ).select_related('content_ad__ad_group').select_related('source')

        ad_group_sources_states = models.AdGroupSourceState.objects.distinct('ad_group_source_id')\
            .filter(
                ad_group_source__ad_group=ad_group,
                ad_group_source__source=filtered_sources,
            )\
            .order_by('ad_group_source_id', '-created_dt')\
            .select_related('ad_group_source')

        for row in rows:
            content_ad_id = int(row['id'])

            content_ad_sources = [cas for cas in all_content_ad_sources if cas.content_ad_id == content_ad_id]
            if content_ad_sources:
                content_ad = content_ad_sources[0].content_ad
            else:
                content_ad = models.ContentAd.objects.get(id=content_ad_id)

            submission_status = helpers.get_content_ad_submission_status(
                user,
                ad_group_sources_states,
                content_ad_sources
            )

            row.update({
                'submission_status': submission_status,
                'status_setting': content_ad.state,
                'editable_fields': {
                    'status_setting': {
                        'enabled': True,
                        'message': None,
                    }
                },
            })

        return rows


class CampaignAdGroupsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_ad_groups_table_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-cost'
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')

        stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['ad_group'],
            order=[order],
            campaign=campaign,
            source=filtered_sources,
        ), request.user)

        ad_groups = campaign.adgroup_set.all().filter_by_sources(filtered_sources)
        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group_id').\
            filter(ad_group__campaign=campaign).\
            order_by('ad_group_id', '-created_dt')

        totals_stats = reports.api_helpers.filter_by_permissions(
            reports.api.query(
                start_date,
                end_date,
                ad_group=ad_groups,
                source=filtered_sources,
            ),
            request.user
        )

        campaign_sync = actionlog.sync.CampaignSync(campaign, sources=filtered_sources)
        last_success_actions = campaign_sync.get_latest_success_by_child()

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date,
                end_date,
                [campaign],
                filtered_sources
            ) if has_aggregate_postclick_permission(request.user) else False

        response = {
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
                campaigns=[campaign],
                sources=filtered_sources
            ),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        }

        if request.user.has_perm('zemauth.data_status_column'):
            response['data_status'] = self.get_data_status(
                ad_groups,
                last_success_actions,
            )

        return self.create_api_response(response)

    def get_data_status(self, ad_groups, last_success_actions):
        return helpers.get_data_status(
            ad_groups,
            helpers.get_last_sync_messages(ad_groups, last_success_actions),
        )

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

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        has_view_archived_permission = request.user.has_perm('zemauth.view_archived_entities')
        show_archived = request.GET.get('show_archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')

        campaigns = models.Campaign.objects.all().filter_by_user(user).\
            filter(account=account_id).filter_by_sources(filtered_sources)

        campaigns_settings = models.CampaignSettings.objects.\
            distinct('campaign_id').\
            filter(campaign__in=campaigns).\
            order_by('campaign_id', '-created_dt')

        stats = reports.api_helpers.filter_by_permissions(reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['campaign'],
            order=[order],
            campaign=campaigns,
            source=filtered_sources,
        ), request.user)

        totals_stats = reports.api_helpers.filter_by_permissions(
            reports.api.query(
                start_date,
                end_date,
                campaign=campaigns,
                source=filtered_sources,
            ), request.user)

        totals_stats['budget'] = sum(budget.CampaignBudget(campaign).get_total()
                                     for campaign in campaigns)
        total_spend = sum(budget.CampaignBudget(campaign).get_spend()
                          for campaign in campaigns)
        totals_stats['available_budget'] = totals_stats['budget'] - total_spend
        totals_stats['unspent_budget'] = totals_stats['budget'] - (totals_stats.get('cost') or 0)

        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group_id').\
            filter(ad_group__campaign__in=campaigns).\
            order_by('ad_group_id', '-created_dt')

        account_sync = actionlog.sync.AccountSync(account, sources=filtered_sources)
        last_success_actions = account_sync.get_latest_success_by_child()

        last_sync = helpers.get_last_sync(last_success_actions.values())

        incomplete_postclick_metrics = \
            not reports.api.has_complete_postclick_metrics_campaigns(
                start_date,
                end_date,
                campaigns,
                filtered_sources,
            ) if has_aggregate_postclick_permission(request.user) else False

        response = {
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
                campaigns=campaigns,
                sources=filtered_sources
            ),
            'order': order,
            'incomplete_postclick_metrics': incomplete_postclick_metrics
        }

        if user.has_perm('zemauth.data_status_column'):
            response['data_status'] = self.get_data_status(
                campaigns,
                last_success_actions,
            )

        return self.create_api_response(response)

    def get_data_status(self, campaigns, last_success_actions):
        return helpers.get_data_status(
            campaigns,
            helpers.get_last_sync_messages(campaigns, last_success_actions),
        )

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
