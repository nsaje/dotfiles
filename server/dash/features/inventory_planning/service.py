import redshiftapi.api_inventory

import dash.features.geolocation
import core.source

from . import constants


ZERO_ROW = {'bids': 0, 'bid_reqs': 0, 'win_notices': 0, 'total_win_price': 0}
MIN_AUCTIONS = 1000

_countries_map = None
_sources_map = None


def _get_countries_map():
    global _countries_map
    if _countries_map is None:
        _countries_map = {
            geolocation.key: geolocation.name
            for geolocation in
            dash.features.geolocation.Geolocation.objects.filter(type=dash.constants.LocationType.COUNTRY)
        }
    return _countries_map


def _get_sources_map():
    global _sources_map
    if _sources_map is None:
        _sources_map = {
            source.id: source.name
            for source in
            core.source.Source.objects.filter(deprecated=False, released=True)
        }
    return _sources_map


def get_summary(filters):
    data = redshiftapi.api_inventory.query(breakdown=None, constraints=filters)[0]
    for field in data:
        data[field] = data[field] or 0
    return data


def get_by_country(filters):
    data = redshiftapi.api_inventory.query(breakdown='country', constraints=filters)
    data = list(filter(_min_auctions_filter, data))
    countries_map = _get_countries_map()
    _add_zero_rows(data, 'country', sorted(countries_map.keys()))
    for item in data:
        item['name'] = countries_map.get(item['country'], 'Not reported')
    return data


def get_by_publisher(filters):
    data = redshiftapi.api_inventory.query(breakdown='publisher', constraints=filters)
    data = list(filter(_min_auctions_filter, data))
    ordered_top_publishers = redshiftapi.api_inventory.query_top_publishers()
    _add_zero_rows(data, 'publisher', ordered_top_publishers)
    return data


def get_by_device_type(filters):
    data = redshiftapi.api_inventory.query(breakdown='device_type', constraints=filters)
    data = list(filter(_min_auctions_filter, data))
    device_types_map = dict(constants.InventoryDeviceType.get_choices())
    _add_zero_rows(data, 'device_type', sorted(device_types_map.keys()))
    for item in data:
        item['name'] = device_types_map.get(item['device_type'])
    return data


def get_by_media_source(filters):
    data = redshiftapi.api_inventory.query(breakdown='source_id', constraints=filters)
    data = list(filter(_min_auctions_filter, data))
    sources_map = _get_sources_map()
    _add_zero_rows(data, 'source_id', sorted(sources_map.keys()))
    data = list(filter(lambda item: item['source_id'] in sources_map, data))
    for item in data:
        item['name'] = sources_map.get(item['source_id'])
    return data


def _min_auctions_filter(item):
    return item['bid_reqs'] >= MIN_AUCTIONS


def _add_zero_rows(data, field_name, all_keys):
    not_present = set(all_keys)
    for item in data:
        not_present.discard(item[field_name])
    for key in all_keys:
        if key in not_present:
            new_row = ZERO_ROW.copy()
            new_row[field_name] = key
            data.append(new_row)
