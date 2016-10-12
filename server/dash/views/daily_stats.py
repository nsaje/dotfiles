from collections import defaultdict
import copy

import reports.api
import reports.api_publishers

from dash import stats_helper
from dash.views import helpers
from dash import models
from dash import constants
from dash import publisher_helpers
from dash import campaign_goals

from utils import api_common
from utils import exc

MAX_DAILY_STATS_BREAKDOWNS = 3


class BaseDailyStatsView(api_common.BaseApiView):

    def get_stats(self, request, group_key, objects, constraints, **data):
        metrics = request.GET.getlist('metrics')
        selected_ids = self._get_selected_ids(request)
        totals = request.GET.get('totals')
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

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
                objects,
                constraints,
                **data
            )

        return {
            'chart_data': stats,
        }

    def get_stats_totals(self, user, start_date, end_date, metrics, constraints, conversion_goals=None, pixels=None, campaign=None):
        stats = stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=conversion_goals,
            pixels=pixels,
            constraints=constraints,
        )

        if campaign and user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(campaign, stats)

        return {
            'id': 'totals',
            'name': 'Totals',
            'series_data': self._format_metric(stats, metrics),
        }

    def _format_metric(self, stats, metrics):
        data = defaultdict(list)
        for stat in stats:
            for metric in metrics:
                data[metric].append(
                    (stat['date'], stat.get(metric))
                )
        return data

    def _get_selected_ids(self, request):
        if not request.GET.getlist('selected_ids'):
            return []
        return [int(id) for id in request.GET.getlist('selected_ids')]

    def get_stats_selected(self, user, start_date, end_date, metrics, selected_ids, group_key, objects, constraints, conversion_goals=None, pixels=None, campaign=None):
        constraints = copy.copy(constraints)
        constraints[group_key] = selected_ids

        join_selected = len(selected_ids) > MAX_DAILY_STATS_BREAKDOWNS
        if join_selected:
            breakdown = ['date']
        else:
            breakdown = ['date', group_key]

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
                    models.Account.objects,
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
                    models.Source.objects,
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
                    models.Campaign.objects,
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
                    models.Source.objects,
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
                    models.AdGroup.objects,
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
                    models.Source.objects,
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
                    models.ContentAd.objects,
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
                    models.Source.objects,
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
        constraints = {'ad_group': ad_group.id}

        show_blacklisted_publishers = request.GET.get(
            'show_blacklisted_publishers', constants.PublisherBlacklistFilter.SHOW_ALL)

        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        pixels = ad_group.campaign.account.conversionpixel_set.filter(archived=False)

        return self.create_api_response(
            self.merge(
                self.get_stats(
                    request,
                    None,
                    None,
                    constraints,
                    conversion_goals=conversion_goals,
                    pixels=pixels,
                    show_blacklisted_publishers=show_blacklisted_publishers,
                    ad_group=ad_group,
                ),
                self.get_goals(
                    request,
                    conversion_goals=conversion_goals,
                    campaign=ad_group.campaign,
                    pixels=pixels,
                )
            )
        )

    def get_stats_selected(self, user, start_date, end_date, metrics, selected_ids, group_key, objects, constraints):
        return []

    def get_stats_totals(self, user, start_date, end_date, metrics, constraints, conversion_goals=None, pixels=None, show_blacklisted_publishers=None, ad_group=None):
        if 'source' in constraints:
            constraints['exchange'] = [s.bidder_slug if s.bidder_slug else s.name.lower() for s in constraints['source']]
            del constraints['source']

        stats = []

        if not show_blacklisted_publishers or\
                show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ALL:
            stats = stats_helper.get_publishers_data_and_conversion_goals(
                user,
                reports.api_publishers.query,
                start_date,
                end_date,
                constraints,
                conversion_goals,
                pixels,
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

            stats = stats_helper.get_publishers_data_and_conversion_goals(
                user,
                query_func,
                start_date,
                end_date,
                constraints,
                conversion_goals,
                pixels,
                publisher_breakdown_fields=['date'],
                touchpoint_breakdown_fields=['date'],
                order_fields=['date'],
                show_blacklisted_publishers=show_blacklisted_publishers,
                adg_blacklisted_publishers=adg_blacklisted_publishers,
            )

        if user.has_perm('zemauth.campaign_goal_optimization'):
            stats = campaign_goals.create_goals(ad_group.campaign, stats)

        return {
            'id': 'totals',
            'name': 'Totals',
            'series_data': self._format_metric(stats, metrics),
        }
