import json

from dash import forms
from dash import table
from dash.views import helpers

from utils import api_common
from utils import exc

import stats.api_breakdowns
import stats.helpers


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


def format_breakdown_response(report_rows, offset, limit):
    blocks = {}

    for row in report_rows:
        if not row['parent_breakdown_id'] in blocks:
            blocks[row['parent_breakdown_id']] = {
                'breakdown_id': row['parent_breakdown_id'],
                'rows': [],
                'totals': {},
                'pagination': {
                    'offset': offset,
                    'limit': limit,
                    'count': -1,  # TODO count
                },
            }

        block = blocks[row['parent_breakdown_id']]
        block['rows'].append(row)

    return blocks.values()


def get_report_through_table(user, form_data):
    """
    FIXME: This code is temporary! It will only be used for the prototype.

    Reuses the the table.py ofr base level breakdowns.
    """

    constraints = extract_constraints(form_data)

    start_date = constraints['date__gte']
    end_date = constraints['date__lte']

    filtered_sources = constraints.get('source')

    offset = form_data.get('offset', DEFAULT_OFFSET)
    limit = form_data.get('limit', DEFAULT_LIMIT)

    # this mapping is not precise, for the demo it will suffice
    size = limit
    page = int(offset / size) + 1
    order = form_data.get('order')

    show_archived = form_data.get('show_archived', False)

    response = table.AccountsAccountsTable().get(
        user,
        filtered_sources,
        start_date,
        end_date,
        order,
        page,
        size,
        show_archived
    )

    for row in response['rows']:
        row['account_id'] = int(row['id'])
        row['account_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['account'], row)
        row['parent_breakdown_id'] = None

    return [{
        'breakdown_id': None,
        'rows': response['rows'],
        'totals': response['totals'],
        'pagination': {
            'offset': response['pagination']['startIndex'] - 1,  # offset is 0-based
            'limit': response['pagination']['endIndex'] - response['pagination']['startIndex'] - 1,
            'count': response['pagination']['count'],
        }
    }]


class AllAccountsBreakdown(api_common.BaseApiView):
    def post(self, request, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.AuthorizationError()

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)
        breakdown = form.cleaned_data.get('breakdown')

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(request.user, form.cleaned_data)
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit)
        return self.create_api_response(report)


class AccountBreakdown(api_common.BaseApiView):
    def post(self, request, account_id, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, account=account),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit)
        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):
    def post(self, request, campaign_id, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, campaign=campaign),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit)
        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):
    def post(self, request, ad_group_id, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)

        report = stats.api_breakdowns.query(
            request.user,
            form.cleaned_data['breakdown'],
            extract_constraints(form.cleaned_data, ad_group=ad_group),
            form.cleaned_data.get('breakdown_page', None),
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit)
        return self.create_api_response(report)
