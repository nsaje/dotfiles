import collections
import json

from dash import forms
from dash import table
from dash.views import helpers

from utils import api_common
from utils import exc

import stats.api_breakdowns
import stats.helpers
import stats.constants


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


def format_breakdown_response(report_rows, offset, limit, breakdown_page):
    blocks = []

    # map rows by breakdown pages
    rows_by_parent_br_id = collections.defaultdict(list)
    for row in report_rows:
        rows_by_parent_br_id[row['parent_breakdown_id']].append(row)

    # create blocks for every breakdown_page
    for parent_br_id in breakdown_page:
        rows = rows_by_parent_br_id[parent_br_id]

        blocks.append({
            'breakdown_id': parent_br_id,
            'rows': rows,
            'totals': {},
            'pagination': {
                'offset': offset,
                'limit': len(rows),  # TODO count current
                'count': -1,  # TODO count all
            },
        })

    return blocks


def get_report_through_table(get_fn, user, form_data, **kwargs):
    """
    FIXME: This code is temporary! It will only be used for the prototype.

    Reuses the the table.py ofr base level breakdowns.
    Base breakdown is always 'account'
    """

    constraints = extract_constraints(form_data)

    start_date = constraints['date__gte']
    end_date = constraints['date__lte']

    filtered_sources = constraints.get('source')

    offset = form_data.get('offset', DEFAULT_OFFSET)
    limit = form_data.get('limit', DEFAULT_LIMIT)

    # this way the whole requested range is fetched, with possibly some extra that is cut off later
    size = limit * 2
    page = int(offset / size) + 1
    order = form_data.get('order')

    show_archived = form_data.get('show_archived', False)

    response = get_fn(
        user,
        filtered_sources,
        start_date,
        end_date,
        order,
        page,
        size,
        show_archived,
        **kwargs
    )

    # only take rows from limit
    rows = response['rows'][offset:offset + limit]
    return [{
        'breakdown_id': None,
        'rows': rows,
        'totals': response['totals'],
        'pagination': {
            'offset': offset,  # offset is 0-based
            'limit': len(rows),
            'count': response.get('pagination', {}).get('count'),  # TODO some views dont support pagination
        }
    }]


def get_report_all_accounts_accounts(user, filtered_sources, start_date, end_date,
                                     order, page, size, show_archived,
                                     **kwargs):
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
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    return response


def get_report_account_campaigns(user, filtered_sources, start_date, end_date,
                                 order, page, size, show_archived,
                                 **kwargs):
    response = table.AccountCampaignsTable().get(
        user,
        filtered_sources=filtered_sources,
        start_date=start_date,
        end_date=end_date,
        order=order,
        show_archived=show_archived,
        **kwargs
    )

    for row in response['rows']:
        row['campaign_id'] = int(row['campaign'])
        row['campaign_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['campaign'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    response['pagination'] = {
        'count': len(response['rows'])
    }

    return response


def get_report_campaign_ad_groups(user, filtered_sources, start_date, end_date,
                                  order, page, size, show_archived,
                                  **kwargs):
    response = table.CampaignAdGroupsTable().get(
        user,
        filtered_sources=filtered_sources,
        start_date=start_date,
        end_date=end_date,
        order=order,
        show_archived=show_archived,
        **kwargs
    )

    for row in response['rows']:
        row['ad_group_id'] = int(row['ad_group'])
        row['ad_group_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['ad_group'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    response['pagination'] = {
        'count': len(response['rows'])
    }

    return response


def get_report_ad_group_content_ads(user, filtered_sources, start_date, end_date,
                                    order, page, size, show_archived,
                                    **kwargs):
    response = table.AdGroupAdsTable().get(
        user,
        filtered_sources=filtered_sources,
        start_date=start_date,
        end_date=end_date,
        order=order,
        show_archived=show_archived,
        page=page,
        size=size,
        ad_group_id=kwargs['ad_group_id']
    )

    for row in response['rows']:
        row['content_ad_id'] = int(row['id'])
        row['content_ad_name'] = row['title']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['content_ad'], row)
        row['breakdown_name'] = row['title']
        row['parent_breakdown_id'] = None

    return response


