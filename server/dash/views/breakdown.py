import collections
import json
from functools import partial

import newrelic.agent

from dash import constants
from dash import forms
from dash import campaign_goals
from dash import threads
from dash import publisher_helpers
from dash.views import helpers
from dash.views import breakdown_helpers

from utils import api_common
from utils import exc

import stats.api_breakdowns
import stats.constraints_helper
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

    if form_data.get('show_blacklisted_publishers'):
        kwargs['show_blacklisted_publishers'] = form_data['show_blacklisted_publishers']

    for k, v in overrides.items():
        kwargs[k] = v

    return kwargs


def format_breakdown_response(report_rows, offset, limit, parents, totals=None, goals=None, **extras):
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

        if goals and goals.conversion_goals is not None:
            blocks[0]['conversion_goals'] = helpers.get_conversion_goals_wo_pixels(goals.conversion_goals)

        if goals and goals.pixels is not None:
            blocks[0]['pixels'] = helpers.get_pixels_list(goals.pixels)

        blocks[0].update(extras)

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


class AllAccountsBreakdown(api_common.BaseApiView):

    @newrelic.agent.function_trace()
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

        constraints = stats.constraints_helper.prepare_all_accounts_constraints(
            request.user, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))

        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_all_accounts_constraints(
                request.user, breakdown, only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, totals_constraints, goals
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

    @newrelic.agent.function_trace()
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

        constraints = stats.constraints_helper.prepare_account_constraints(
            request.user, account, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_account_constraints(
                request.user, account, breakdown,
                only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, totals_constraints, goals
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

    @newrelic.agent.function_trace()
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

        constraints = stats.constraints_helper.prepare_campaign_constraints(
            request.user, campaign, breakdown, only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_campaign_constraints(
                request.user, campaign, breakdown, only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, totals_constraints, goals)
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

    @newrelic.agent.function_trace()
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

        constraints = stats.constraints_helper.prepare_ad_group_constraints(
            request.user, ad_group, breakdown,
            only_used_sources=base_dim == 'source_id',
            **get_constraints_kwargs(form.cleaned_data))
        goals = stats.api_breakdowns.get_goals(constraints)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_ad_group_constraints(
                request.user, ad_group, breakdown, only_used_sources=(base_dim == 'source_id'),
                **get_constraints_kwargs(form.cleaned_data, show_archived=True))
            totals_fn = partial(
                stats.api_breakdowns.totals,
                request.user, level, breakdown, totals_constraints, goals)
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

        if breakdown == ['content_ad_id']:
            breakdown_helpers.format_report_rows_content_ad_editable_fields(rows)

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.result

        extras = {}
        if base_dim == 'content_ad_id':
            batches = helpers.get_upload_batches_for_ad_group(ad_group)
            extras['batches'] = breakdown_helpers.get_upload_batches_response_list(batches)

        if base_dim == 'source_id':
            extras.update(breakdown_helpers.get_ad_group_sources_extras(ad_group))

        if stats.constants.get_target_dimension(breakdown) == 'publisher_id':
            extras['ob_blacklisted_count'] = publisher_helpers.get_ob_blacklisted_publishers_count(
                ad_group.campaign.account_id)

        report = format_breakdown_response(rows, offset, limit + REQUEST_LIMIT_OVERFLOW, parents, totals, goals,
                                           **extras)
        if len(breakdown) == 1 and request.user.has_perm('zemauth.campaign_goal_optimization'):
            report[0]['campaign_goals'] = campaign_goals.get_campaign_goals(
                ad_group.campaign, report[0].get('conversion_goals', []))

        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
        return self.create_api_response(report)
