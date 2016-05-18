import json

from dash import forms
from dash.views import helpers

from utils import api_common
from utils import exc

import stats.api_breakdowns


DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 10


def extract_constraints(form_data, **kwargs):
    constraints = {
        'date__gte': form_data['start_date'],
        'date__lte': form_data['end_date'],
        'source': form_data.get('filtered_sources'),
        'show_archived': form_data.get('show_archived'),
    }
    constraints.update(kwargs)
    return constraints


class AllAccountsBreakdown(api_common.BaseApiView):
    def post(self, request, breakdown):
        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            form.cleaned_data.get('offset', DEFAULT_OFFSET),
            form.cleaned_data.get('limit', DEFAULT_LIMIT)
        )

        return self.create_api_response(report)


class AccountBreakdown(api_common.BaseApiView):
    def post(self, request, account_id, breakdown):
        account = helpers.get_account(request.user, account_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, account=account),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            form.cleaned_data.get('offset', DEFAULT_OFFSET),
            form.cleaned_data.get('limit', DEFAULT_LIMIT)
        )

        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):
    def post(self, request, campaign_id, breakdown):
        campaign = helpers.get_campaign(request.user, campaign_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, campaign=campaign),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            form.cleaned_data.get('offset', DEFAULT_OFFSET),
            form.cleaned_data.get('limit', DEFAULT_LIMIT)
        )

        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):
    def post(self, request, ad_group_id, breakdown):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, ad_group=ad_group),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            form.cleaned_data.get('offset', DEFAULT_OFFSET),
            form.cleaned_data.get('limit', DEFAULT_LIMIT)
        )

        return self.create_api_response(report)

