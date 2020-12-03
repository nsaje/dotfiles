import collections

import dash.campaign_goals
from core.models import all_rtb
from dash import constants
from dash.views import helpers


"""
Helper functions that transform breakdown responses into what frontend expects.
"""


def format_report_rows_state_fields(rows):
    for row in rows:
        if "status" in row:
            status = {"value": row["status"]}
            if "notifications" in row:
                status["popover_message"] = row["notifications"].get("message")
                status["important"] = row["notifications"].get("important")
            row["status"] = status

        if "state" in row:
            row["state"] = {"value": row["state"]}


def format_report_rows_performance_fields(rows, goals, currency):
    map_values = {x.campaign_goal_id: x for x in (goals.campaign_goal_values or [])}

    campaign_goals_by_campaign_id = collections.defaultdict(list)
    for campaign_goal in goals.campaign_goals:
        campaign_goals_by_campaign_id[campaign_goal.campaign_id].append(campaign_goal)

    rows_by_campaign_id = collections.defaultdict(list)
    for row in rows:
        if row.get("campaign_id"):
            rows_by_campaign_id[row["campaign_id"]].append(row)

    if len(list(campaign_goals_by_campaign_id.keys())) > 1 and len(list(rows_by_campaign_id.keys())) < 1:
        # in case we have data for multiple campaigns but we couldn't separate rows by campaigns
        # then don't add performance info
        return

    for campaign_id, campaign_goals in list(campaign_goals_by_campaign_id.items()):
        primary_goal = next((x for x in goals.primary_goals if x.campaign_id == campaign_id), None)
        primary_goal_key = None
        performance_prefix = None
        if primary_goal:
            performance_prefix = "etfm_performance_"
            primary_goal_key = performance_prefix + primary_goal.get_view_key()

        for row in rows_by_campaign_id[campaign_id] if rows_by_campaign_id else rows:

            # user rights for performance were already checked in the stats module
            # here just add additional formatting if keys are present
            if any(x for x in list(row.keys()) if x.startswith(performance_prefix)):
                row.update({"performance": {"overall": None, "list": []}, "styles": {}})

                if primary_goal_key and primary_goal_key in row:
                    row["performance"]["overall"] = dash.campaign_goals.STATUS_TO_EMOTICON_MAP[row[primary_goal_key]]

                goals_performances = []
                for goal in campaign_goals:
                    metric = dash.campaign_goals.get_goal_performance_metric(goal, goals.conversion_goals)

                    metric_value = row.get(metric)

                    goals_performances.append(
                        (
                            row.get(performance_prefix + goal.get_view_key()),
                            metric_value,
                            map_values.get(goal.id) and map_values[goal.id].local_value,
                            goal,
                        )
                    )

                set_row_goal_performance_meta(row, goals_performances, goals.conversion_goals, currency)


def format_report_rows_ad_group_editable_fields(rows):
    for row in rows:
        row["editable_fields"] = get_ad_group_editable_fields(row, row["campaign_has_available_budget"])


def format_report_rows_content_ad_editable_fields(rows):
    for row in rows:
        submission_states = []

        for _, source_status in list(row.get("status_per_source", {}).items()):

            source_status_text = ""
            if (
                "source_status" in source_status
                and source_status["source_status"] != constants.AdGroupSourceSettingsState.ACTIVE
            ):
                source_status_text = "(paused)"

            submission_status = source_status["submission_status"]
            submission_errors = source_status["submission_errors"]

            text = constants.ContentAdSubmissionStatus.get_text(submission_status)
            if submission_status == constants.ContentAdSubmissionStatus.REJECTED and submission_errors is not None:
                text = "{} ({})".format(text, submission_errors)

            state = {
                "name": source_status["source_name"],
                "status": source_status["submission_status"],
                "source_state": source_status_text,
                "text": text,
            }
            if "source_link" in source_status:
                state["source_link"] = source_status["source_link"]

            submission_states.append(state)

        row.update(
            {
                "id": row["content_ad_id"],
                "submission_status": submission_states,
                "editable_fields": {
                    "state": {"enabled": True, "message": None},
                    "bid_modifier": {"enabled": True, "message": None},
                },
            }
        )


def set_row_goal_performance_meta(row, goals_performances, conversion_goals, currency):
    for goal_status, goal_metric, goal_value, goal in goals_performances:
        performance_item = {
            "emoticon": dash.campaign_goals.STATUS_TO_EMOTICON_MAP.get(goal_status, constants.Emoticon.NEUTRAL),
            "text": dash.campaign_goals.format_campaign_goal(goal.type, goal_metric, goal.conversion_goal, currency),
        }

        if goal_value:
            performance_item["text"] += " (planned {})".format(
                dash.campaign_goals.format_value(goal.type, goal_value, currency)
            )

        row["performance"]["list"].append(performance_item)

        # with_local_prefix=False because client expects colored_column to not have local_ prefix
        primary_metric_map = dash.campaign_goals.get_goal_to_primary_metric_map(with_local_prefix=False)
        colored_column = primary_metric_map.get(goal.type)
        if goal.type == constants.CampaignGoalKPI.CPA:
            colored_column = "avg_etfm_cost_per_" + goal.conversion_goal.get_view_key(conversion_goals)

        if not colored_column:
            continue

        if goal_status == constants.CampaignGoalPerformance.SUPERPERFORMING:
            row["styles"][colored_column] = constants.Emoticon.HAPPY
        elif goal_status == constants.CampaignGoalPerformance.UNDERPERFORMING:
            row["styles"][colored_column] = constants.Emoticon.SAD


