from dash.views import helpers
from dash.views import breakdown_forms

from utils import api_common

import stats.api_breakdowns


class AllAccountsBreakdown(api_common.BaseApiView):
    def post(self, request, breakdown):
        request_data = request.POST

        constraints = breakdown_forms.clean_default_params(request.user, request_data)
        breakdown = breakdown_forms.clean_breakdown(breakdown)
        breakdown_constraints = breakdown_forms.clean_breakdown_page(request_data, breakdown)

        page, page_size = breakdown_forms.clean_page_params(request_data)
        order = breakdown_forms.clean_order(request_data)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            constraints,
            breakdown_constraints,
            order,
            page,
            page_size
        )

        return self.create_api_response(report)


class AccountBreakdown(api_common.BaseApiView):
    def post(self, request, account_id, breakdown):
        request_data = request.POST

        account = helpers.get_account(request.user, account_id)

        constraints = breakdown_forms.clean_default_params(request.user, request_data)
        breakdown = breakdown_forms.clean_breakdown(breakdown)
        breakdown_constraints = breakdown_forms.clean_breakdown_page(request_data, breakdown)

        page, page_size = breakdown_forms.clean_page_params(request_data)
        order = breakdown_forms.clean_order(request_data)

        constraints['account'] = account

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            constraints,
            breakdown_constraints,
            order,
            page,
            page_size
        )

        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):
    def post(self, request, campaign_id, breakdown):
        request_data = request.POST

        campaign = helpers.get_campaign(request.user, campaign_id)

        constraints = breakdown_forms.clean_default_params(request.user, request_data)
        constraints['campaign'] = campaign
        breakdown = breakdown_forms.clean_breakdown(breakdown)
        breakdown_constraints = breakdown_forms.clean_breakdown_page(request_data, breakdown)

        page, page_size = breakdown_forms.clean_page_params(request_data)
        order = breakdown_forms.clean_order(request_data)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            constraints,
            breakdown_constraints,
            order,
            page,
            page_size
        )

        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):
    def post(self, request, ad_group_id, breakdown):
        request_data = request.POST

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        constraints = breakdown_forms.clean_default_params(request.user, request_data)
        constraints['ad_group'] = ad_group
        breakdown = breakdown_forms.clean_breakdown(breakdown)
        breakdown_constraints = breakdown_forms.clean_breakdown_page(request_data, breakdown)

        page, page_size = breakdown_forms.clean_page_params(request_data)
        order = breakdown_forms.clean_order(request_data)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            constraints,
            breakdown_constraints,
            order,
            page,
            page_size
        )

        return self.create_api_response(report)
