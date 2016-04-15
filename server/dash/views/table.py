import newrelic.agent

from dash.views import helpers
from dash import table as dt

from utils import api_common
from utils import statsd_helper


class AdGroupSourcesTableUpdates(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_notifications_get')
    def get(self, request, ad_group_id_=None):
        user = request.user

        last_change_dt = helpers.parse_datetime(request.GET.get('last_change_dt'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))

        response = dt.AdGroupSourcesTableUpdates().get(
            user,
            last_change_dt,
            filtered_sources,
            ad_group_id_
        )

        return self.create_api_response(response)


class SourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.sources_table_get')
    @newrelic.agent.function_trace()
    def get(self, request, level_, id_=None):
        newrelic.agent.set_transaction_name('dash.views.table:SourcesTable#%s' % (level_))

        user = request.user
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        order = request.GET.get('order', None)

        response = dt.SourcesTable().get(
            user,
            level_,
            filtered_sources,
            start_date,
            end_date,
            order,
            id_
        )

        return self.create_api_response(response)


class AccountsAccountsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_accounts_table_get')
    def get(self, request):

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        page = request.GET.get('page')
        size = request.GET.get('size')
        order = request.GET.get('order')

        show_archived = request.GET.get('show_archived') == 'true'

        user = request.user

        response = dt.AccountsAccountsTable().get(
            user,
            filtered_sources,
            start_date,
            end_date,
            order,
            page,
            size,
            show_archived
        )

        return self.create_api_response(response)


class AdGroupAdsPlusTableUpdates(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_table_updates_get')
    def get(self, request, ad_group_id):
        user = request.user

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        last_change_dt = helpers.parse_datetime(request.GET.get('last_change'))

        response = dt.AdGroupAdsPlusTableUpdates().get(
            user,
            ad_group_id,
            filtered_sources,
            last_change_dt
        )

        return self.create_api_response(response)


class AdGroupAdsPlusTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_table_get')
    def get(self, request, ad_group_id):
        from pudb import set_trace; set_trace()
        user = request.user

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        page = request.GET.get('page')
        order = request.GET.get('order') or 'cost'
        size = request.GET.get('size')
        show_archived = request.GET.get('show_archived')

        response = dt.AdGroupAdsPlusTable().get(
            user,
            ad_group_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            page,
            size,
            show_archived
        )

        return self.create_api_response(response)


class CampaignAdGroupsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_ad_groups_table_get')
    def get(self, request, campaign_id):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-cost'
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        show_archived = request.GET.get('show_archived')

        user = request.user

        response = dt.CampaignAdGroupsTable().get(
            user,
            campaign_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            show_archived
        )
        return self.create_api_response(response)


class AccountCampaignsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_campaigns_table_get')
    def get(self, request, account_id):
        user = request.user

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        show_archived = request.GET.get('show_archived')

        response = dt.AccountCampaignsTable().get(
            user,
            account_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            show_archived
        )

        return self.create_api_response(response)


class PublishersTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.publishers_table_get')
    def get(self, request, level_, id_=None):
        newrelic.agent.set_transaction_name('dash.views.table:PublishersTable#%s' % (level_))

        user = request.user

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        page = request.GET.get('page')
        order = request.GET.get('order') or 'cost'
        size = request.GET.get('size')

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        show_blacklisted_publishers = request.GET.get('show_blacklisted_publishers')

        response = dt.PublishersTable().get(
            user,
            level_,
            filtered_sources,
            show_blacklisted_publishers,
            start_date,
            end_date,
            order,
            page,
            size,
            id_
        )

        return self.create_api_response(response)
