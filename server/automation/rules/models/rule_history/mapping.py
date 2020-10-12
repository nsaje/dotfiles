import core.models
import dash.constants
import dash.features.geolocation

_geolocations_cache = None
_sources_cache = None


def get_geolocations_map():
    global _geolocations_cache
    if _geolocations_cache is None:
        _geolocations_cache = {
            geolocation.key: geolocation.name
            for geolocation in dash.features.geolocation.Geolocation.objects.filter(
                type__in=[
                    dash.constants.LocationType.COUNTRY,
                    dash.constants.LocationType.REGION,
                    dash.constants.LocationType.DMA,
                ]
            )
        }
    return _geolocations_cache


def get_sources_map():
    global _sources_cache
    if _sources_cache is None:
        _sources_cache = {source.id: source.name for source in core.models.Source.objects.filter(deprecated=False)}
    return _sources_cache


def get_operating_systems_map():
    return dict(dash.constants.OperatingSystem.get_choices())


def get_device_types_map():
    return dict(dash.constants.DeviceType.get_choices())


def get_environments_map():
    return dict(dash.constants.Environment.get_choices())


def get_browsers_map():
    return dict(dash.constants.BrowserFamily.get_choices())


def get_connection_types_map():
    return dict(dash.constants.ConnectionType.get_choices())


def get_empty_map():
    return {}