def get_ad_group_editable_fields(row, has_available_budget):
    state = {"enabled": True, "message": None}
    if row["state"] == constants.AdGroupSettingsState.INACTIVE and not has_available_budget:
        state["enabled"] = False
        state["message"] = "Cannot enable ad group without available budget."

    return {"state": state}


def clean_non_relevant_fields(rows):
    for row in rows:
        row.pop("campaign_has_available_budget", None)
        row.pop("status_per_source", None)
        row.pop("notifications", None)


def get_upload_batches_response_list(upload_batches):
    upload_batches = upload_batches.order_by("-created_dt")
    return list(upload_batches.values("id", "name"))


def get_ad_group_sources_extras(ad_group):
    return {
        "enabling_autopilot_sources_allowed": ad_group.campaign.account.agency_uses_realtime_autopilot()
        or helpers.enabling_autopilot_single_source_allowed(ad_group),
        "ad_group_autopilot_state": ad_group.settings.autopilot_state,
        "campaign_autopilot": ad_group.campaign.settings.autopilot,
    }


# MVP for all-RTB-sources-as-one
def create_all_rtb_source_row(request, constraints):
    ad_group = constraints["ad_group"]
    settings = ad_group.get_current_settings()
    if not settings.b1_sources_group_enabled:
        return

    rtb_source_ids = (
        constraints["filtered_sources"].filter(source_type__type=constants.SourceType.B1).values_list("id", flat=True)
    )
    rtb_source_ids = list(map(str, rtb_source_ids))

    # Create All RTB Source row using rtb_source_ids for newly created group
    all_rtb_source_row = create_all_rtb_source_row_data(request, ad_group, settings)
    all_rtb_source_row["group"] = {"ids": rtb_source_ids}
    return all_rtb_source_row


def create_all_rtb_source_row_data(request, ad_group, ad_group_settings):
    status = {"value": ad_group_settings.b1_sources_group_state}
    notifications = {}
    if (
        ad_group_settings.state == constants.AdGroupSettingsState.INACTIVE
        and status["value"] == constants.AdGroupSourceSettingsState.ACTIVE
    ):
        status["value"] = constants.AdGroupSourceSettingsState.INACTIVE
        status["popover_message"] = "RTB Sources are enabled but will not run until " "you enable ad group."
        status["important"] = True

    campaign_settings = ad_group.campaign.get_current_settings()

    state_edit_enabled = True
    state_edit_message = None

    daily_budget_edit_enabled = True
    daily_budget_edit_message = None
    if (
        not ad_group.campaign.account.agency_uses_realtime_autopilot()
        and ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    ):
        daily_budget_edit_enabled = False
        daily_budget_edit_message = "This setting cannot be edited and will soon be deprecated. To adjust Ad group’s daily budget, please navigate to ad group settings."
    if campaign_settings.autopilot or (
        ad_group.campaign.account.agency_uses_realtime_autopilot() and ad_group.settings.b1_sources_group_enabled
    ):
        daily_budget_edit_enabled = False
        daily_budget_edit_message = "This setting cannot be edited and will soon be deprecated. To adjust Ad group’s daily budget, please navigate to ad group settings."

    bid_edit_enabled = True
    bid_edit_message = None
    if ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE:
        bid_edit_enabled = False
        bid_edit_message = "This setting cannot be edited and will soon be deprecated. To adjust Ad group’s daily budget, please navigate to ad group settings."
    if campaign_settings.autopilot:
        bid_edit_enabled = False
        bid_edit_message = "This setting cannot be edited and will soon be deprecated. To adjust Ad group’s daily budget, please navigate to ad group settings."

    return {
        "breakdown_name": all_rtb.AllRTBSource.name,
        "breakdown_id": all_rtb.AllRTBSource.id,
        "state": {"value": ad_group_settings.b1_sources_group_state},
        "status": status,
        "daily_budget": ad_group_settings.local_b1_sources_group_daily_budget,
        "bid_cpc": ad_group_settings.local_b1_sources_group_cpc_cc,
        "bid_cpm": ad_group_settings.local_b1_sources_group_cpm,
        "notifications": notifications,
        "editable_fields": {
            "state": {"message": state_edit_message, "enabled": state_edit_enabled},
            "daily_budget": {"message": daily_budget_edit_message, "enabled": daily_budget_edit_enabled},
            "bid_cpc": {"message": bid_edit_message, "enabled": bid_edit_enabled},
            "bid_cpm": {"message": bid_edit_message, "enabled": bid_edit_enabled},
        },
    }
