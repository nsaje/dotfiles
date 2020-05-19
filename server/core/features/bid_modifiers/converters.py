import utils.cache_helper
import utils.exc
from core.features import publisher_groups
from dash import constants as dash_constants
from dash import models
from dash import publisher_helpers
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
        constants.BidModifierType.ENVIRONMENT: "_from_environment_target",
        constants.BidModifierType.COUNTRY: "_from_country_target",
        constants.BidModifierType.STATE: "_from_state_target",
        constants.BidModifierType.DMA: "_from_dma_target",
        constants.BidModifierType.AD: "_from_content_ad_target",
        constants.BidModifierType.DAY_HOUR: "_from_day_hour_target",
        constants.BidModifierType.PLACEMENT: "_from_placement_target",
    }
    _to_target_map = {
        constants.BidModifierType.PUBLISHER: "_to_publisher_target",
        constants.BidModifierType.SOURCE: "_to_source_target",
        constants.BidModifierType.DEVICE: "_to_device_type_target",
        constants.BidModifierType.OPERATING_SYSTEM: "_to_operating_system_target",
        constants.BidModifierType.ENVIRONMENT: "_to_environment_target",
        constants.BidModifierType.COUNTRY: "_to_country_target",
        constants.BidModifierType.STATE: "_to_state_target",
        constants.BidModifierType.DMA: "_to_dma_target",
        constants.BidModifierType.AD: "_to_content_ad_target",
        constants.BidModifierType.DAY_HOUR: "_to_day_hour_target",
        constants.BidModifierType.PLACEMENT: "_to_placement_target",
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
    def _to_placement_target(cls, value):
        try:
            publisher, source_id, placement = publisher_helpers.dissect_placement_id(value)
            if not placement:
                raise ValueError()
            publisher_groups.validate_placement(placement)
        except Exception:
            raise exceptions.BidModifierTargetInvalid("Invalid Placement Target")
        if not models.Source.objects.filter(id=source_id).exists():
            raise exceptions.BidModifierTargetInvalid("Invalid Source")
        return value

    @classmethod
    def _from_placement_target(cls, target):
        return target

    @classmethod
    def _to_source_target(cls, value):
        source = models.Source.objects.filter(bidder_slug=value).only("id").first()

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target):
        return models.Source.objects.filter(id=int(target)).only("bidder_slug").first().bidder_slug

    @classmethod
    def _to_device_type_target(cls, value):
        if value == dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Device Type Target")

        device_type = dash_constants.DeviceType.get_constant_value(value)
        if device_type is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Device Type")

        return str(device_type)

    @classmethod
    def _from_device_type_target(cls, target):
        return dash_constants.DeviceType.get_name(int(target))

    @classmethod
    def _to_day_hour_target(cls, value):
        day_hour = dash_constants.DayHour.get_constant_value(value)
        if day_hour is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Day-Hour")

        return str(day_hour)

    @classmethod
    def _from_day_hour_target(cls, target):
        return dash_constants.DayHour.get_name(target)

    @classmethod
    def _to_operating_system_target(cls, value):
        if value == dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Operating System Target")

        operating_system = dash_constants.OperatingSystem.get_constant_value(value)
        if operating_system is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Operating System")

        return operating_system

    @classmethod
    def _from_operating_system_target(cls, target):
        return dash_constants.OperatingSystem.get_name(target)

    @classmethod
    def _to_environment_target(cls, value):
        if value == dash_constants.Environment.get_text(dash_constants.Environment.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Environment Target")

        environment = dash_constants.Environment.get_constant_value(value)
        if environment is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Environment")

        return environment

    @classmethod
    def _from_environment_target(cls, target):
        return dash_constants.Environment.get_name(target)

    @classmethod
    @utils.cache_helper.memoize
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
    pass

    @classmethod
    def _to_operating_system_target(cls, value):
        # map legacy file operating system values
        converted_legacy_value = dash_constants.OperatingSystem.get_value(value)
        if converted_legacy_value is not None:
            value = dash_constants.OperatingSystem.get_name(converted_legacy_value)

        return super()._to_operating_system_target(value)


class ApiConverter(TargetConverter):
    pass


class DashboardConverter(TargetConverter):
    @classmethod
    def _to_device_type_target(cls, value):
        if value == dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Device Type Target")

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
        elif value in constants.UNSUPPORTED_TARGETS or value == dash_constants.OperatingSystem.get_text(
            dash_constants.OperatingSystem.UNKNOWN
        ):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Operating System Target")

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
    def _to_environment_target(cls, value):
        if value == dash_constants.Environment.get_text(dash_constants.Environment.UNKNOWN):
            raise exceptions.BidModifierUnsupportedTarget("Unsupported Environment Target")

        environment_text = dash_constants.Environment.get_text(value)
        if environment_text is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Environment")

        return value

    @classmethod
    def _from_environment_target(cls, target):
        dash_constants.Environment.get_name(target)
        return target

    @classmethod
    def _to_dma_target(cls, value):
        return TargetConverter._to_dma_target(str(value))

    @classmethod
    def _from_dma_target(cls, target):
        return int(target)

    @classmethod
    def _to_source_target(cls, value):
        try:
            return str(models.Source.objects.filter(name=value).only("id").get().id)
        except (models.Source.DoesNotExist, models.Source.MultipleObjectsReturned):
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

    @classmethod
    def _from_source_target(cls, target):
        return models.Source.objects.filter(id=int(target)).only("name").get().name


class StatsConverter(TargetConverter):
    @classmethod
    def _to_device_type_target(cls, value):
        return DashboardConverter._to_device_type_target(value)

    @classmethod
    def _from_device_type_target(cls, target):
        return DashboardConverter._from_device_type_target(target)

    @classmethod
    def _to_operating_system_target(cls, value):
        return DashboardConverter._to_operating_system_target(value)

    @classmethod
    def _from_operating_system_target(cls, target):
        return DashboardConverter._from_operating_system_target(target)

    @classmethod
    def _to_environment_target(cls, value):
        return DashboardConverter._to_environment_target(value)

    @classmethod
    def _from_environment_target(cls, target):
        return DashboardConverter._from_environment_target(target)

    @classmethod
    def _to_source_target(cls, value):
        source = models.Source.objects.filter(id=value).only("id").first()

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target):
        return str(target)