def get_report_all_accounts_sources(user, filtered_sources, start_date, end_date,
                                    order, page, size, show_archived,
                                    **kwargs):
    response = table.SourcesTable().get(
        user,
        'all_accounts',
        filtered_sources,
        start_date,
        end_date,
        order
    )

    for row in response['rows']:
        row['source_id'] = int(row['id'])
        row['source_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['source'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    return response


def get_report_account_sources(user, filtered_sources, start_date, end_date,
                               order, page, size, show_archived,
                               **kwargs):
    response = table.SourcesTable().get(
        user,
        'accounts',
        filtered_sources,
        start_date,
        end_date,
        order,
        id_=kwargs['account_id']
    )

    for row in response['rows']:
        row['source_id'] = int(row['id'])
        row['source_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['source'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    return response


def get_report_campaign_sources(user, filtered_sources, start_date, end_date,
                                order, page, size, show_archived,
                                **kwargs):
    response = table.SourcesTable().get(
        user,
        'campaigns',
        filtered_sources,
        start_date,
        end_date,
        order,
        id_=kwargs['campaign_id']
    )

    for row in response['rows']:
        row['source_id'] = int(row['id'])
        row['source_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['source'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    return response


def get_report_ad_group_sources(user, filtered_sources, start_date, end_date,
                                order, page, size, show_archived,
                                **kwargs):
    response = table.SourcesTable().get(
        user,
        'ad_groups',
        filtered_sources,
        start_date,
        end_date,
        order,
        id_=kwargs['ad_group_id']
    )

    for row in response['rows']:
        row['source_id'] = int(row['id'])
        row['source_name'] = row['name']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['source'], row)
        row['breakdown_name'] = row['name']
        row['parent_breakdown_id'] = None

    return response


def get_report_ad_group_publishers(user, filtered_sources, start_date, end_date,
                                   order, page, size, show_archived,
                                   **kwargs):
    response = table.PublishersTable().get(
        user,
        'ad_groups',
        filtered_sources,
        kwargs['show_blacklisted_publishers'],
        start_date,
        end_date,
        order,
        page,
        size,
        id_=kwargs['ad_group_id']
    )

    for row in response['rows']:
        row['publisher'] = row['domain']
        row['publisher_name'] = row['domain']
        row['breakdown_id'] = stats.helpers.create_breakdown_id(['publisher'], row)
        row['breakdown_name'] = row['domain']
        row['parent_breakdown_id'] = None

    return response


class AllAccountsBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.ACCOUNT: get_report_all_accounts_accounts,
            stats.constants.StructureDimension.SOURCE: get_report_all_accounts_sources,
        }[base_dimension]

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
        breakdown_page = form.cleaned_data.get('breakdown_page', None)

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(
                self._get_workaround_fn(stats.constants.get_base_dimension(breakdown)),
                request.user,
                form.cleaned_data
            )
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data),
            breakdown_page,
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit, breakdown_page)
        return self.create_api_response(report)


class AccountBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.CAMPAIGN: get_report_account_campaigns,
            stats.constants.StructureDimension.SOURCE: get_report_account_sources,
        }[base_dimension]

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
        breakdown = form.cleaned_data.get('breakdown')
        breakdown_page = form.cleaned_data.get('breakdown_page', None)

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(
                self._get_workaround_fn(stats.constants.get_base_dimension(breakdown)),
                request.user,
                form.cleaned_data,
                account_id=account.id
            )
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, account=account),
            breakdown_page,
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit, breakdown_page)
        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.AD_GROUP: get_report_campaign_ad_groups,
            stats.constants.StructureDimension.SOURCE: get_report_campaign_sources,
        }[base_dimension]

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
        breakdown = form.cleaned_data.get('breakdown')
        breakdown_page = form.cleaned_data.get('breakdown_page', None)

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(
                self._get_workaround_fn(stats.constants.get_base_dimension(breakdown)),
                request.user,
                form.cleaned_data,
                campaign_id=campaign.id
            )
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, campaign=campaign),
            breakdown_page,
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit, breakdown_page)
        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.CONTENT_AD: get_report_ad_group_content_ads,
            stats.constants.StructureDimension.SOURCE: get_report_ad_group_sources,
            stats.constants.StructureDimension.PUBLISHER: get_report_ad_group_publishers,
        }[base_dimension]

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
        breakdown = form.cleaned_data.get('breakdown')
        breakdown_page = form.cleaned_data.get('breakdown_page', None)

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(
                self._get_workaround_fn(stats.constants.get_base_dimension(breakdown)),
                request.user,
                form.cleaned_data,
                ad_group_id=ad_group.id,
                show_blacklisted_publishers=form.cleaned_data.get('show_blacklisted_publishers'),
            )
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, ad_group=ad_group),
            breakdown_page,
            form.cleaned_data.get('order', None),
            offset,
            limit,
        )

        report = format_breakdown_response(report, offset, limit, breakdown_page)
        return self.create_api_response(report)
