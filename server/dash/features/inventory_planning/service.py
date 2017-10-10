import redshiftapi.api_inventory

import dash.features.geolocation

import constants


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
    data = redshiftapi.api_inventory.query(breakdown=None, constraints=filters)[0]
    for field in data:
        data[field] = data[field] or 0
    return data


def get_by_country(filters):
    data = redshiftapi.api_inventory.query(breakdown='country', constraints=filters)
    countries_map = _get_countries_map()
    for item in data:
        item['name'] = countries_map.get(item['country'], 'Not reported')
    return data


def get_by_publisher(filters):
    data = redshiftapi.api_inventory.query(breakdown='publisher', constraints=filters)
    for item in data:
        if not item['value']:
            item['name'] = 'Not reported'
    return data


def get_by_device_type(filters):
    device_types_map = dict(constants.DeviceType.get_choices())
    data = redshiftapi.api_inventory.query(breakdown='device_type', constraints=filters)
    for item in data:
        item['name'] = device_types_map.get(item['device_type'])
    return data
