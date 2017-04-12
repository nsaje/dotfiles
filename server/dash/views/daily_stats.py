from collections import defaultdict
from decimal import Decimal

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

    def extract_params(self, request, breakdown, selected_only):
        return {
            'user': request.user,
            'breakdown': breakdown,
            'start_date': helpers.get_stats_start_date(request.GET.get('start_date')),
            'end_date': helpers.get_stats_end_date(request.GET.get('end_date')),
            'filtered_sources': helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')),
        }

    def get_stats(self, request, group_key, should_use_publishers_view=False):
        totals = request.GET.get('totals')
        metrics = request.GET.getlist('metrics')

        result = []
        if totals:
            result.append(self.get_stats_totals(
                request,
                metrics,
                should_use_publishers_view=should_use_publishers_view,
            ))

        if self.selected_objects:
            result += self.get_stats_selected(
                request,
                metrics,
                group_key,
                should_use_publishers_view=should_use_publishers_view,
            )

        return {
            'chart_data': result,
        }

    def get_stats_totals(self, request, metrics, should_use_publishers_view):
        breakdown = ['day']

        constraints = self.prepare_constraints(request, breakdown)
        goals = stats.api_breakdowns.get_goals(constraints)

        query_results = self._query_stats(
            request.user, breakdown, metrics, constraints, goals, should_use_publishers_view)
        return {
            'id': 'totals',
            'name': 'Totals',
            'series_data': self._format_metric(query_results, metrics)['totals'],
        }

    def get_stats_selected(
            self,
            request,
            metrics,
            group_key,
            should_use_publishers_view
    ):
        join_selected = len(self.selected_ids) > MAX_DAILY_STATS_BREAKDOWNS

        breakdown = ['day']
        if not join_selected:
            breakdown.append(group_key)

        constraints = self.prepare_constraints(request, breakdown, selected_only=True)
        goals = stats.api_breakdowns.get_goals(constraints)
        query_results = self._query_stats(
            request.user, breakdown, metrics, constraints, goals, should_use_publishers_view)

        if join_selected:
            return [{
                'id': 'selected',
                'name': 'Selected',
                'series_data': self._format_metric(query_results, metrics)['totals'],
            }]

        data = self._get_series_groups_dict(self.selected_objects)
        formatted = self._format_metric(query_results, metrics, group_key=group_key, group_ids=self.selected_ids)
        for group_id in self.selected_ids:
            data[group_id]['series_data'] = formatted[group_id]
        return data.values()

    def _query_stats(self, user, breakdown, metrics, constraints, goals, should_use_publishers_view):
        order = 'day'
        return stats.api_dailystats.query(
            user,
            breakdown,
            metrics,
            constraints,
            goals,
            order,
            should_use_publishers_view=should_use_publishers_view
        )

    def _get_selected_objects(self, request, objects):
        select_all = request.GET.get('select_all', False)
        select_batch_id = request.GET.get('select_batch')
        selected_ids = [int(id) for id in request.GET.getlist('selected_ids')]
        not_selected_ids = [int(id) for id in request.GET.getlist('not_selected_ids')]
        return helpers.get_selected_entities(objects, select_all, selected_ids, not_selected_ids, True, select_batch_id)

    def _format_metric(self, stats, metrics, group_key=None, group_ids=None):
        data = defaultdict(lambda: defaultdict(list))
        for stat in stats:
            for metric in metrics:
                if not group_key:
                    group_id = 'totals'
                elif group_ids and group_key in stat and stat[group_key] in group_ids:
                    group_id = stat[group_key]
                else:
                    continue
                data[group_id][metric].append(
                    (stat['day'], float(stat[metric]) if isinstance(stat.get(metric), Decimal) else stat.get(metric))
                )
                # when all values are None we treat this as no data (an empty array)
                if all(x[1] is None for x in data[metric]):
                    data[metric] = []
        return data

    def _get_series_groups_dict(self, objects):
        result = {obj.id: {
            'id': obj.id,
            'name': getattr(obj, 'name', None) or obj.title,
        } for obj in objects}

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
            if d:
                ret.update(d)
        return ret


class AllAccountsDailyStatsView(BaseDailyStatsView):

    def prepare_constraints(self, request, breakdown, selected_only=False):
        params = self.extract_params(request, breakdown, selected_only)
        return stats.constraints_helper.prepare_all_accounts_constraints(**params)

    def extract_params(self, request, breakdown, selected_only):
        params = super(AllAccountsDailyStatsView, self).extract_params(request, breakdown, selected_only)
        params['filtered_agencies'] = self.view_filter.filtered_agencies
        params['filtered_account_types'] = self.view_filter.filtered_account_types
        return params


