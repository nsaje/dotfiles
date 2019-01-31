import core.models
import dash.features.geolocation
import redshiftapi.api_inventory

from . import constants

ZERO_ROW = {"bids": 0, "bid_reqs": 0, "win_notices": 0, "total_win_price": 0, "slots": 0, "redirects": 0}
MIN_AUCTIONS = 1000

_countries_cache = None
_sources_cache = None


def get_countries_map():
    global _countries_cache
    if _countries_cache is None:
        _countries_cache = {
            geolocation.key: geolocation.name
            for geolocation in dash.features.geolocation.Geolocation.objects.filter(
                type=dash.constants.LocationType.COUNTRY
            )
        }
    return _countries_cache


def _get_sources_cache():
    global _sources_cache
    if _sources_cache is None:
        _sources_cache = core.models.Source.objects.filter(deprecated=False)
    return _sources_cache


def get_filtered_sources_map(request):
    sources_map = {
        source.id: source.name
        for source in _get_sources_cache()
        if (
            source.released
            or has_mediamond_credentials(request)
            and source.id == constants.NativeAdServerSourceId.MEDIAMOND
            or has_rcs_credentials(request)
            and source.id == constants.NativeAdServerSourceId.RCS
            or has_newscorp_credentials(request)
            and source.id in [constants.NativeAdServerSourceId.NEWSCORP, constants.NativeAdServerSourceId.NEWSCORP_TEST]
        )
    }
    return sources_map


def has_mediamond_credentials(request):
    return (
        request is None
        or request.user.has_perm("zemauth.can_see_mediamond_publishers")
        or request.user.agency_set.filter(
            id__in=[constants.NativeAdServerAgencyId.MEDIAMOND, constants.NativeAdServerAgencyId.MEDIAMOND_SELF_MANAGED]
        ).exists()
    )


def has_rcs_credentials(request):
    return (
        request is None
        or request.user.has_perm("zemauth.can_see_rcs_publishers")
        or request.user.agency_set.filter(
            id__in=[constants.NativeAdServerAgencyId.RCS_MEDIAGROUP, constants.NativeAdServerAgencyId.RCS]
        ).exists()
    )


def has_newscorp_credentials(request):
    return (
        request is None
        or request.user.has_perm("zemauth.can_see_newscorp_publishers")
        or request.user.agency_set.filter(id=constants.NativeAdServerAgencyId.NEWSCORP).exists()
    )


def _update_filters(request, filters):
    updated_filters = filters.copy()
    if "source_id" not in filters:
        updated_filters["source_id"] = list(get_filtered_sources_map(request).keys())
    return updated_filters


def get_summary(request, filters):
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown=None, constraints=updated_filters)[0]
    for field in data:
        data[field] = data[field] or 0
    return data


def get_by_country(request, filters):
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown="country", constraints=updated_filters)
    data = list(filter(_min_auctions_filter, data))
    countries_map = get_countries_map()
    _add_zero_rows(data, "country", sorted(countries_map.keys()))
    for item in data:
        item["name"] = countries_map.get(item["country"], "Not reported")
    return data


def get_by_publisher(request, filters):
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown="publisher", constraints=updated_filters)
    data = list(filter(_min_auctions_filter, data))
    ordered_top_publishers = redshiftapi.api_inventory.query_top_publishers()
    _add_zero_rows(data, "publisher", ordered_top_publishers)
    return data


def get_by_device_type(request, filters):
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown="device_type", constraints=updated_filters)
    data = list(filter(_min_auctions_filter, data))
    device_types_map = dict(constants.InventoryDeviceType.get_choices())
    _add_zero_rows(data, "device_type", sorted(device_types_map.keys()))
    for item in data:
        item["name"] = device_types_map.get(item["device_type"])
    return data


def get_by_media_source(request, filters):
    data = redshiftapi.api_inventory.query(breakdown="source_id", constraints=filters)
    data = list(filter(_min_auctions_filter, data))
    sources_map = get_filtered_sources_map(request)
    _add_zero_rows(data, "source_id", sorted(sources_map.keys()))
    data = list(filter(lambda item: item["source_id"] in sources_map, data))
    for item in data:
        item["name"] = sources_map.get(item["source_id"])
    return data


def _min_auctions_filter(item):
    return item["bid_reqs"] >= MIN_AUCTIONS


def _add_zero_rows(data, field_name, all_keys):
    not_present = set(all_keys)
    for item in data:
        not_present.discard(item[field_name])
    for key in all_keys:
        if key in not_present:
            new_row = ZERO_ROW.copy()
            new_row[field_name] = key
            data.append(new_row)
