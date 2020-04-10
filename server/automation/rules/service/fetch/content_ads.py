from typing import Dict
from typing import Sequence
from typing import Union

from django.db.models import F

import core.models

from ... import constants
from . import helpers


def prepare_content_ad_settings(
    ad_groups: Sequence[core.models.AdGroup],
) -> Dict[int, Dict[int, Dict[str, Union[int, str]]]]:
    content_ad_annotate_mappings = _prepare_content_ad_annotations()
    content_ad_settings_qs = (
        core.models.ContentAd.objects.filter(ad_group__in=ad_groups)
        .annotate(content_ad_id=F("id"), **content_ad_annotate_mappings)
        .values("ad_group_id", "content_ad_id", *content_ad_annotate_mappings.keys())
    )
    settings_by_ad_group_id_by_content_ad_id: Dict[int, Dict[int, Dict[str, Union[int, str]]]] = {}
    for el in content_ad_settings_qs:
        settings_by_ad_group_id_by_content_ad_id.setdefault(el["ad_group_id"], {})
        settings_by_ad_group_id_by_content_ad_id[el["ad_group_id"]][el["content_ad_id"]] = el
    return settings_by_ad_group_id_by_content_ad_id


def _prepare_content_ad_annotations():
    metric_mappings = {
        constants.MetricType.AD_TITLE: F("title"),
        constants.MetricType.AD_LABEL: F("label"),
        constants.MetricType.AD_CREATED_DATE: helpers.cast_datetime_field_to_date("created_dt"),
        constants.MetricType.DAYS_SINCE_AD_CREATED: helpers.get_days_since_created_field("created_dt"),
    }
    annotate_mappings = helpers.map_keys_from_constant_to_qs_string_representation(metric_mappings)
    return annotate_mappings
