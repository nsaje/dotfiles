import collections
import json
from functools import partial

from dash import constants
from dash import forms
from dash import table
from dash import campaign_goals
from dash import threads
from dash.views import helpers
from dash.views import grid
from dash.views import breakdown_helpers

from utils import api_common
from utils import exc
from utils import sort_helper

import stats.api_breakdowns
import stats.helpers
import stats.constants


DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 10
REQUEST_LIMIT_OVERFLOW = 1  # [workaround] Request additional rows to check if more data is available


def get_constraints_kwargs(form_data, **overrides):
    kwargs = {
        'start_date': form_data['start_date'],
        'end_date': form_data['end_date'],
        'filtered_sources': form_data['filtered_sources'],
        'show_archived': form_data.get('show_archived'),
    }

    if form_data.get('filtered_agencies'):
        kwargs['filtered_agencies'] = form_data.get('filtered_agencies')

    if form_data.get('filtered_account_types'):
        kwargs['filtered_account_types'] = form_data.get('filtered_account_types')

    for k, v in overrides.items():
        kwargs[k] = v

    return kwargs


def format_breakdown_response(report_rows, offset, limit, parents, totals=None, goals=None):
    blocks = []

    if parents:
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
    else:
        blocks = [{
            'breakdown_id': None,
            'rows': report_rows,
            'totals': totals,
            'pagination': {
                'offset': offset,
                'limit': len(report_rows),  # TODO count current
                'count': -1,  # TODO count all
            },
        }]

        if goals and goals.conversion_goals:
            blocks[0]['conversion_goals'] = helpers.get_conversion_goals_wo_pixels(goals.conversion_goals)

        if goals and goals.pixels:
            blocks[0]['pixels'] = helpers.get_pixels_list(goals.pixels)

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

    start_date = form_data['start_date']
    end_date = form_data['end_date']

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


def get_report_ad_group_content_ads(user, filtered_sources, start_date, end_date,
                                    order, page, size, show_archived,
                                    **kwargs):
    prefix, order_field = sort_helper.dissect_order(order)
    if order_field == 'name':
        order_field = 'title'
    elif order_field in ('status', 'state', 'status_setting'):
        order_field = 'status_setting'

    order = prefix + order_field

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
        base_dim = stats.constants.get_base_dimension(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.api_breakdowns.prepare_all_accounts_constraints(
            request.user, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))

        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            constraints = stats.api_breakdowns.prepare_all_accounts_constraints(
                request.user, breakdown, only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, constraints, goals
            )
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.result

        report = format_breakdown_response(rows, offset, limit + REQUEST_LIMIT_OVERFLOW, parents, totals, goals=goals)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)

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
        breakdown = form.cleaned_data.get('breakdown')
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.ACCOUNTS
        base_dim = stats.constants.get_base_dimension(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.api_breakdowns.prepare_account_constraints(
            request.user, account, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            constraints = stats.api_breakdowns.prepare_account_constraints(
                request.user, account, breakdown,
                only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, constraints, goals
            )
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.result

        report = format_breakdown_response(rows, offset, limit + REQUEST_LIMIT_OVERFLOW, parents, totals, goals=goals)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)

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
        breakdown = form.cleaned_data.get('breakdown')
        parents = form.cleaned_data.get('parents', None)
        level = constants.Level.CAMPAIGNS
        base_dim = stats.constants.get_base_dimension(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.api_breakdowns.prepare_campaign_constraints(
            request.user, campaign, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            constraints = stats.api_breakdowns.prepare_campaign_constraints(
                request.user, campaign, breakdown, only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, constraints, goals)
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        if breakdown == ['ad_group_id']:
            breakdown_helpers.format_report_rows_ad_group_editable_fields(rows)

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.result

        report = format_breakdown_response(rows, offset, limit + REQUEST_LIMIT_OVERFLOW, parents, totals, goals=goals)
        if len(breakdown) == 1 and request.user.has_perm('zemauth.campaign_goal_optimization'):
            report[0]['campaign_goals'] = campaign_goals.get_campaign_goals(
                campaign, report[0].get('conversion_goals', []))

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
        base_dim = stats.constants.get_base_dimension(breakdown)

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

        constraints = stats.api_breakdowns.prepare_ad_group_constraints(
            request.user, ad_group, breakdown,
            only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get('order', None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals)
        breakdown_helpers.clean_non_relevant_fields(rows)

        report = format_breakdown_response(rows, offset, limit + REQUEST_LIMIT_OVERFLOW, parents)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
        return self.create_api_response(report)
