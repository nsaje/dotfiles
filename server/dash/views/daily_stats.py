from collections import defaultdict
import copy

from dash import stats_helper
from dash.views import helpers
from dash import models
from dash import constants
from dash import campaign_goals

from utils import api_common
from utils import exc

import stats.constants
import stats.api_dailystats

MAX_DAILY_STATS_BREAKDOWNS = 3


class BaseDailyStatsView(api_common.BaseApiView):
    def get_stats(self, request, group_key, objects, constraints, **data):
        metrics = request.GET.getlist('metrics')
        totals = request.GET.get('totals')
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        selected_objects = self._get_selected_objects(request, objects)
        selected_ids = [obj.id for obj in selected_objects]

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        constraints['source'] = filtered_sources

        stats = []

        if totals:
            stats.append(self.get_stats_totals(
                request.user,
                start_date,
                end_date,
                metrics,
                constraints,
                **data
            ))

        if selected_ids:
            stats += self.get_stats_selected(
                request.user,
                start_date,
                end_date,
                metrics,
                selected_ids,
                group_key,
                selected_objects,
                constraints,
                **data
            )

        return {
            'chart_data': stats,
        }

    def get_stats_totals(self, user, start_date, end_date, metrics, constraints, **data):
        stats = self._query_stats(user, start_date, end_date, ['date'], constraints, **data)

        return {
            'id': 'totals',
            'name': 'Totals',
            'series_data': self._format_metric(stats, metrics),
        }

    def _query_stats(self, user, start_date, end_date, breakdown, constraints, conversion_goals=None, pixels=None, campaign=None):
        stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=breakdown,
            order=['date'],
            conversion_goals=conversion_goals,
            pixels=pixels,
            constraints=constraints,
        )

        if campaign and user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(campaign, stats)

        return stats

    def _format_metric(self, stats, metrics):
        data = defaultdict(list)
        for stat in stats:
            for metric in metrics:
                data[metric].append(
                    (stat['date'], stat.get(metric))
                )
        return data

    def _get_selected_objects(self, request, objects):
        select_all = request.GET.get('select_all', False)
        select_batch_id = request.GET.get('select_batch')
        selected_ids = [int(id) for id in request.GET.getlist('selected_ids')]
        not_selected_ids = [int(id) for id in request.GET.getlist('not_selected_ids')]
        return helpers.get_selected_entities(objects, select_all, selected_ids, not_selected_ids, True, select_batch_id)

    def get_stats_selected(self, user, start_date, end_date, metrics, selected_ids, group_key, objects, constraints, **data):
        constraints = copy.copy(constraints)
        constraints[group_key] = selected_ids

        join_selected = len(selected_ids) > MAX_DAILY_STATS_BREAKDOWNS
        if join_selected:
            breakdown = ['date']
        else:
            breakdown = ['date', group_key]

        stats = self._query_stats(user, start_date, end_date, breakdown, constraints, **data)

        if join_selected:
            return [{
                'id': 'selected',
                'name': 'Selected',
                'series_data': self._format_metric(stats, metrics),
            }]

        data = self._get_series_groups_dict(objects, selected_ids)
        for stat in stats:
            group_id = stat.get(group_key)
            for metric in metrics:
                data[group_id]['series_data'][metric].append(
                    (stat['date'], stat.get(metric))
                )

        return data.values()

    def _get_series_groups_dict(self, objects, selected_ids):
        result = {obj.id: {
            'id': obj.id,
            'name': getattr(obj, 'name', None) or obj.title,
            'series_data': defaultdict(list),
        } for obj in objects.filter(pk__in=selected_ids)}

        return result

    def get_goals(
            self,
            request,
            conversion_goals=None,
            campaign=None,
            pixels=None):
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        result = {}
        if conversion_goals is not None:
            result['conversion_goals'] = helpers.get_conversion_goals_wo_pixels(conversion_goals)

        if pixels:
            result['pixels'] = helpers.get_pixels_list(pixels)

        can_see_campaign_goals = user.has_perm('zemauth.campaign_goal_performance')
        if campaign is not None and can_see_campaign_goals:
            result['goal_fields'] = campaign_goals.inverted_campaign_goal_map(
                conversion_goals
            )

            result['campaign_goals'] = dict(
                campaign_goals.get_campaign_goal_metrics(
                    campaign,
                    start_date,
                    end_date
                )
            )
            if conversion_goals:
                result['campaign_goals'].update(
                    campaign_goals.get_campaign_conversion_goal_metrics(
                        campaign,
                        start_date,
                        end_date,
                        conversion_goals
                    )
                )
        return result

    def merge(self, *arg):
        '''
        Merge an arbitrary number of dictionaries
        '''
        ret = {}
        for d in arg:
            ret.update(d)
        return ret


