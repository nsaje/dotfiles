import collections
import json

from dash import constants
from dash import forms
from dash import table
from dash.views import helpers
from dash.views import grid

from utils import api_common
from utils import exc

import stats.api_breakdowns
import stats.helpers
import stats.constants


DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 10
REQUEST_LIMIT_OVERFLOW = 1  # [workaround] Request additional rows to check if more data is available


def extract_constraints(form_data, account=None, campaign=None, ad_group=None):
    # TODO rename date_gte and date_lte to start_date and end_date
    constraints = {
        'date__gte': form_data['start_date'],
        'date__lte': form_data['end_date'],
        'filtered_sources': form_data['filtered_sources'],
        'show_archived': form_data.get('show_archived'),
    }

    if form_data.get('filtered_agencies'):
        constraints['filtered_agencies'] = form_data['filtered_agencies']

    if form_data.get('filtered_account_types'):
        constraints['filtered_account_types'] = form_data['filtered_account_types']

    if account:
        constraints['account'] = account

    if campaign:
        constraints['campaign'] = campaign

    if ad_group:
        constraints['ad_group'] = ad_group

    return constraints


def format_breakdown_response(report_rows, offset, limit, parents):
    blocks = []

    # map rows by parent breakdown ids
    rows_by_parent_br_id = collections.defaultdict(list)
    for row in report_rows:
        rows_by_parent_br_id[row['parent_breakdown_id']].append(row)

    # create blocks for every parent
    for parent in parents:
        rows = rows_by_parent_br_id[parent]

        blocks.append({
            'breakdown_id': parent,
            'rows': rows,
            'totals': {},
            'pagination': {
                'offset': offset,
                'limit': len(rows),  # TODO count current
                'count': -1,  # TODO count all
            },
        })

    return blocks


def _process_request_overflow(blocks, limit, overflow):
    # FIXME: This is workaround to find out if additional data can be requested by clients
    # We request more data then required by client to check if breakdown collection is complete
    # At the end all overflow data is removed and pagination limit updated
    for block in blocks:
        pagination = block['pagination']
        if pagination['limit'] < limit + overflow:
            pagination['count'] = pagination['offset'] + pagination['limit']

        if pagination['limit'] > limit:
            pagination['limit'] = limit
            block['rows'] = block['rows'][:limit]
    return blocks


def _get_page_and_size(offset, limit):
    # most sure way to get what we want
    page = 1
    size = offset + limit
    return page, size


