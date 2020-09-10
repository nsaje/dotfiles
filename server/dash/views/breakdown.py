import collections
import json
from functools import partial

import newrelic.agent

import core.features.publisher_groups
import stats.api_breakdowns
import stats.constants
import stats.constraints_helper
import stats.helpers
import zemauth.access
from core.features import bid_modifiers
from dash import campaign_goals
from dash import constants
from dash import forms
from dash.common.views_base import DASHAPIBaseView
from dash.views import breakdown_helpers
from dash.views import helpers
from restapi.serializers.bid_modifiers import BidModifierTypeSummary
from utils import exc
from utils import threads
from zemauth.features.entity_permission import Permission

DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 10
REQUEST_LIMIT_OVERFLOW = 1  # [workaround] Request additional rows to check if more data is available
LIMIT_SOURCE = 1000


def get_constraints_kwargs(form_data, **overrides):
    kwargs = {
        "start_date": form_data["start_date"],
        "end_date": form_data["end_date"],
        "filtered_sources": form_data["filtered_sources"],
        "show_archived": form_data.get("show_archived"),
    }

    if form_data.get("filtered_agencies"):
        kwargs["filtered_agencies"] = form_data.get("filtered_agencies")

    if form_data.get("filtered_account_types"):
        kwargs["filtered_account_types"] = form_data.get("filtered_account_types")

    if form_data.get("filtered_businesses"):
        kwargs["filtered_businesses"] = form_data.get("filtered_businesses")

    if form_data.get("show_blacklisted_publishers"):
        kwargs["show_blacklisted_publishers"] = form_data["show_blacklisted_publishers"]

    for k, v in list(overrides.items()):
        kwargs[k] = v

    return kwargs


def format_breakdown_response(report_rows, offset, parents, totals=None, goals=None, **extras):
    blocks = []

    if parents:
        # map rows by parent breakdown ids
        rows_by_parent_br_id = collections.defaultdict(list)
        for row in report_rows:
            rows_by_parent_br_id[row["parent_breakdown_id"]].append(row)

        # create blocks for every parent
        for parent in parents:
            rows = rows_by_parent_br_id[parent]

            blocks.append(
                {
                    "breakdown_id": parent,
                    "rows": rows,
                    "totals": {},
                    "pagination": {
                        "offset": offset,
                        "limit": len(rows),  # TODO count current
                        "count": -1,  # TODO count all
                    },
                }
            )
    else:
        blocks = [
            {
                "breakdown_id": None,
                "rows": report_rows,
                "totals": totals,
                "pagination": {
                    "offset": offset,
                    "limit": len(report_rows),  # TODO count current
                    "count": -1,  # TODO count all
                },
            }
        ]

        if goals and goals.conversion_goals is not None:
            blocks[0]["conversion_goals"] = helpers.get_conversion_goals_wo_pixels(goals.conversion_goals)

        if goals and goals.pixels is not None:
            blocks[0]["pixels"] = helpers.get_pixels_list(goals.pixels)

        blocks[0].update(extras)

    return blocks


def _process_request_overflow(blocks, limit, overflow):
    # FIXME: This is workaround to find out if additional data can be requested by clients
    # We request more data then required by client to check if breakdown collection is complete
    # At the end all overflow data is removed and pagination limit updated
    for block in blocks:
        pagination = block["pagination"]
        if pagination["limit"] < limit + overflow:
            pagination["count"] = pagination["offset"] + pagination["limit"]

        if pagination["limit"] > limit:
            pagination["limit"] = limit
            block["rows"] = block["rows"][:limit]
    return blocks


def _get_page_and_size(offset, limit):
    # most sure way to get what we want
    page = 1
    size = offset + limit
    return page, size


def _get_limit(breakdown, limit):
    target_dimension = stats.constants.get_target_dimension(breakdown)
    if target_dimension == stats.constants.DimensionIdentifierMapping.get(stats.constants.DimensionIdentifier.SOURCE):
        # NOTE: override limit for source breakdown
        return LIMIT_SOURCE
    return limit