class AllAccountsAccountsDailyStats(BaseDailyStatsView):
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        view_filter = helpers.ViewFilter(request=request)

        accounts = models.Account.objects.all()\
            .filter_by_user(request.user)\
            .filter_by_agencies(view_filter.filtered_agencies)\
            .filter_by_account_types(view_filter.filtered_account_types)
        constraints = {'account': accounts}

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'account',
                    accounts,
                    constraints,
                ),
            )
        )


class AllAccountsSourcesDailyStats(BaseDailyStatsView):
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        view_filter = helpers.ViewFilter(request=request)

        accounts = models.Account.objects.all()\
            .filter_by_user(request.user)\
            .filter_by_agencies(view_filter.filtered_agencies)\
            .filter_by_account_types(view_filter.filtered_account_types)
        constraints = {'account': accounts}

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source',
                    models.Source.objects.all(),
                    constraints,
                ),
            )
        )


class AccountCampaignsDailyStats(BaseDailyStatsView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        constraints = {'account': account.id}

        pixels = account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'campaign',
                    account.campaign_set.all(),
                    constraints,
                    pixels=pixels,
                ),
                self.get_goals(
                    request,
                    pixels=pixels,
                )
            )
        )


class AccountSourcesDailyStats(BaseDailyStatsView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        constraints = {'account': account.id}

        pixels = account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source',
                    models.Source.objects.all(),
                    constraints,
                    pixels=pixels,
                ),
                self.get_goals(
                    request,
                    pixels=pixels,
                )
            )
        )


class CampaignAdGroupsDailyStats(BaseDailyStatsView):
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        constraints = {'campaign': campaign.id}

        conversion_goals = campaign.conversiongoal_set.all()
        pixels = campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'ad_group',
                    campaign.adgroup_set.all(),
                    constraints,
                    conversion_goals=conversion_goals,
                    pixels=pixels,
                    campaign=campaign,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=campaign,
                    pixels=pixels,
                )
            )
        )


class CampaignSourcesDailyStats(BaseDailyStatsView):
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        constraints = {'campaign': campaign.id}

        conversion_goals = campaign.conversiongoal_set.all()
        pixels = campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source',
                    models.Source.objects.all(),
                    constraints,
                    conversion_goals=conversion_goals,
                    pixels=pixels,
                    campaign=campaign,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupContentAdsDailyStats(BaseDailyStatsView):
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        constraints = {'ad_group': ad_group.id}

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        pixels = ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'content_ad',
                    ad_group.contentad_set.all(),
                    constraints,
                    conversion_goals=conversion_goals,
                    pixels=pixels,
                    campaign=ad_group.campaign,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupSourcesDailyStats(BaseDailyStatsView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        constraints = {'ad_group': ad_group.id}

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        pixels = ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source',
                    models.Source.objects.all(),
                    constraints,
                    conversion_goals=conversion_goals,
                    pixels=pixels,
                    campaign=ad_group.campaign,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupPublishersDailyStats(BaseDailyStatsView):
    def get(self, request, ad_group_id, ):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        metrics = request.GET.getlist('metrics')
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        show_blacklisted_publishers = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL)

        breakdown = ['day']
        order = 'day'

        constraints = stats.constraints_helper.prepare_ad_group_constraints(
            request.user, ad_group, breakdown, start_date, end_date, filtered_sources,
            only_used_sources=False, show_blacklisted_publishers=show_blacklisted_publishers)
        goals = stats.api_breakdowns.get_goals(constraints)

        chart_data = {
            "chart_data": [{
                "id": "totals",
                "name": "Totals",
                "series_data": self._format_metric(
                    stats.api_dailystats.query(
                        request.user, breakdown, metrics, constraints, goals, order, should_use_publishers_view=True),
                    metrics
                ),
            }]
        }

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        pixels = ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                chart_data, self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                    pixels=pixels,
                )
            ))

    def _format_metric(self, stats, metrics):
        data = defaultdict(list)
        for stat in stats:
            for metric in metrics:
                data[metric].append(
                    (stat['day'], stat.get(metric))
                )
        return data
