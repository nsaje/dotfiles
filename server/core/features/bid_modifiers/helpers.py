import decimal

from core.models.source import model as source_model
from dash import constants as dash_constants
from dash.features import geolocation

from . import constants
from . import exceptions

MODIFIER_MAX = decimal.Decimal("11.0")
MODIFIER_MIN = decimal.Decimal("0.01")


def get_source_slug(modifier_type, source):
    if modifier_type is constants.BidModifierType.PUBLISHER:
        if source is None:
            raise exceptions.BidModifierSourceInvalid("Source is required for publisher bid modifier")

        return source.bidder_slug

    else:
        if source is not None:
            raise exceptions.BidModifierSourceInvalid("Source must be empty for non-publisher bid modifier")

        return ""


def modifier_bounds_ok(modifier):
    return MODIFIER_MIN <= modifier <= MODIFIER_MAX


def describe_bid_modifier(modifier_type, target, source):
    return "%s, %s%s" % (
        constants.BidModifierType.get_text(modifier_type),
        target,
        ", " + source.name if source else "",
    )


def clean_bid_modifier_type_input(modifier_type_input, errors):
    modifier_type = constants.BidModifierType.get_value(modifier_type_input)
    if modifier_type is None:
        errors.append("Invalid Bid Modifier Type")

    return modifier_type


def output_modifier_type(modifier_type):
    return constants.BidModifierType.get_text(modifier_type)


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

    if modifier < MODIFIER_MIN:
        errors.append("Bid modifier too low (< %s)" % MODIFIER_MIN)

    if modifier > MODIFIER_MAX:
        errors.append("Bid modifier too high (> %s)" % MODIFIER_MAX)

    if modifier == 1.0:
        modifier = None

    return modifier


def clean_publisher_input(publisher, errors):
    publisher = publisher.strip()
    prefixes = ("http://", "https://")
    if any(publisher.startswith(x) for x in prefixes):
        errors.append("Remove the following prefixes: http, https")

    for prefix in ("http://", "https://"):
        publisher = publisher.replace(prefix, "")

    if "/" in publisher:
        errors.append("Publisher should not contain /")
        publisher = publisher.strip("/")

    return publisher


def clean_source_input(source_input, errors):
    source = source_model.Source.objects.filter(bidder_slug=source_input).only("id").first()
    if source is None:
        errors.append("Invalid Source")
        return None

    return str(source.id)


def output_source_target(source_target):
    source = source_model.Source.objects.filter(id=source_target).only("bidder_slug").first()
    if source is None:
        raise ValueError("Provided source target does not exist")

    return source.bidder_slug


def clean_device_type_input(device_type_input, errors):
    device_type = dash_constants.DeviceType.get_value(device_type_input)
    if device_type is None:
        errors.append("Invalid Device")
        return None

    return str(device_type)


def output_device_type_target(device_type_target):
    device_type = dash_constants.DeviceType.get_text(int(device_type_target))
    if device_type is None:
        raise ValueError("Provided device type target does not exist")

    return device_type


def clean_operating_system_input(os_type_input, errors):
    os = dash_constants.OperatingSystem.get_value(os_type_input)
    if os is None:
        errors.append("Invalid Operating System")
        return None

    return str(os)


def output_operating_system_target(operating_system_target):
    operating_system = dash_constants.OperatingSystem.get_text(operating_system_target)
    if operating_system is None:
        raise ValueError("Provided operating system target does not exist")

    return operating_system


def clean_placement_medium_input(placement_medium_input, errors):
    placement_medium = dash_constants.PlacementMedium.get_value(placement_medium_input)
    if placement_medium is None:
        errors.append("Invalid Placement")
        return None

    return str(placement_medium)


def output_placement_medium_target(placement_medium_target):
    placement_medium = dash_constants.PlacementMedium.get_text(placement_medium_target)
    if placement_medium is None:
        raise ValueError("Provided placement medium target does not exist")

    return placement_medium


def clean_geolocation_input(geolocation_input, modifier_type, errors):
    if modifier_type == constants.BidModifierType.COUNTRY:
        geo_type = dash_constants.LocationType.COUNTRY
    elif modifier_type == constants.BidModifierType.STATE:
        geo_type = dash_constants.LocationType.REGION
    elif modifier_type == constants.BidModifierType.DMA:
        geo_type = dash_constants.LocationType.DMA
    else:
        raise ValueError("Illegal geolocation bid modifier type")

    geo_location = geolocation.Geolocation.objects.filter(key=geolocation_input, type=geo_type).only("key").first()
    if geo_location is None:
        errors.append("Invalid Geolocation")
        return None

    return str(geo_location.key)
