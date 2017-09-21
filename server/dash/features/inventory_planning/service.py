import redshiftapi.api_inventory

import dash.features.geolocation
import dash.constants


_countries_map = None


def _get_countries_map():
    global _countries_map
    if _countries_map is None:
        _countries_map = {
            geolocation.key: geolocation.name
            for geolocation in
            dash.features.geolocation.Geolocation.objects.filter(type=dash.constants.LocationType.COUNTRY)
        }
    return _countries_map


def get_summary(filters):
    data = redshiftapi.api_inventory.query(breakdown=None, constraints=filters)
    return data[0]


def get_by_country(filters):
    data = redshiftapi.api_inventory.query(breakdown='country', constraints=filters)
    countries_map = _get_countries_map()
    data = _remap_value(data, 'country')
    for item in data:
        item['name'] = countries_map.get(item['value'])
    return data


def get_by_publisher(filters):
    data = redshiftapi.api_inventory.query(breakdown='publisher', constraints=filters)
    data = _remap_value(data, 'publisher')
    return data


def get_by_device_type(filters):
    device_types_map = dict(dash.constants.DeviceType.get_choices())
    data = redshiftapi.api_inventory.query(breakdown='device_type', constraints=filters)
    data = _remap_value(data, 'device_type')
    for item in data:
        item['name'] = device_types_map.get(item['value'])
    return data


def _remap_value(data, field_name):
    for item in data:
        item['value'] = item.pop(field_name)
    return data
