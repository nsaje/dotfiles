from dash import constants as dash_constants
from dash import models
from dash.features import geolocation

from . import constants
from . import exceptions
from . import helpers


class TargetConverter:

    _from_target_map = {
        constants.BidModifierType.PUBLISHER: "_from_publisher_target",
        constants.BidModifierType.SOURCE: "_from_source_target",
        constants.BidModifierType.DEVICE: "_from_device_type_target",
        constants.BidModifierType.OPERATING_SYSTEM: "_from_operating_system_target",
        constants.BidModifierType.PLACEMENT: "_from_placement_medium_target",
        constants.BidModifierType.COUNTRY: "_from_country_target",
        constants.BidModifierType.STATE: "_from_state_target",
        constants.BidModifierType.DMA: "_from_dma_target",
        constants.BidModifierType.AD: "_from_content_ad_target",
    }
    _to_target_map = {
        constants.BidModifierType.PUBLISHER: "_to_publisher_target",
        constants.BidModifierType.SOURCE: "_to_source_target",
        constants.BidModifierType.DEVICE: "_to_device_type_target",
        constants.BidModifierType.OPERATING_SYSTEM: "_to_operating_system_target",
        constants.BidModifierType.PLACEMENT: "_to_placement_medium_target",
        constants.BidModifierType.COUNTRY: "_to_country_target",
        constants.BidModifierType.STATE: "_to_state_target",
        constants.BidModifierType.DMA: "_to_dma_target",
        constants.BidModifierType.AD: "_to_content_ad_target",
    }

    @classmethod
    def from_target(cls, modifier_type, target):
        converter_fn_name = cls._from_target_map.get(modifier_type)
        if not converter_fn_name:
            raise exceptions.BidModifierTypeInvalid("Invalid Bid Modifier Type")

        converter_fn = getattr(cls, converter_fn_name)
        return converter_fn(target)

    @classmethod
    def to_target(cls, modifier_type, value):
        converter_fn_name = cls._to_target_map.get(modifier_type)
        if not converter_fn_name:
            raise exceptions.BidModifierTypeInvalid("Invalid Bid Modifier Type")

        converter_fn = getattr(cls, converter_fn_name)
        return converter_fn(value)

    @classmethod
    def _to_publisher_target(cls, value):
        return helpers.validate_publisher(value)

    @classmethod
    def _from_publisher_target(cls, target):
        return target

    @classmethod
    def _to_source_target(cls, value):
        try:
            source = models.Source.objects.filter(id=value).only("id").first()
        except ValueError:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target):
        return target

    @classmethod
    def _to_device_type_target(cls, value):
        if value == dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Device Type Traget")

        device_type = dash_constants.DeviceType.get_constant_value(value)
        if device_type is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Device Type")

        return str(device_type)

    @classmethod
    def _from_device_type_target(cls, target):
        return dash_constants.DeviceType.get_name(int(target))

    @classmethod
    def _to_operating_system_target(cls, value):
        if value == dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Operating System Traget")

        operating_system = dash_constants.OperatingSystem.get_value(value)
        if operating_system is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Operating System")

        return operating_system

    @classmethod
    def _from_operating_system_target(cls, target):
        value = dash_constants.OperatingSystem.get_text(target)
        if not value:
            raise ValueError("Invalid Operating System target")

        return value

    @classmethod
    def _to_placement_medium_target(cls, value):
        if value == dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Placement Medium Traget")

        placement_medium = dash_constants.PlacementMedium.get_constant_value(value)
        if placement_medium is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Placement Medium")

        return placement_medium

    @classmethod
    def _from_placement_medium_target(cls, target):
        return dash_constants.PlacementMedium.get_name(target)

    @classmethod
    def _to_geolocation_target(cls, geo_type, value):
        geo_location = geolocation.Geolocation.objects.filter(key=value, type=geo_type).only("key").first()
        if geo_location is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Geolocation")

        return geo_location.key

    @classmethod
    def _from_geolocation_target(cls, geo_type, target):
        return target

    @classmethod
    def _to_country_target(cls, value):
        return cls._to_geolocation_target(dash_constants.LocationType.COUNTRY, value)

    @classmethod
    def _from_country_target(cls, target):
        return cls._from_geolocation_target(dash_constants.LocationType.COUNTRY, target)

    @classmethod
    def _to_state_target(cls, value):
        return cls._to_geolocation_target(dash_constants.LocationType.REGION, value)

    @classmethod
    def _from_state_target(cls, target):
        return cls._from_geolocation_target(dash_constants.LocationType.REGION, target)

    @classmethod
    def _to_dma_target(cls, value):
        return cls._to_geolocation_target(dash_constants.LocationType.DMA, value)

    @classmethod
    def _from_dma_target(cls, target):
        return cls._from_geolocation_target(dash_constants.LocationType.DMA, target)

    @classmethod
    def _to_content_ad_target(cls, value):
        try:
            content_ad = models.ContentAd.objects.filter(id=value).only("id").first()
        except ValueError:
            raise exceptions.BidModifierTargetInvalid("Invalid Content Ad")

        if content_ad is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Content Ad")

        return str(content_ad.id)

    @classmethod
    def _from_content_ad_target(cls, target):
        return target


class FileConverter(TargetConverter):
    @classmethod
    def _to_source_target(cls, value):
        try:
            source = models.Source.objects.filter(bidder_slug=value).only("id").first()
        except ValueError:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target):
        return models.Source.objects.filter(id=int(target)).only("bidder_slug").first().bidder_slug


class ApiConverter(TargetConverter):
    @classmethod
    def _to_operating_system_target(cls, value):
        if value == dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Operating System Traget")

        operating_system = dash_constants.OperatingSystem.get_constant_value(value)
        if operating_system is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Operating System")

        return operating_system

    @classmethod
    def _from_operating_system_target(cls, target):
        return dash_constants.OperatingSystem.get_name(target)


class StatsConverter(TargetConverter):
    @classmethod
    def _to_device_type_target(cls, value):
        if value == dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Device Type Traget")

        device_type_text = dash_constants.DeviceType.get_text(value)
        if device_type_text is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Device Type")

        return str(value)

    @classmethod
    def _from_device_type_target(cls, target):
        dash_constants.DeviceType.get_name(int(target))
        return int(target)

    @classmethod
    def _to_operating_system_target(cls, value):
        if value == "WinPhone":
            value = "Windows Phone"
        elif (
            value == dash_constants.OperatingSystem.UNKNOWN
            or value == dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.UNKNOWN)
            or value == "Other"
        ):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Operating System Traget")

        operating_system = dash_constants.OperatingSystem.get_value(value)
        if operating_system is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Operating System")

        return operating_system

    @classmethod
    def _from_operating_system_target(cls, target):
        value = dash_constants.OperatingSystem.get_text(target)
        if not value:
            raise ValueError("Invalid Operating System target")

        if value == "Windows Phone":
            value = "WinPhone"

        return value

    @classmethod
    def _to_placement_medium_target(cls, value):
        if value == dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Placement Medium Traget")

        placement_medium_text = dash_constants.PlacementMedium.get_text(value)
        if placement_medium_text is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Placement Medium")

        return value

    @classmethod
    def _from_placement_medium_target(cls, target):
        dash_constants.PlacementMedium.get_name(target)
        return target

    @classmethod
    def _to_dma_target(cls, value):
        return TargetConverter._to_dma_target(str(value))

    @classmethod
    def _from_dma_target(cls, target):
        return int(target)
