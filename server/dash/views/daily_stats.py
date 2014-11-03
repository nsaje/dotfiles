import slugify

import reports.api

from dash.views import helpers
from dash import models

from utils import statsd_helper
from utils import api_common
from utils import exc


class BaseDailyStatsView(api_common.BaseApiView):
    def get_stats(self, request, totals_kwargs, selected_kwargs=None, group_key=None):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        breakdown = ['date']

        totals_stats = []
        if totals_kwargs:
            totals_stats = reports.api.query(
                start_date,
                end_date,
                breakdown,
                ['date'],
                **totals_kwargs
            )

        breakdown_stats = []

        if selected_kwargs:
            breakdown.append(group_key)
            breakdown_stats = reports.api.query(
                start_date,
                end_date,
                breakdown,
                ['date'],
                **selected_kwargs
            )

        return breakdown_stats + totals_stats

    def get_series_groups_dict(self, totals, groups_dict):
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

    def process_stat_goals(self, stat_goals, goals, stat):
        # may modify goal_metrics and stat
        for goal_name, goal_metrics in stat_goals.items():
            for metric_type, metric_value in goal_metrics.items():
                metric_id = '{}_goal_{}'.format(
                    slugify.slugify(goal_name).encode('ascii', 'replace'),
                    metric_type
                )

                if metric_id not in goal_metrics:
                    goals[metric_id] = {
                        'name': goal_name,
                        'type': metric_type
                    }

                # set it in stat
                stat[metric_id] = metric_value

    def get_response_dict(self, stats, totals, groups_dict, metrics, group_key=None):
        series_groups = self.get_series_groups_dict(totals, groups_dict)
        goals = {}

        for stat in stats:
            if stat.get('goals') is not None:
                self.process_stat_goals(stat['goals'], goals, stat)

            # get id of group it belongs to
            group_id = stat.get(group_key) or 'totals'

            data = series_groups[group_id]['series_data']
            for metric in metrics:
                if metric not in data:
                    data[metric] = []

                series_groups[group_id]['series_data'][metric].append(
                    (stat['date'], stat.get(metric))
                )

        return {
            'goals': goals,
            'chart_data': series_groups.values()
        }


class AccountDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'account_daily_stats_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')
        sources = request.GET.get('sources')

        totals_kwargs = None
        selected_kwargs = None
        group_key = 'campaign'
        group_names = None

        if sources:
            group_key = 'source'

        if totals:
            totals_kwargs = {'account': int(account.id)}

        if selected_ids:
            ids = [int(x) for x in selected_ids]
            selected_kwargs = {'account': int(account.id), group_key: ids}

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

        totals_kwargs = None
        selected_kwargs = None
        group_key = 'ad_group'
        group_names = None

        if sources:
            group_key = 'source'

        if totals:
            totals_kwargs = {'campaign': int(campaign.id)}

        if selected_ids:
            ids = [int(x) for x in selected_ids]
            selected_kwargs = {'campaign': int(campaign.id), '{}_id'.format(group_key): ids}

            if sources:
                sources = models.Source.objects.filter(pk__in=ids)
                group_names = {source.id: source.name for source in sources}
            else:
                ad_groups = models.AdGroup.objects.filter(pk__in=ids)
                group_names = {ad_group.id: ad_group.name for ad_group in ad_groups}

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, group_key)

        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            group_names,
            metrics,
            group_key
        ))


class AdGroupDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_daily_stats_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')

        totals_kwargs = None
        selected_kwargs = None
        sources = []

        if totals:
            totals_kwargs = {'ad_group': int(ad_group.id)}

        if selected_ids:
            ids = [int(x) for x in selected_ids]
            selected_kwargs = {'ad_group': int(ad_group.id), 'source_id': ids}

            sources = models.Source.objects.filter(pk__in=ids)

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, 'source')

        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            {source.id: source.name for source in sources},
            metrics,
            'source'
        ))


class AccountsDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_daily_stats_get')
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')

        totals_kwargs = None
        selected_kwargs = None
        group_key = None
        group_names = None

        accounts = models.Account.objects.all().filter_by_user(request.user)

        if totals:
            totals_kwargs = {'account': accounts}

        if selected_ids:
            ids = [int(x) for x in selected_ids]
            selected_kwargs = {'account': accounts, 'source_id': ids}

            group_key = 'source'

            sources = models.Source.objects.filter(pk__in=ids)
            group_names = {source.id: source.name for source in sources}

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, group_key)

        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            group_names,
            metrics,
            group_key
        ))