class AllAccountsAccountsDailyStats(AllAccountsDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AllAccountsAccountsDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_accounts'] = self.selected_objects
        return params

    def get(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        self.view_filter = helpers.ViewFilter(request=request)
        accounts = models.Account.objects.all()\
            .filter_by_user(request.user)\
            .filter_by_agencies(self.view_filter.filtered_agencies)\
            .filter_by_account_types(self.view_filter.filtered_account_types)

        self.selected_objects = self._get_selected_objects(request, accounts)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.get_stats(
                request,
                'account_id',
            ),
        )


class AllAccountsSourcesDailyStats(AllAccountsDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AllAccountsSourcesDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_sources'] = params['filtered_sources'].filter(
                id__in=self.selected_objects.values_list('pk', flat=True)
            )
        return params

    def get(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        self.view_filter = helpers.ViewFilter(request=request)
        sources = models.Source.objects.all()

        self.selected_objects = self._get_selected_objects(request, sources)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.get_stats(
                request,
                'source_id',
            ),
        )


class AccountDailyStatsView(BaseDailyStatsView):

    def prepare_constraints(self, request, breakdown, selected_only=False):
        params = self.extract_params(request, breakdown, selected_only)
        return stats.constraints_helper.prepare_account_constraints(**params)

    def extract_params(self, request, breakdown, selected_only):
        params = super(AccountDailyStatsView, self).extract_params(request, breakdown, selected_only)
        params['account'] = self.account
        return params


class AccountCampaignsDailyStats(AccountDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AccountCampaignsDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_campaigns'] = self.selected_objects
        return params

    def get(self, request, account_id):
        self.account = helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)

        campaigns = self.account.campaign_set.all().filter_by_user(request.user)
        self.selected_objects = self._get_selected_objects(request, campaigns)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'campaign_id',
                ),
                self.get_goals(
                    request,
                    pixels=pixels,
                )
            )
        )


class AccountSourcesDailyStats(AccountDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AccountSourcesDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_sources'] = params['filtered_sources'].filter(
                id__in=self.selected_objects.values_list('pk', flat=True)
            )
        return params

    def get(self, request, account_id):
        self.account = helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source_id',
                ),
                self.get_goals(
                    request,
                    pixels=pixels,
                )
            )
        )


class CampaignDailyStatsView(BaseDailyStatsView):

    def prepare_constraints(self, request, breakdown, selected_only=False):
        params = self.extract_params(request, breakdown, selected_only)
        return stats.constraints_helper.prepare_campaign_constraints(**params)

    def extract_params(self, request, breakdown, selected_only):
        params = super(CampaignDailyStatsView, self).extract_params(request, breakdown, selected_only)
        params['campaign'] = self.campaign
        return params


class CampaignAdGroupsDailyStats(CampaignDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(CampaignAdGroupsDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_ad_groups'] = self.selected_objects
        return params

    def get(self, request, campaign_id):
        self.campaign = helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)

        ad_groups = self.campaign.adgroup_set.all()
        self.selected_objects = self._get_selected_objects(request, ad_groups)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'ad_group_id',
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.campaign,
                    pixels=pixels,
                )
            )
        )


class CampaignSourcesDailyStats(CampaignDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(CampaignSourcesDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_sources'] = params['filtered_sources'].filter(
                id__in=self.selected_objects.values_list('pk', flat=True)
            )
        return params

    def get(self, request, campaign_id):
        self.campaign = helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source_id',
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupDailyStatsView(BaseDailyStatsView):

    def prepare_constraints(self, request, breakdown, selected_only=False):
        params = self.extract_params(request, breakdown, selected_only)
        return stats.constraints_helper.prepare_ad_group_constraints(**params)

    def extract_params(self, request, breakdown, selected_only):
        params = super(AdGroupDailyStatsView, self).extract_params(request, breakdown, selected_only)
        params['ad_group'] = self.ad_group
        return params


class AdGroupContentAdsDailyStats(AdGroupDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AdGroupContentAdsDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_content_ads'] = self.selected_objects
        return params

    def get(self, request, ad_group_id):
        self.ad_group = helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        content_ads = self.ad_group.contentad_set.all()
        self.selected_objects = self._get_selected_objects(request, content_ads)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'content_ad_id',
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.ad_group.campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupSourcesDailyStats(AdGroupDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AdGroupSourcesDailyStats, self).extract_params(request, breakdown, selected_only)
        if selected_only:
            params['filtered_sources'] = params['filtered_sources'].filter(
                id__in=self.selected_objects.values_list('pk', flat=True)
            )
        return params

    def get(self, request, ad_group_id):
        self.ad_group = helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)
        self.selected_ids = [obj.id for obj in self.selected_objects]

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    'source_id',
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.ad_group.campaign,
                    pixels=pixels,
                )
            )
        )


class AdGroupPublishersDailyStats(AdGroupDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AdGroupPublishersDailyStats, self).extract_params(request, breakdown, selected_only)
        params['show_blacklisted_publishers'] = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL
        )
        params['only_used_sources'] = False
        return params

    def get(self, request, ad_group_id, ):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        self.ad_group = helpers.get_ad_group(request.user, ad_group_id)

        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        self.selected_objects = None
        self.selected_ids = None

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    None,
                    should_use_publishers_view=True,
                ), self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.ad_group.campaign,
                    pixels=pixels,
                )
            ))
