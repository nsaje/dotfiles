
from dash.views import helpers
from utils import exc
from utils import api_common


"""
Views by level so that we do separate auth
BUT
  we want to merge that with reports

Per level initialization
"""

"""
Common parameters that need to parsed and are differently parsed for exports:
show_archived
filtered_sources
account_id ...
"""

def clean_default_parameters(request):
    start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
    end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
    filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
    show_archived = request.GET.get('show_archived') == 'true'

    return {
        'start_date': start_date,
        'end_date': end_date,
        'filtered_sources': filtered_sources,
        'show_archived': show_archived,
    }


def clean_breakdown(request, params):
    pass


def clean_order(request):
    return request.GET.get('order')


def get_report(request, breakdown, params=None):
    if params is None:
        params = {}

    params.update(clean_default_parameters(request))
    user = request.user

    order = clean_order(request)
    breakdown = clean_breakdown(breakdown)


class AllAccountsBreakdown(api_common.BaseApiView):
    def get(self, request, breakdown):
        params = clean_default_parameters(request)
        pass


class AccountBreakdown(api_common.BaseApiView):
    def get(self, request, account_id, breakdown):

        params = {
            'account': helpers.get_account(request.user, account_id)
        }

        report = get_report(request, breakdown, params)
        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):
    def get(self, request, campaign_id, breakdown):
        params = {
            'campaign': helpers.get_campaign(request.user, campaign_id)
        }

        report = get_report(request, breakdown, params)
        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):
    def get(self, request, ad_group_id, breakdown):
        params = {
            'ad_group': helpers.get_ad_group(request.user, ad_group_id)
        }

        report = get_report(request, breakdown, params)
        return self.create_api_response(report)


class BreakdownView(api_common.BaseApiView):
    def get(self, request, level_, id_, breakdown):
        # check permissions for table_breakdowns
        # clean query parameters - create constraints

        # validate breakdown is supported (call stats)
        # validate breakdown size (call stats)

        # execute the breakdown
        # convert results to format suitable for resposne
        return self.create_api_response({})