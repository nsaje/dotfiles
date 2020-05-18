import datetime

from dash import constants as dash_constants
from dash import models
from stats import constants
from stats import fields
from stats import helpers


def augment(breakdown, rows):
    target_dimension = constants.get_target_dimension(breakdown)

    # TODO not fully supported, value is wrong
    remove_status = breakdown == ["content_ad_id", "source_id"] or breakdown == ["source_id", "content_ad_id"]

    target_dimension_mapping = get_target_dimension_mapping(target_dimension)
    augment_target_dimension_mapping(target_dimension_mapping, target_dimension, rows)

    for row in rows:
        row["breakdown_id"] = helpers.encode_breakdown_id(breakdown, row)
        row["parent_breakdown_id"] = (
            helpers.encode_breakdown_id(constants.get_parent_breakdown(breakdown), row) if breakdown else None
        )

        if target_dimension in constants.DeliveryDimension._ALL:
            _augment_row_delivery(row, target_dimension, target_dimension_mapping)

        if target_dimension in constants.TimeDimension._ALL:
            _augment_row_time(row, target_dimension)

        if "placement_type" in row:
            augment_placement_type(row)

        row["breakdown_name"] = row["name"]

        if remove_status:
            row.pop("status", None)
            row.pop("state", None)


def cleanup(rows, target_dimension, constraints):
    to_remove = []

    # remove rows of deprecated sources without stats
    if target_dimension == "source_id":
        deprecated_source_ids = list(
            constraints["filtered_sources"].filter(deprecated=True).values_list("pk", flat=True)
        )
        if deprecated_source_ids:
            for row in rows:
                if (
                    row["source_id"] in deprecated_source_ids
                    and not _has_traffic_data(row)
                    and not _has_postclick_data(row)
                    and not _has_conversion_goal_data(row)
                ):
                    to_remove.append(row)

    for row in to_remove:
        rows.remove(row)


def get_target_dimension_mapping(target_dimension):
    mapping = {
        constants.DeliveryDimension.DEVICE: dash_constants.DeviceType,
        constants.DeliveryDimension.DEVICE_OS: dash_constants.OperatingSystem,
        constants.DeliveryDimension.ENVIRONMENT: dash_constants.Environment,
        constants.DeliveryDimension.ZEM_PLACEMENT_TYPE: dash_constants.ZemPlacementType,
        constants.DeliveryDimension.VIDEO_PLAYBACK_METHOD: dash_constants.VideoPlaybackMethod,
        constants.DeliveryDimension.COUNTRY: dash_constants.AdTargetLocation,
        constants.DeliveryDimension.REGION: dash_constants.AdTargetLocation,
        constants.DeliveryDimension.DMA: dash_constants.AdTargetLocation,
        constants.DeliveryDimension.AGE: dash_constants.Age,
        constants.DeliveryDimension.GENDER: dash_constants.Gender,
        constants.DeliveryDimension.AGE_GENDER: dash_constants.AgeGender,
    }.get(target_dimension)

    if mapping is not None:
        mapping = mapping._VALUES.copy()

    return mapping


def augment_target_dimension_mapping(target_dimension_mapping, target_dimension, rows):
    if target_dimension in (
        constants.DeliveryDimension.COUNTRY,
        constants.DeliveryDimension.REGION,
        constants.DeliveryDimension.DMA,
    ):
        geolocation_keys = [row[target_dimension] for row in rows if row[target_dimension] is not None]
        geolocation_mapping = {
            record["key"]: record["name"]
            for record in models.Geolocation.objects.filter(key__in=geolocation_keys).values("key", "name")
        }
        target_dimension_mapping.update(geolocation_mapping)


def _augment_row_delivery(row, target_dimension, target_dimension_mapping):
    if target_dimension_mapping is not None:
        value = row[target_dimension]
        if target_dimension == constants.DeliveryDimension.DMA:
            value = str(value) if value else None

        row["name"] = target_dimension_mapping.get(value) or value or constants.NOT_REPORTED

    else:
        row["name"] = row.get(target_dimension) or constants.NOT_REPORTED  # when we don't have a designated mapping


def augment_placement_type(row):
    row["placement_type"] = dash_constants.PlacementType.human_readable(row["placement_type"])


def _augment_row_time(row, target_dimension):
    if target_dimension == constants.TimeDimension.DAY:
        date = row[constants.TimeDimension.DAY]
        row["name"] = date.isoformat()

    if target_dimension == constants.TimeDimension.WEEK:
        date = row[constants.TimeDimension.WEEK]
        row["name"] = "Week {} - {}".format(date.isoformat(), (date + datetime.timedelta(days=6)).isoformat())

    if target_dimension == constants.TimeDimension.MONTH:
        date = row[constants.TimeDimension.MONTH]
        row["name"] = date.strftime("%B/%Y")


def _has_traffic_data(row):
    return any(row.get(field) is not None for field in fields.TRAFFIC_FIELDS)


def _has_postclick_data(row):
    return any(
        row.get(field) is not None for field in fields.POSTCLICK_ACQUISITION_FIELDS | fields.POSTCLICK_ENGAGEMENT_FIELDS
    )


def _has_conversion_goal_data(row):
    return any(k.startswith("conversion_goal_") and v > 0 for k, v in row.items())
