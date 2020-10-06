import csv
import decimal
import io as StringIO
import numbers
import os
import random
import string
from collections import Counter

from dash import constants as dash_constants
from stats import constants as stats_constants

from . import constants
from . import converters
from . import exceptions

MODIFIER_MAX = decimal.Decimal("11.0")
MODIFIER_MIN = decimal.Decimal("0.01")


_BREAKDOWN_NAME_MAP = {
    stats_constants.DimensionIdentifier.PUBLISHER: constants.BidModifierType.PUBLISHER,
    stats_constants.DimensionIdentifier.SOURCE: constants.BidModifierType.SOURCE,
    stats_constants.DeliveryDimension.DEVICE: constants.BidModifierType.DEVICE,
    stats_constants.DeliveryDimension.DEVICE_OS: constants.BidModifierType.OPERATING_SYSTEM,
    stats_constants.DeliveryDimension.ENVIRONMENT: constants.BidModifierType.ENVIRONMENT,
    stats_constants.DeliveryDimension.COUNTRY: constants.BidModifierType.COUNTRY,
    stats_constants.DeliveryDimension.REGION: constants.BidModifierType.STATE,
    stats_constants.DeliveryDimension.DMA: constants.BidModifierType.DMA,
    stats_constants.DimensionIdentifier.CONTENT_AD: constants.BidModifierType.AD,
    stats_constants.DimensionIdentifier.PLACEMENT: constants.BidModifierType.PLACEMENT,
    stats_constants.DeliveryDimension.BROWSER: constants.BidModifierType.BROWSER,
    stats_constants.DeliveryDimension.CONNECTION_TYPE: constants.BidModifierType.CONNECTION_TYPE,
}

_BID_MODIFIER_CONSTANT_MAP = {
    constants.BidModifierType.DEVICE: {"constant": dash_constants.DeviceType, "name": "Device Type"},
    constants.BidModifierType.OPERATING_SYSTEM: {
        "constant": dash_constants.OperatingSystem,
        "name": "Operating System",
    },
    constants.BidModifierType.ENVIRONMENT: {"constant": dash_constants.Environment, "name": "Environment"},
    constants.BidModifierType.DAY_HOUR: {"constant": dash_constants.DayHour, "name": "Day-Hour"},
    constants.BidModifierType.BROWSER: {"constant": dash_constants.BrowserFamily, "name": "Browser Family"},
    constants.BidModifierType.CONNECTION_TYPE: {"constant": dash_constants.ConnectionType, "name": "Connection Type"},
}


def supported_breakdown_names():
    return _BREAKDOWN_NAME_MAP.keys()


def breakdown_name_to_modifier_type(breakdown_name):
    return _BREAKDOWN_NAME_MAP[breakdown_name]


def modifier_type_to_breakdown_name(modifier_type):
    return {v: k for k, v in _BREAKDOWN_NAME_MAP.items()}[modifier_type]


def get_source_slug(modifier_type, source):
    if modifier_type not in constants.BidModifierType.get_all():
        raise exceptions.BidModifierTypeInvalid("Invalid bid modifier type")

    if modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT):
        if source is None:
            raise exceptions.BidModifierSourceInvalid("Source is required for publisher bid modifier")

        return source.bidder_slug

    else:
        if source is not None:
            raise exceptions.BidModifierSourceInvalid("Source must be empty for non-publisher bid modifier")

        return ""


def check_modifier_value(modifier):
    if not isinstance(modifier, numbers.Number):
        raise exceptions.BidModifierValueInvalid("Bid Modifier value is not a number")

    error_message = _get_modifier_bounds_error_message(modifier)
    if error_message:
        if modifier < MODIFIER_MIN:
            raise exceptions.BidModifierValueTooLow(error_message)
        else:
            raise exceptions.BidModifierValueTooHigh(error_message)


def _get_modifier_bounds_error_message(modifier):
    if modifier < MODIFIER_MIN:
        return "Bid modifier too low: %s (< %s)" % (modifier, MODIFIER_MIN)

    if modifier > MODIFIER_MAX:
        return "Bid modifier too high: %s (> %s)" % (modifier, MODIFIER_MAX)

    return None


def describe_bid_modifier(modifier_type, target, source):
    return "%s, %s%s" % (
        constants.BidModifierType.get_text(modifier_type),
        converters.DashboardConverter.from_target(modifier_type, target),
        ", " + source.name if source else "",
    )


def clean_bid_modifier_type_input(modifier_type_input, errors):
    modifier_type = constants.BidModifierType.get_value(modifier_type_input)
    if modifier_type is None:
        errors.append("Invalid Bid Modifier Type")

    return modifier_type


