import core.models
import dash.features.geolocation
import redshiftapi.api_inventory

from . import constants
from . import nas

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


def get_filtered_sources_map(request, filters):
    sources_map = {
        source.id: source.name
        for source in _get_sources_cache()
        if (source.released or nas.should_show_nas_source(source, request))
        and _source_supports_channel(source, filters)
    }
    return sources_map


def _source_supports_channel(source, filters):
    if "channel" not in filters:
        return True

    if constants.InventoryChannel.NATIVE in filters["channel"]:
        return True

    supports_filters = False
    if constants.InventoryChannel.VIDEO in filters["channel"]:
        supports_filters = supports_filters or source.supports_video
    if constants.InventoryChannel.DISPLAY in filters["channel"]:
        supports_filters = supports_filters or source.supports_display

    return supports_filters


def _update_filters(request, filters):
    updated_filters = filters.copy()
    if "source_id" not in filters:
        updated_filters["source_id"] = list(get_filtered_sources_map(request, filters).keys())
    if "channel" in filters:
        if (
            constants.InventoryChannel.NATIVE in filters["channel"]
            or constants.InventoryChannel.VIDEO in filters["channel"]
        ):
            filters["channel"].append(constants.InventoryChannel.NATIVE_OR_VIDEO)
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
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown="source_id", constraints=updated_filters)
    data = list(filter(_min_auctions_filter, data))
    sources_map = get_filtered_sources_map(request, filters)
    _add_zero_rows(data, "source_id", sorted(sources_map.keys()))
    data = list(filter(lambda item: item["source_id"] in sources_map, data))
    for item in data:
        item["name"] = sources_map.get(item["source_id"])
    return data


def get_by_channel(request, filters):
    updated_filters = _update_filters(request, filters)
    data = redshiftapi.api_inventory.query(breakdown="channel", constraints=updated_filters)
    data = list(filter(_min_auctions_filter, data))
    channels_map = dict(constants.InventoryChannel.get_choices())
    del channels_map[constants.InventoryChannel.NATIVE_OR_VIDEO]
    _add_zero_rows(data, "channel", sorted(channels_map.keys()))
    data = _add_nativeorvideo_to_native_and_video(data)
    data = list(filter(lambda item: item["channel"] in channels_map, data))
    data = sorted(data, key=lambda item: item["slots"], reverse=True)
    for item in data:
        item["name"] = channels_map.get(item["channel"])
    return data


def _add_nativeorvideo_to_native_and_video(data):
    native_row = None
    video_row = None
    nativeorvideo_row = None
    for row in data:
        if row["channel"] == constants.InventoryChannel.NATIVE:
            native_row = row
        if row["channel"] == constants.InventoryChannel.VIDEO:
            video_row = row
        if row["channel"] == constants.InventoryChannel.NATIVE_OR_VIDEO:
            nativeorvideo_row = row
    if nativeorvideo_row:
        for field in ZERO_ROW.keys():
            native_row[field] += nativeorvideo_row[field]
            video_row[field] += nativeorvideo_row[field]
    return data


def _min_auctions_filter(item):
    return item["slots"] >= MIN_AUCTIONS


def _add_zero_rows(data, field_name, all_keys):
    not_present = set(all_keys)
    for item in data:
        not_present.discard(item[field_name])
    for key in all_keys:
        if key in not_present:
            new_row = ZERO_ROW.copy()
            new_row[field_name] = key
            data.append(new_row)
