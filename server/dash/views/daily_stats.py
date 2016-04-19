from django.db.models import Q

import reports.api
import reports.api_publishers

from dash import stats_helper
from dash.views import helpers
from dash import models
from dash import constants
from dash import publisher_helpers
from dash import campaign_goals

from utils import statsd_helper
from utils import api_common
from utils import exc
from utils.sort_helper import sort_results


class BaseDailyStatsView(api_common.BaseApiView):
    def get_stats(self, request, totals_kwargs, selected_kwargs=None, group_key=None, conversion_goals=None):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        totals_stats = []

        if totals_kwargs:
            totals_stats = stats_helper.get_stats_with_conversions(
                request.user,
                start_date,
                end_date,
                breakdown=['date'],
                order=['date'],
                conversion_goals=conversion_goals,
                constraints=totals_kwargs
            )

        breakdown_stats = []

        if selected_kwargs:
            breakdown_stats = stats_helper.get_stats_with_conversions(
                request.user,
                start_date,
                end_date,
                breakdown=['date', group_key],
                order=['date'],
                conversion_goals=conversion_goals,
                constraints=selected_kwargs,
            )

        return breakdown_stats + totals_stats

    def _get_series_groups_dict(self, totals, groups_dict):
        result = {}

        if groups_dict is not None:
            result = {key: {
                'id': key,
                'name': groups_dict[key],
                'series_data': {}
            } for key in groups_dict}

        if totals:
            result['totals'] = {
                'id': 'totals',
                'name': 'Totals',
                'series_data': {}
            }

        return result

    def get_response_dict(
        self,
        stats,
        totals,
        groups_dict,
        metrics,
        group_key=None
    ):
        series_groups = self._get_series_groups_dict(totals, groups_dict)

        for stat in stats:
            # get id of group it belongs to
            group_id = stat.get(group_key) or 'totals'

            data = series_groups[group_id]['series_data']
            for metric in metrics:
                if metric not in data:
                    data[metric] = []

                series_groups[group_id]['series_data'][metric].append(
                    (stat['date'], stat.get(metric))
                )

        result = {
            'chart_data': series_groups.values()
        }

        return result

    def get_goals(
        self,
        request,
        conversion_goals=None,
        can_see_conversion_goals=True,
        campaign=None,
    ):
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        result = {}
        can_see_conversion_goals = can_see_conversion_goals and\
            user.has_perm('zemauth.conversion_reports')
        if can_see_conversion_goals and conversion_goals is not None:
            result['conversion_goals'] = [{'id': cg.get_view_key(conversion_goals), 'name': cg.name} for cg in conversion_goals]

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


class AccountDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'account_daily_stats_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')
        sources = request.GET.get('sources')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        totals_kwargs = None
        selected_kwargs = None
        group_key = 'campaign'
        group_names = None

        if sources:
            group_key = 'source'

        if totals:
            totals_kwargs = {'account': int(account.id), 'source': filtered_sources}

        if selected_ids:
            ids = map(int, selected_ids)

            selected_kwargs = {
                'account': int(account.id),
            }
            if request.user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
                if sources:
                    selected_kwargs['source'] = ids
                else:
                    selected_kwargs['campaign'] = ids
            else:
                selected_kwargs['source_id' if sources else 'ad_group__campaign__id'] = ids

            if sources:
                sources = models.Source.objects.filter(pk__in=ids)
                group_names = {source.id: source.name for source in sources}
            else:
                campaigns = models.Campaign.objects.filter(pk__in=ids)
                group_names = {campaign.id: campaign.name for campaign in campaigns}

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, group_key)
        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            group_names,
            metrics,
            group_key
        ))


class CampaignDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_daily_stats_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')
        sources = request.GET.get('sources')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        totals_kwargs = None
        selected_kwargs = None
        group_key = 'ad_group'
        group_names = None

        if sources:
            group_key = 'source'

        if totals:
            totals_kwargs = {'campaign': int(campaign.id), 'source': filtered_sources}

        if selected_ids:
            ids = [int(x) for x in selected_ids]

            if request.user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
                selected_kwargs = {'campaign': int(campaign.id), '{}'.format(group_key): ids}
            else:
                selected_kwargs = {'campaign': int(campaign.id), '{}_id'.format(group_key): ids}

            if sources:
                sources = models.Source.objects.filter(pk__in=ids)
                group_names = {source.id: source.name for source in sources}
            else:
                ad_groups = models.AdGroup.objects.filter(pk__in=ids)
                group_names = {ad_group.id: ad_group.name for ad_group in ad_groups}

        conversion_goals = campaign.conversiongoal_set.all()
        stats = self.get_stats(request, totals_kwargs, selected_kwargs, group_key, conversion_goals)
        if request.user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(campaign, stats)

        return self.create_api_response(
            self.merge(
                self.get_response_dict(
                    stats,
                    totals,
                    group_names,
                    metrics,
                    group_key,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=campaign,
                )
            )
        )


class AdGroupDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_daily_stats_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        totals_kwargs = None
        selected_kwargs = None
        sources = []

        if totals:
            totals_kwargs = {'ad_group': int(ad_group.id), 'source': filtered_sources}

        if selected_ids:
            ids = map(int, selected_ids)
            sources = models.Source.objects.filter(id__in=tuple(ids))
            selected_kwargs = {'ad_group': int(ad_group.id), 'source': sources}

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        stats = self.get_stats(
            request, totals_kwargs, selected_kwargs=selected_kwargs,
            group_key='source', conversion_goals=conversion_goals)

        if request.user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(ad_group.campaign, stats)

        return self.create_api_response(
            self.merge(
                self.get_response_dict(
                    stats,
                    totals,
                    {source.id: source.name for source in sources},
                    metrics,
                    group_key='source',
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                )
            )
        )


class AdGroupPublishersDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_publishers_daily_stats_get')
    def get(self, request, ad_group_id, ):
        if not request.user.has_perm('zemauth.can_see_publishers'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        metrics = request.GET.getlist('metrics')
        totals = request.GET.get('totals')
        show_blacklisted_publishers = request.GET.get('show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL)

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        totals_constraints = None
        map_exchange_to_source_name = {}
        # bidder_slug is unique, so no issues with taking all of the sources
        for s in filtered_sources:
            if s.bidder_slug:
                exchange_name = s.bidder_slug
            else:
                exchange_name = s.name.lower()
            map_exchange_to_source_name[exchange_name] = s.name

        if totals:
            totals_constraints = {'ad_group': int(ad_group.id)}

        if set(models.Source.objects.all()) != set(filtered_sources):
            totals_constraints['exchange'] = map_exchange_to_source_name.keys()

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        stats = self.get_stats(request, ad_group, totals_constraints, show_blacklisted_publishers, selected_kwargs=None, group_key='source', conversion_goals=conversion_goals)

        if request.user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(ad_group.campaign, stats)

        can_see_conversion_goals = request.user.has_perm('zemauth.view_pubs_conversion_goals')
        return self.create_api_response(
            self.merge(
                self.get_response_dict(
                    stats,
                    totals,
                    {},
                    metrics,
                    'domain',
                ),
                self.get_goals(
                    request,
                    can_see_conversion_goals=can_see_conversion_goals,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                )
            )
        )

    def get_stats(self, request, ad_group, totals_constraints, show_blacklisted_publishers, selected_kwargs=None, group_key=None, conversion_goals=None):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        totals_stats = []
        if totals_constraints:

            if not show_blacklisted_publishers or\
                    show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ALL:
                totals_stats = stats_helper.get_publishers_data_and_conversion_goals(
                    request.user,
                    reports.api_publishers.query,
                    start_date,
                    end_date,
                    totals_constraints,
                    conversion_goals,
                    publisher_breakdown_fields=['date'],
                    touchpoint_breakdown_fields=['date'],
                    order_fields=['date'])

            elif show_blacklisted_publishers in (
                constants.PublisherBlacklistFilter.SHOW_ACTIVE,
                constants.PublisherBlacklistFilter.SHOW_BLACKLISTED,):

                adg_blacklisted_publishers = publisher_helpers.prepare_publishers_for_rs_query(
                    ad_group
                )

                query_func = None
                if show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ACTIVE:
                    query_func = reports.api_publishers.query_active_publishers
                else:
                    query_func = reports.api_publishers.query_blacklisted_publishers

                totals_stats = stats_helper.get_publishers_data_and_conversion_goals(
                    request.user,
                    query_func,
                    start_date,
                    end_date,
                    totals_constraints,
                    conversion_goals,
                    publisher_breakdown_fields=['date'],
                    touchpoint_breakdown_fields=['date'],
                    order_fields=['date'],
                    show_blacklisted_publishers=show_blacklisted_publishers,
                    adg_blacklisted_publishers=adg_blacklisted_publishers,
                )

        breakdown_stats = []

        return breakdown_stats + totals_stats


class AccountsDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_daily_stats_get')
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        totals_kwargs = None
        selected_kwargs = None
        group_key = None
        group_names = None

        accounts = models.Account.objects.all().filter_by_user(request.user)

        if totals:
            totals_kwargs = {'account': accounts, 'source': filtered_sources}

        if selected_ids:
            ids = map(int, selected_ids)
            sources = models.Source.objects.filter(id__in=tuple(ids))
            selected_kwargs = {'account': accounts, 'source': sources}

            group_key = 'source'

            sources = models.Source.objects.filter(pk__in=ids)
            group_names = {source.id: source.name for source in sources}

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, group_key)

        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            group_names,
            metrics=metrics,
            group_key=group_key
        ))


class AdGroupAdsDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_daily_stats_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        metrics = request.GET.getlist('metrics')
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        stats = self._get_stats(request, ad_group, filtered_sources, conversion_goals)

        if request.user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(ad_group.campaign, stats)

        return self.create_api_response(
            self.merge(
                self.get_response_dict(
                    stats,
                    totals=True,
                    groups_dict=None,
                    metrics=metrics,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                )
            )
        )

    def _get_stats(self, request, ad_group, sources, conversion_goals):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        stats = stats_helper.get_content_ad_stats_with_conversions(
            request.user,
            start_date,
            end_date,
            breakdown=['date'],
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            constraints={'ad_group': ad_group.id, 'source': sources}
        )

        return sort_results(stats, ['date'])