def output_modifier_type(modifier_type):
    output_value = constants.BidModifierType.get_text(modifier_type)
    if output_value is None:
        raise exceptions.BidModifierTypeInvalid("Invalid bid modifier type")

    return output_value


def clean_source_bidder_slug_input(source_slug_input, sources_by_slug, errors):
    source = sources_by_slug.get(source_slug_input)
    if source is None:
        errors.append("Invalid Source Slug")

    return source


def output_source_bidder_slug(source_bidder_slug):
    return source_bidder_slug.bidder_slug if source_bidder_slug else ""


def clean_bid_modifier_value_input(modifier, errors):
    if modifier == "":
        modifier = 1.0

    try:
        modifier = float(modifier)
    except ValueError:
        errors.append("Invalid Bid Modifier")
        return None

    error_message = _get_modifier_bounds_error_message(modifier)
    if error_message:
        errors.append(error_message)

    if modifier == 1.0:
        modifier = None

    return modifier


def validate_publisher(publisher):
    if not publisher.strip():
        raise exceptions.BidModifierTargetInvalid("Publisher should not be empty")

    return publisher.strip().lower()


def clean_target_input(input_value, modifier_type, errors):
    try:
        return converters.FileConverter.to_target(modifier_type, input_value)
    except exceptions.BidModifierInvalid as exc:
        errors.append(str(exc))

    return None


def transform_target(modifier_type, target_value):
    return converters.FileConverter.from_target(modifier_type, target_value)


def make_csv_file_columns(modifier_type):
    target_column_name = output_modifier_type(modifier_type)
    csv_columns = [target_column_name, "Bid Modifier"]

    if modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT):
        csv_columns.insert(1, "Source Slug")

    return csv_columns


def extract_modifier_type(csv_column_names):
    for modifier_type in constants.BidModifierType.get_all():
        column_name = output_modifier_type(modifier_type)
        if column_name in csv_column_names:
            return modifier_type, column_name

    raise exceptions.InvalidBidModifierFile("Bid Modifier target column is missing")


def create_csv_error_key():
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64))


def create_bulk_csv_file(sub_file_generator):
    csv_example_file = StringIO.StringIO()
    first_line = True
    for sub_file in sub_file_generator:
        if first_line:
            first_line = False
        else:
            csv_example_file.write(csv.excel.lineterminator)

        csv_example_file.write(sub_file.read())

    csv_example_file.seek(0)
    return csv_example_file


def split_bulk_csv_file(bulk_csv_file):
    sub_file = StringIO.StringIO()
    sub_files = []
    for line in bulk_csv_file:
        if not [e.strip() for e in line.split(",") if e.strip()]:
            sub_file.seek(0)
            sub_files.append(sub_file)
            sub_file = StringIO.StringIO()
        else:
            sub_file.write(line)

    if sub_file.tell() != 0:
        sub_file.seek(0)
        sub_files.append(sub_file)

    return sub_files


def create_upload_summary_response(delete_type_counts, instances):
    delete_types_counter = {e["type"]: e["count"] for e in delete_type_counts if e["count"] > 0}
    types_counter = Counter(i.type for i in instances if i is not None)
    return {
        "deleted": {
            "count": sum(delete_types_counter.values()),
            "dimensions": len(delete_types_counter),
            "summary": [
                {"type": constants.BidModifierType.get_name(t), "count": c}
                for t, c in sorted(delete_types_counter.items(), key=lambda x: x[0])
            ],
        },
        "created": {
            "count": sum(types_counter.values()),
            "dimensions": len(types_counter),
            "summary": [
                {"type": constants.BidModifierType.get_name(t), "count": c}
                for t, c in sorted(types_counter.items(), key=lambda x: x[0])
            ],
        },
    }


def create_error_file_path(ad_group_id, csv_error_key):
    ad_group_string = "ad_group_{}".format(ad_group_id) if ad_group_id is not None else "temporary"
    return os.path.join("bid_modifier_errors", ad_group_string, csv_error_key + ".csv")


def create_bid_modifier_dict(bid_modifier_or_none, modifier_type=None, target=None, source_slug=None):
    bid_modifier_dict = {
        "id": None,
        "type": modifier_type,
        "target": target,
        "source_slug": source_slug,
        "modifier": None,
    }
    if bid_modifier_or_none:
        bid_modifier_dict["id"] = bid_modifier_or_none.id
        bid_modifier_dict["modifier"] = bid_modifier_or_none.modifier
        bid_modifier_dict["source_slug"] = bid_modifier_or_none.source_slug
    return bid_modifier_dict


def modifier_type_to_constant_dimension(bid_modifier_type):
    dimension = _BID_MODIFIER_CONSTANT_MAP.get(bid_modifier_type)
    return (dimension.get("constant"), dimension.get("name"))
