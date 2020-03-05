from typing import Dict
from typing import Sequence
from typing import Union

from django.db.models import Case
from django.db.models import DateField
from django.db.models import DecimalField
from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models import When
from django.db.models.functions import Cast
from django.db.models.functions import Coalesce
from django.db.models.functions import ExtractDay
from django.db.models.functions import Now

import core.models
import dash.constants

from .. import constants


def prepare_ad_group_settings(
    ad_groups: Sequence[core.models.AdGroup],
    include_campaign_goals: bool = False,
    include_ad_group_daily_cap: bool = False,
) -> Dict[int, Dict[str, Union[int, str]]]:
    annotate_mappings = _prepare_ad_group_settings_annotations(
        include_campaign_goals=include_campaign_goals, include_ad_group_daily_cap=include_ad_group_daily_cap
    )
    ad_group_settings_qs = (
        core.models.AdGroup.objects.filter(id__in=[ag.id for ag in ad_groups])
        .annotate(ad_group_id=F("id"), **annotate_mappings)
        .values("ad_group_id", *annotate_mappings.keys())
    )
    return {el["ad_group_id"]: el for el in ad_group_settings_qs}


def prepare_content_ad_settings(
    ad_groups: Sequence[core.models.AdGroup]
) -> Dict[int, Dict[int, Dict[str, Union[int, str]]]]:
    content_ad_annotate_mappings = _prepare_content_ad_annotations()
    content_ad_settings_qs = (
        core.models.ContentAd.objects.filter(ad_group__in=ad_groups)
        .annotate(content_ad_id=F("id"), **content_ad_annotate_mappings)
        .values("ad_group_id", "content_ad_id", *content_ad_annotate_mappings.keys())
    )
    settings_by_ad_group_by_content_ad: Dict[int, Dict[int, Dict[str, Union[int, str]]]] = {}
    for el in content_ad_settings_qs:
        settings_by_ad_group_by_content_ad.setdefault(el["ad_group_id"], {})
        settings_by_ad_group_by_content_ad[el["ad_group_id"]][el["content_ad_id"]] = el
    return settings_by_ad_group_by_content_ad


def _prepare_content_ad_annotations():
    metric_mappings = {
        constants.MetricType.AD_TITLE: F("title"),
        constants.MetricType.AD_LABEL: F("label"),
        constants.MetricType.AD_CREATED_DATE: _cast_datetime_field_to_date("created_dt"),
        constants.MetricType.DAYS_SINCE_AD_CREATED: _get_days_since_created_field("created_dt"),
    }
    annotate_mappings = _map_keys_from_constant_to_qs_string_representation(metric_mappings)
    return annotate_mappings


def _prepare_ad_group_settings_annotations(*, include_campaign_goals: bool, include_ad_group_daily_cap: bool):
    metric_mappings = {
        constants.MetricType.ACCOUNT_NAME: F("campaign__account__name"),
        constants.MetricType.ACCOUNT_CREATED_DATE: _cast_datetime_field_to_date("campaign__account__created_dt"),
        constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED: _get_days_since_created_field("campaign__account__created_dt"),
        constants.MetricType.CAMPAIGN_NAME: F("campaign__name"),
        constants.MetricType.CAMPAIGN_CREATED_DATE: _cast_datetime_field_to_date("campaign__created_dt"),
        constants.MetricType.DAYS_SINCE_CAMPAIGN_CREATED: _get_days_since_created_field("campaign__created_dt"),
        constants.MetricType.CAMPAIGN_TYPE: F("campaign__type"),
        constants.MetricType.CAMPAIGN_MANAGER: F("campaign__settings__campaign_manager__email"),
        constants.MetricType.CAMPAIGN_CATEGORY: F("campaign__settings__iab_category"),
        constants.MetricType.CAMPAIGN_LANGUAGE: F("campaign__settings__language"),
        constants.MetricType.AD_GROUP_NAME: F("name"),
        constants.MetricType.AD_GROUP_CREATED_DATE: _cast_datetime_field_to_date("created_dt"),
        constants.MetricType.DAYS_SINCE_AD_GROUP_CREATED: _get_days_since_created_field("created_dt"),
        constants.MetricType.AD_GROUP_START_DATE: F("settings__start_date"),
        constants.MetricType.AD_GROUP_END_DATE: F("settings__end_date"),
        constants.MetricType.AD_GROUP_BIDDING_TYPE: F("bidding_type"),
        constants.MetricType.AD_GROUP_BID: _get_ad_group_bid_field(),
        constants.MetricType.AD_GROUP_DELIVERY_TYPE: F("settings__delivery_type"),
    }
    if include_campaign_goals:
        metric_mappings.update(_constuct_campaign_goals_annotations())
    if include_ad_group_daily_cap:
        metric_mappings.update(_construct_ad_group_daily_cap_annotations())
    annotate_mappings = _map_keys_from_constant_to_qs_string_representation(metric_mappings)
    return annotate_mappings


def _construct_ad_group_daily_cap_annotations():
    # NOTE: possible optimization - materialize daily cap
    ad_group_source_caps_subquery = (
        core.models.AdGroupSource.objects.filter(ad_group_id=OuterRef("id"))
        .filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        .filter(Q(ad_group__settings__b1_sources_group_enabled=False) | ~Q(source__source_type__type="b1"))
        .values("ad_group__pk")
        .annotate(daily_cap=Sum("settings__local_daily_budget_cc"))
    )
    return {
        constants.MetricType.AD_GROUP_DAILY_CAP: Case(
            When(settings__b1_sources_group_enabled=True, then=F("settings__local_b1_sources_group_daily_budget")),
            default=0,
        )
        + Coalesce(Subquery(ad_group_source_caps_subquery.values("daily_cap")[:1], output_field=DecimalField()), 0)
    }


def _constuct_campaign_goals_annotations():
    # NOTE: possible optimization - store primary goal fk on campaign itself
    campaign_goals_subquery = core.features.goals.CampaignGoal.objects.filter(
        campaign_id=OuterRef("campaign_id"), primary=True
    )
    campaign_goals_values_subquery = core.features.goals.CampaignGoalValue.objects.filter(
        campaign_goal_id=OuterRef("id")
    ).order_by("-created_dt")
    return {
        constants.MetricType.CAMPAIGN_PRIMARY_GOAL: Subquery(campaign_goals_subquery.values("type")),
        constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE: Subquery(
            campaign_goals_subquery.annotate(
                local_value=Subquery(campaign_goals_values_subquery.values("local_value")[:1])
            )[:1].values("local_value"),
            output_field=DecimalField(),
        ),
    }


def _get_ad_group_bid_field():
    return Case(
        When(bidding_type=dash.constants.BiddingType.CPC, then=F("settings__local_cpc")),
        When(bidding_type=dash.constants.BiddingType.CPM, then=F("settings__local_cpm")),
    )


def _get_days_since_created_field(field):
    return ExtractDay(Cast(Now(), DateField()) - _cast_datetime_field_to_date(field))


def _cast_datetime_field_to_date(field):
    return Cast(field, DateField())


def _map_keys_from_constant_to_qs_string_representation(metric_mappings):
    # NOTE: django expects strings as keys in annotations.
    # They are mapped to descriptive names for clarity.
    return {constants.METRIC_SETTINGS_MAPPING[metric]: field for metric, field in metric_mappings.items()}
