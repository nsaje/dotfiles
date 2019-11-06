
from dash.constants import Level
from stats import constants
from utils import exc


def validate_breakdown_by_permissions(level, user, breakdown):
    if constants.StructureDimension.PUBLISHER in breakdown and not user.has_perm("zemauth.can_see_publishers"):
        raise exc.MissingDataError()
    elif constants.StructureDimension.SOURCE in breakdown:
        if level == Level.ALL_ACCOUNTS and not user.has_perm("zemauth.all_accounts_sources_view"):
            raise exc.MissingDataError()
        elif level == Level.ACCOUNTS and not user.has_perm("zemauth.account_sources_view"):
            raise exc.MissingDataError()
    else:
        if level == Level.ALL_ACCOUNTS and not user.has_perm("zemauth.all_accounts_accounts_view"):
            raise exc.MissingDataError()
        elif level == Level.ACCOUNTS and not user.has_perm("zemauth.account_campaigns_view"):
            raise exc.MissingDataError()

    if (
        constants.StructureDimension.PUBLISHER in breakdown
        and constants.StructureDimension.CONTENT_AD in breakdown
        and not user.has_perm("zemauth.can_breakdown_reports_by_ads_and_publishers")
    ):
        raise exc.MissingDataError()

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if delivery_dimension is not None and not user.has_perm("zemauth.can_view_breakdown_by_delivery"):
        raise exc.MissingDataError()

    if constants.is_extended_delivery_dimension(delivery_dimension) and not user.has_perm(
        "zemauth.can_view_breakdown_by_delivery_extended"
    ):
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
    clean_breakdown.extend(delivery)

    unsupported_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupported_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns: {}".format(", ".join(unsupported_breakdowns)))