class AllAccountsBreakdown(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def post(self, request, breakdown):
        if not request.user.has_perm("zemauth.can_access_table_breakdowns_feature"):
            raise exc.MissingDataError()

        request_body = json.loads(request.body).get("params")
        form = forms.BreakdownForm(breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get("offset", DEFAULT_OFFSET)
        breakdown = form.cleaned_data.get("breakdown")
        limit = _get_limit(breakdown, form.cleaned_data.get("limit", DEFAULT_LIMIT))
        parents = form.cleaned_data.get("parents", None)
        level = constants.Level.ALL_ACCOUNTS
        target_dim = stats.constants.get_target_dimension(breakdown)

        _newrelic_set_breakdown_transaction_name(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        only_used_sources = target_dim == "source_id"
        # HACK(nsaje): don't filter by sources for internal users because it takes too long. Maybe we should reimplement showing
        # only used sources by filtering by allowed_sources? Downside is it would hide sources that used to be allowed but aren't anymore. Maybe we could keep track per account.
        only_used_sources = only_used_sources and not request.user.has_perm("zemauth.can_see_all_accounts")
        constraints = stats.constraints_helper.prepare_all_accounts_constraints(
            request.user, only_used_sources=only_used_sources, **get_constraints_kwargs(form.cleaned_data)
        )

        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_all_accounts_constraints(
                request.user, only_used_sources=False, **get_constraints_kwargs(form.cleaned_data, show_archived=True)
            )
            totals_fn = partial(stats.api_breakdowns.totals, request.user, level, breakdown, totals_constraints, goals)
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get("order", None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.get_result()

        currency = stats.helpers.get_report_currency(request.user, constraints["allowed_accounts"])
        extras = {"currency": currency}
        stats.helpers.update_rows_to_contain_values_in_currency(rows, currency)
        if totals:
            stats.helpers.update_rows_to_contain_values_in_currency([totals], currency)

        report = format_breakdown_response(rows, offset, parents, totals, goals=goals, **extras)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)

        return self.create_api_response(report)


class AccountBreakdown(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def post(self, request, account_id, breakdown):
        if not request.user.has_perm("zemauth.can_access_table_breakdowns_feature"):
            raise exc.AuthorizationError()

        account = zemauth.access.get_account(request.user, Permission.READ, account_id)
        currency = stats.helpers.get_report_currency(request.user, [account])

        request_body = json.loads(request.body).get("params")
        form = forms.BreakdownForm(breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get("offset", DEFAULT_OFFSET)
        breakdown = form.cleaned_data.get("breakdown")
        limit = _get_limit(breakdown, form.cleaned_data.get("limit", DEFAULT_LIMIT))
        parents = form.cleaned_data.get("parents", None)
        level = constants.Level.ACCOUNTS
        target_dim = stats.constants.get_target_dimension(breakdown)

        _newrelic_set_breakdown_transaction_name(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.constraints_helper.prepare_account_constraints(
            request.user,
            account,
            only_used_sources=target_dim == "source_id",
            **get_constraints_kwargs(form.cleaned_data),
        )
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_account_constraints(
                request.user,
                account,
                only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True),
            )
            totals_fn = partial(stats.api_breakdowns.totals, request.user, level, breakdown, totals_constraints, goals)
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get("order", None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals, currency)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.get_result()

        extras = {}
        if stats.constants.get_target_dimension(breakdown) == "publisher_id":
            extras["ob_blacklisted_count"] = core.features.publisher_groups.get_ob_blacklisted_publishers_count(account)

        extras["currency"] = currency
        stats.helpers.update_rows_to_contain_values_in_currency(rows, currency)
        if totals:
            stats.helpers.update_rows_to_contain_values_in_currency([totals], currency)

        report = format_breakdown_response(rows, offset, parents, totals, goals=goals, **extras)
        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)

        return self.create_api_response(report)


class CampaignBreakdown(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def post(self, request, campaign_id, breakdown):
        if not request.user.has_perm("zemauth.can_access_table_breakdowns_feature"):
            raise exc.AuthorizationError()

        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id, select_related=True)

        request_body = json.loads(request.body).get("params")
        form = forms.BreakdownForm(breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get("offset", DEFAULT_OFFSET)
        breakdown = form.cleaned_data.get("breakdown")
        limit = _get_limit(breakdown, form.cleaned_data.get("limit", DEFAULT_LIMIT))
        parents = form.cleaned_data.get("parents", None)
        level = constants.Level.CAMPAIGNS
        target_dim = stats.constants.get_target_dimension(breakdown)

        _newrelic_set_breakdown_transaction_name(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.constraints_helper.prepare_campaign_constraints(
            request.user,
            campaign,
            only_used_sources=target_dim == "source_id",
            **get_constraints_kwargs(form.cleaned_data),
        )
        currency = stats.helpers.get_report_currency(request.user, [constraints["account"]])
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_campaign_constraints(
                request.user,
                campaign,
                only_used_sources=False,
                **get_constraints_kwargs(form.cleaned_data, show_archived=True),
            )
            totals_fn = partial(stats.api_breakdowns.totals, request.user, level, breakdown, totals_constraints, goals)
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get("order", None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        if breakdown == ["ad_group_id"]:
            breakdown_helpers.format_report_rows_ad_group_editable_fields(rows)

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals, currency)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.get_result()

        extras = {}
        if stats.constants.get_target_dimension(breakdown) == "publisher_id":
            extras["ob_blacklisted_count"] = core.features.publisher_groups.get_ob_blacklisted_publishers_count(
                campaign.account
            )

        extras["currency"] = currency
        stats.helpers.update_rows_to_contain_values_in_currency(rows, currency)
        if totals:
            stats.helpers.update_rows_to_contain_values_in_currency([totals], currency)

        report = format_breakdown_response(rows, offset, parents, totals, goals=goals, **extras)
        if len(breakdown) == 1:
            report[0]["campaign_goals"] = campaign_goals.get_campaign_goals(
                campaign, report[0].get("conversion_goals", [])
            )

        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)
        return self.create_api_response(report)


class AdGroupBreakdown(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def post(self, request, ad_group_id, breakdown):
        if not request.user.has_perm("zemauth.can_access_table_breakdowns_feature_on_ad_group_level"):
            raise exc.AuthorizationError()

        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        request_body = json.loads(request.body).get("params")
        form = forms.BreakdownForm(breakdown, request_body)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        offset = form.cleaned_data.get("offset", DEFAULT_OFFSET)
        breakdown = form.cleaned_data.get("breakdown")
        limit = _get_limit(breakdown, form.cleaned_data.get("limit", DEFAULT_LIMIT))
        parents = form.cleaned_data.get("parents", None)
        level = constants.Level.AD_GROUPS
        target_dim = stats.constants.get_target_dimension(breakdown)

        _newrelic_set_breakdown_transaction_name(breakdown)

        stats.api_breakdowns.validate_breakdown_allowed(level, request.user, breakdown)

        constraints = stats.constraints_helper.prepare_ad_group_constraints(
            request.user, ad_group, only_used_sources=True, **get_constraints_kwargs(form.cleaned_data)
        )
        currency = stats.helpers.get_report_currency(request.user, [constraints["account"]])
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        totals_thread = None
        if len(breakdown) == 1:
            totals_constraints = stats.constraints_helper.prepare_ad_group_constraints(
                request.user,
                ad_group,
                only_used_sources=(target_dim == "source_id"),
                **get_constraints_kwargs(form.cleaned_data, show_archived=True),
            )
            totals_fn = partial(stats.api_breakdowns.totals, request.user, level, breakdown, totals_constraints, goals)
            totals_thread = threads.AsyncFunction(totals_fn)
            totals_thread.start()

        rows = stats.api_breakdowns.query(
            level,
            request.user,
            breakdown,
            constraints,
            goals,
            parents,
            form.cleaned_data.get("order", None),
            offset,
            limit + REQUEST_LIMIT_OVERFLOW,
        )

        if breakdown == ["content_ad_id"]:
            breakdown_helpers.format_report_rows_content_ad_editable_fields(rows)

        breakdown_helpers.format_report_rows_state_fields(rows)
        breakdown_helpers.format_report_rows_performance_fields(rows, goals, currency)
        breakdown_helpers.clean_non_relevant_fields(rows)

        totals = None
        if totals_thread is not None:
            totals_thread.join()
            totals = totals_thread.get_result()

        extras = {}
        if breakdown == ["content_ad_id"]:
            batches = helpers.get_upload_batches_for_ad_group(ad_group)
            extras["batches"] = breakdown_helpers.get_upload_batches_response_list(batches)

        if breakdown == ["source_id"]:
            extras.update(breakdown_helpers.get_ad_group_sources_extras(ad_group))

        if stats.constants.get_target_dimension(breakdown) == "publisher_id":
            extras["ob_blacklisted_count"] = core.features.publisher_groups.get_ob_blacklisted_publishers_count(
                ad_group.campaign.account
            )

        bid_modifier_type = stats.constants.TargetDimensionToBidModifierTypeMap.get(target_dim)
        if bid_modifier_type is not None:
            extras["autopilot_state"] = constants.AdGroupSettingsAutopilotState.get_name(
                ad_group.settings.autopilot_state
            )
            extras["bidding_type"] = constants.BiddingType.get_name(ad_group.bidding_type)
            extras["bid"] = (
                ad_group.settings.local_cpc
                if ad_group.bidding_type == constants.BiddingType.CPC
                else ad_group.settings.local_cpm
            )
            extras["type_summaries"] = BidModifierTypeSummary(
                bid_modifiers.get_type_summaries(ad_group.id), many=True
            ).data

        extras["currency"] = currency
        stats.helpers.update_rows_to_contain_values_in_currency(rows, currency)
        if totals:
            stats.helpers.update_rows_to_contain_values_in_currency([totals], currency)

        report = format_breakdown_response(rows, offset, parents, totals, goals, **extras)
        if len(breakdown) == 1:
            report[0]["campaign_goals"] = campaign_goals.get_campaign_goals(
                ad_group.campaign, report[0].get("conversion_goals", [])
            )

        report = _process_request_overflow(report, limit, REQUEST_LIMIT_OVERFLOW)

        # MVP for all-RTB-sources-as-one
        # Append ALL_RTB_SOURCE row at the end of the requested page
        # Frontend REQ: should be present on each page to be able to merge grouped rows
        if breakdown == ["source_id"]:
            all_rtb_source_row = breakdown_helpers.create_all_rtb_source_row(
                request, constraints, request.user.has_perm("zemauth.can_set_rtb_sources_as_one_cpc")
            )
            if all_rtb_source_row:
                report[0]["rows"].append(all_rtb_source_row)

        return self.create_api_response(report)


def _newrelic_set_breakdown_transaction_name(breakdown):
    transaction = newrelic.agent.current_transaction()
    if not transaction:
        return
    new_transaction_name = f"{transaction.name} - {breakdown}"
    newrelic.agent.set_transaction_name(new_transaction_name)
