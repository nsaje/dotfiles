import dash.views.helpers
from dash import models
from dash import constants
from dash import campaign_goals

from utils import api_common
from utils import exc

import stats.api_breakdowns
import stats.api_dailystats
import stats.constraints_helper

import helpers

MAX_DAILY_STATS_BREAKDOWNS = 3


class BaseDailyStatsView(api_common.BaseApiView):

    def extract_params(self, request, breakdown, selected_only):
        return {
            'user': request.user,
            'breakdown': breakdown,
            'start_date': dash.views.helpers.get_stats_start_date(request.GET.get('start_date')),
            'end_date': dash.views.helpers.get_stats_end_date(request.GET.get('end_date')),
            'filtered_sources': dash.views.helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')),
            'show_archived': request.GET.get('filtered_sources') == 'true',
        }

    def get_stats(self, request, group_key, should_use_publishers_view=False):
        totals = request.GET.get('totals')
        metrics = request.GET.getlist('metrics')

        result = []
        if totals:
            result += self.get_stats_totals(
                request,
                metrics,
                should_use_publishers_view=should_use_publishers_view,
            )

        if self.selected_objects:
            result += self.get_stats_selected(
                request,
                metrics,
                group_key,
                [obj.id for obj in self.selected_objects],
                should_use_publishers_view=should_use_publishers_view,
            )

        return {
            'chart_data': result,
        }

    def get_stats_totals(self, request, metrics, should_use_publishers_view):
        breakdown = ['day']

        constraints = self.prepare_constraints(request, breakdown)
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        query_results = stats.api_dailystats.query(
            request.user,
            breakdown,
            metrics,
            constraints,
            goals,
            'day',
            should_use_publishers_view=should_use_publishers_view
        )
        return helpers.format_metrics(
            query_results,
            metrics,
            {
                'totals': 'Totals',
            },
            default_group='totals',
        )

    def get_stats_selected(
            self,
            request,
            metrics,
            group_key,
            selected_ids,
            should_use_publishers_view
    ):
        join_selected = len(selected_ids) > MAX_DAILY_STATS_BREAKDOWNS

        breakdown = ['day']
        if not join_selected:
            breakdown.append(group_key)

        constraints = self.prepare_constraints(request, breakdown, selected_only=True)
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)
        query_results = stats.api_dailystats.query(
            request.user,
            breakdown,
            metrics,
            constraints,
            goals,
            'day',
            should_use_publishers_view=should_use_publishers_view
        )

        if join_selected:
            return helpers.format_metrics(
                query_results,
                metrics,
                {
                    'selected': 'Selected',
                },
                default_group='selected',
            )
        else:
            return helpers.format_metrics(
                query_results,
                metrics,
                helpers.get_object_mapping(self.selected_objects),
                group_key=group_key,
            )

    def _get_selected_objects(self, request, objects):
        select_all = request.GET.get('select_all', False)
        select_batch_id = request.GET.get('select_batch')
        selected_ids = [int(id) for id in request.GET.getlist('selected_ids')]
        not_selected_ids = [int(id) for id in request.GET.getlist('not_selected_ids')]
        return dash.views.helpers.get_selected_entities(objects, select_all, selected_ids, not_selected_ids, True, select_batch_id)

    def get_goals(
            self,
            request,
            conversion_goals=None,
            campaign=None,
            pixels=None):
        user = request.user
        start_date = dash.views.helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = dash.views.helpers.get_stats_end_date(request.GET.get('end_date'))

        result = {}
        if conversion_goals is not None:
            result['conversion_goals'] = dash.views.helpers.get_conversion_goals_wo_pixels(conversion_goals)

        if pixels:
            result['pixels'] = dash.views.helpers.get_pixels_list(pixels)

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

        self.view_filter = dash.views.helpers.ViewFilter(request=request)
        accounts = models.Account.objects.all()\
            .filter_by_user(request.user)\
            .filter_by_agencies(self.view_filter.filtered_agencies)\
            .filter_by_account_types(self.view_filter.filtered_account_types)

        self.selected_objects = self._get_selected_objects(request, accounts)

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

        self.view_filter = dash.views.helpers.ViewFilter(request=request)
        sources = models.Source.objects.all()

        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            self.get_stats(
                request,
                'source_id',
            ),
        )


class AllAccountsPublishersDailyStats(AllAccountsDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AllAccountsPublishersDailyStats, self).extract_params(request, breakdown, selected_only)
        params['show_blacklisted_publishers'] = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL
        )
        params['only_used_sources'] = False
        return params

    def get(self, request):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        self.view_filter = dash.views.helpers.ViewFilter(request=request)

        self.selected_objects = None

        return self.create_api_response(
            self.get_stats(
                request,
                None,
                should_use_publishers_view=True,
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
        self.account = dash.views.helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)

        campaigns = self.account.campaign_set.all().filter_by_user(request.user)
        self.selected_objects = self._get_selected_objects(request, campaigns)

        return self.create_api_response(
            helpers.merge(
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
        self.account = dash.views.helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(
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


class AccountPublishersDailyStats(AccountDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(AccountPublishersDailyStats, self).extract_params(request, breakdown, selected_only)
        params['show_blacklisted_publishers'] = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL
        )
        params['only_used_sources'] = False
        return params

    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        self.account = dash.views.helpers.get_account(request.user, account_id)

        pixels = self.account.conversionpixel_set.filter(archived=False)

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
                self.get_stats(
                    request,
                    None,
                    should_use_publishers_view=True,
                ), self.get_goals(
                    request,
                    pixels=pixels,
                )
            ))


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
        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)

        ad_groups = self.campaign.adgroup_set.all()
        self.selected_objects = self._get_selected_objects(request, ad_groups)

        return self.create_api_response(
            helpers.merge(
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
        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(
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


class CampaignPublishersDailyStats(CampaignDailyStatsView):

    def extract_params(self, request, breakdown, selected_only):
        params = super(CampaignPublishersDailyStats, self).extract_params(request, breakdown, selected_only)
        params['show_blacklisted_publishers'] = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL
        )
        params['only_used_sources'] = False
        return params

    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)

        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
                self.get_stats(
                    request,
                    None,
                    should_use_publishers_view=True,
                ), self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=self.campaign,
                    pixels=pixels,
                )
            ))


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
        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        content_ads = self.ad_group.contentad_set.all()
        self.selected_objects = self._get_selected_objects(request, content_ads)

        return self.create_api_response(
            helpers.merge(
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
        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(
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

        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)

        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
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