def get_report_through_table(get_fn, user, form_data, all_accounts_level=False, **kwargs):
    """
    FIXME: This code is temporary! It will only be used for the prototype.

    Reuses the the table.py ofr base level breakdowns.
    Base breakdown is always 'account'
    """

    constraints = extract_constraints(form_data)

    start_date = constraints['date__gte']
    end_date = constraints['date__lte']

    view_filter = helpers.ViewFilter(user=user, data=form_data)
    filtered_sources = view_filter.filtered_sources

    offset = form_data.get('offset', DEFAULT_OFFSET)
    limit = form_data.get('limit', DEFAULT_LIMIT)

    page, size = _get_page_and_size(offset, limit)
    order = form_data.get('order')

    show_archived = form_data.get('show_archived', False)

    response = get_fn(
        user,
        view_filter if all_accounts_level else filtered_sources,
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

    base = {
        'breakdown_id': None,
        'rows': rows,
        'totals': response['totals'],
        'pagination': {
            'offset': offset,  # offset is 0-based
            'limit': len(rows),
            'count': response.get('pagination', {}).get('count'),  # TODO some views dont support pagination
        }
    }

    if 'campaign_goals' in response:
        base['campaign_goals'] = response['campaign_goals']

    if 'conversion_goals' in response:
        base['conversion_goals'] = response['conversion_goals']

    if 'pixels' in response:
        base['pixels'] = response['pixels']

    if 'enabling_autopilot_sources_allowed' in response:
        base['enabling_autopilot_sources_allowed'] = response['enabling_autopilot_sources_allowed']

    if 'ad_group_autopilot_state' in response:
        base['ad_group_autopilot_state'] = response['ad_group_autopilot_state']

    if 'batches' in response:
        base['batches'] = response['batches']

    if 'ob_blacklisted_count' in response:
        base['ob_blacklisted_count'] = response['ob_blacklisted_count']

    return [base]


def get_report_all_accounts_accounts(user, view_filter, start_date, end_date,
                                     order, page, size, show_archived,
                                     **kwargs):
    response = table.AccountsAccountsTable().get(
        user,
        view_filter,
        start_date,
        end_date,
        order,
        page,
        size,
        show_archived
    )
    return grid.convert_resource_response(constants.Level.ALL_ACCOUNTS, 'account_id', response)


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
    response['pagination'] = {
        'count': len(response['rows'])
    }
    return grid.convert_resource_response(constants.Level.ACCOUNTS, 'campaign_id', response)


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

    response['pagination'] = {
        'count': len(response['rows'])
    }
    return grid.convert_resource_response(constants.Level.CAMPAIGNS, 'ad_group_id', response)


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
    return grid.convert_resource_response(constants.Level.AD_GROUPS, 'content_ad_id', response)


def get_report_all_accounts_sources(user, view_filter, start_date, end_date,
                                    order, page, size, show_archived,
                                    **kwargs):
    response = table.SourcesTable().get(
        user,
        'all_accounts',
        view_filter,
        start_date,
        end_date,
        order
    )
    return grid.convert_resource_response(constants.Level.ALL_ACCOUNTS, 'source_id', response)


def get_report_account_sources(user, filtered_sources, start_date, end_date,
                               order, page, size, show_archived,
                               **kwargs):
    view_filter = helpers.ViewFilter()
    view_filter.filtered_sources = filtered_sources

    response = table.SourcesTable().get(
        user,
        'accounts',
        view_filter,
        start_date,
        end_date,
        order,
        id_=kwargs['account_id']
    )
    return grid.convert_resource_response(constants.Level.ACCOUNTS, 'source_id', response)


def get_report_campaign_sources(user, filtered_sources, start_date, end_date,
                                order, page, size, show_archived,
                                **kwargs):
    view_filter = helpers.ViewFilter()
    view_filter.filtered_sources = filtered_sources

    response = table.SourcesTable().get(
        user,
        'campaigns',
        view_filter,
        start_date,
        end_date,
        order,
        id_=kwargs['campaign_id']
    )
    return grid.convert_resource_response(constants.Level.CAMPAIGNS, 'source_id', response)


def get_report_ad_group_sources(user, filtered_sources, start_date, end_date,
                                order, page, size, show_archived,
                                **kwargs):
    view_filter = helpers.ViewFilter()
    view_filter.filtered_sources = filtered_sources

    response = table.SourcesTable().get(
        user,
        'ad_groups',
        view_filter,
        start_date,
        end_date,
        order,
        id_=kwargs['ad_group_id']
    )
    return grid.convert_resource_response(constants.Level.AD_GROUPS, 'source_id', response)


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
    return grid.convert_resource_response(constants.Level.AD_GROUPS, 'publisher', response)


class AllAccountsBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.ACCOUNT: get_report_all_accounts_accounts,
            stats.constants.StructureDimension.SOURCE: get_report_all_accounts_sources,
        }[base_dimension]

    def post(self, request, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature'):
            raise exc.MissingDataError()

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)
        breakdown = form.cleaned_data.get('breakdown')
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.ALL_ACCOUNTS

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        # FIXME redirect to table.py if base level request for a breakdown
        if len(breakdown) == 1:
            report = get_report_through_table(
                self._get_workaround_fn(stats.constants.get_base_dimension(breakdown)),
                request.user,
                form.cleaned_data,
                all_accounts_level=True
            )
            return self.create_api_response(report)

        report = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data),
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        report = format_breakdown_response(report, offset, limit + REQUEST_LIMIT_OVERFLOW, parents)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
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
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.ACCOUNTS

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

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
            level,
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, account=account),
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        report = format_breakdown_response(report, offset, limit + REQUEST_LIMIT_OVERFLOW, parents)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
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
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.CAMPAIGNS

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

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
            level,
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, campaign=campaign),
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        report = format_breakdown_response(report, offset, limit + REQUEST_LIMIT_OVERFLOW, parents)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
        return self.create_api_response(report)


class AdGroupBreakdown(api_common.BaseApiView):

    def _get_workaround_fn(self, base_dimension):
        return {
            stats.constants.StructureDimension.CONTENT_AD: get_report_ad_group_content_ads,
            stats.constants.StructureDimension.SOURCE: get_report_ad_group_sources,
            stats.constants.StructureDimension.PUBLISHER: get_report_ad_group_publishers,
        }[base_dimension]

    def post(self, request, ad_group_id, breakdown):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_feature_on_ad_group_level'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        request_body = json.loads(request.body).get('params')
        form = forms.BreakdownForm(request.user, breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get('offset', DEFAULT_OFFSET)
        limit = form.cleaned_data.get('limit', DEFAULT_LIMIT)
        breakdown = form.cleaned_data.get('breakdown')
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.AD_GROUPS

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

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

        if stats.constants.get_base_dimension(breakdown) == 'publisher':
            breakdown = ['publisher', 'source_id'] + breakdown[1:]

        report = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            extract_constraints(form.cleaned_data, ad_group=ad_group),
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        report = format_breakdown_response(report, offset, limit + REQUEST_LIMIT_OVERFLOW, parents)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
        return self.create_api_response(report)
