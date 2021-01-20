
from dash.constants import Level
from stats import constants
from utils import exc


def validate_breakdown_by_permissions(level, user, breakdown):
    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if constants.is_extended_delivery_dimension(delivery_dimension) and not user.has_perm(
        "zemauth.can_view_breakdown_by_delivery_extended"
    ):
        raise exc.MissingDataError()

    if constants.is_placement_breakdown(breakdown):
        if level in (Level.ALL_ACCOUNTS, Level.CONTENT_ADS):
            raise exc.MissingDataError()


def validate_breakdown_by_structure(level, breakdown):
    if constants.StructureDimension.PUBLISHER in breakdown and constants.StructureDimension.SOURCE in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - publishers are broken down by source by default")

    clean_breakdown = [dimension for dimension in breakdown if dimension in constants.StructureDimension._ALL]

    time = constants.get_time_dimension(breakdown)
    if time:
        clean_breakdown.append(time)

    delivery = [dimension for dimension in breakdown if dimension in constants.DeliveryDimension._ALL]
    if len(delivery) > 1:
        raise exc.InvalidBreakdownError("Unsupported breakdown - only one delivery breakdown supported per report")

    if constants.is_placement_breakdown(breakdown) and "content_ad_id" in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - content ads can not be broken down by placement")

    if delivery and constants.is_placement_breakdown(breakdown):
        raise exc.InvalidBreakdownError(
            "Unsupported breakdown - placements can not be broken down by {}".format(delivery[0])
        )

    clean_breakdown.extend(delivery)
    unsupported_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupported_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns: {}".format(", ".join(unsupported_breakdowns)))
