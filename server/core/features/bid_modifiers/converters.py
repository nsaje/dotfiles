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
        constants.BidModifierType.DEVICE: "_from_constant_target",
        constants.BidModifierType.OPERATING_SYSTEM: "_from_operating_system_target",
        constants.BidModifierType.ENVIRONMENT: "_from_constant_target",
        constants.BidModifierType.COUNTRY: "_from_country_target",
        constants.BidModifierType.STATE: "_from_state_target",
        constants.BidModifierType.DMA: "_from_dma_target",
        constants.BidModifierType.AD: "_from_content_ad_target",
        constants.BidModifierType.DAY_HOUR: "_from_constant_target",
        constants.BidModifierType.PLACEMENT: "_from_placement_target",
        constants.BidModifierType.BROWSER: "_from_constant_target",
        constants.BidModifierType.CONNECTION_TYPE: "_from_constant_target",
    }
    _to_target_map = {
        constants.BidModifierType.PUBLISHER: "_to_publisher_target",
        constants.BidModifierType.SOURCE: "_to_source_target",
        constants.BidModifierType.DEVICE: "_to_constant_target",
        constants.BidModifierType.OPERATING_SYSTEM: "_to_operating_system_target",
        constants.BidModifierType.ENVIRONMENT: "_to_constant_target",
        constants.BidModifierType.COUNTRY: "_to_country_target",
        constants.BidModifierType.STATE: "_to_state_target",
        constants.BidModifierType.DMA: "_to_dma_target",
        constants.BidModifierType.AD: "_to_content_ad_target",
        constants.BidModifierType.DAY_HOUR: "_to_constant_target",
        constants.BidModifierType.PLACEMENT: "_to_placement_target",
        constants.BidModifierType.BROWSER: "_to_constant_target",
        constants.BidModifierType.CONNECTION_TYPE: "_to_constant_target",
    }

    @classmethod
    def from_target(cls, modifier_type, target):
        converter_fn_name = cls._from_target_map.get(modifier_type)
        if not converter_fn_name:
            raise exceptions.BidModifierTypeInvalid("Invalid Bid Modifier Type")

        converter_fn = getattr(cls, converter_fn_name)
        return converter_fn(target, modifier_type)

    @classmethod
    def to_target(cls, modifier_type, value):
        converter_fn_name = cls._to_target_map.get(modifier_type)
        if not converter_fn_name:
            raise exceptions.BidModifierTypeInvalid("Invalid Bid Modifier Type")

        converter_fn = getattr(cls, converter_fn_name)
        return converter_fn(value, modifier_type)

    @classmethod
    def _to_publisher_target(cls, value, _):
        return helpers.validate_publisher(value)

    @classmethod
    def _from_publisher_target(cls, target, _):
        return target

    @classmethod
    def _to_placement_target(cls, value, _):
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
    def _from_placement_target(cls, target, _):
        return target

    @classmethod
    def _to_source_target(cls, value, _):
        source = models.Source.objects.filter(bidder_slug=value).only("id").first()

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target, _):
        return models.Source.objects.filter(id=int(target)).only("bidder_slug").first().bidder_slug

    @classmethod
    def _to_operating_system_target(cls, value, modifier_type):
        return cls._to_constant_target(value, modifier_type)

    @classmethod
    def _from_operating_system_target(cls, target, modifier_type):
        return cls._from_constant_target(target, modifier_type)

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
    def _to_country_target(cls, value, _):
        return cls._to_geolocation_target(dash_constants.LocationType.COUNTRY, value)

    @classmethod
    def _from_country_target(cls, target, _):
        return cls._from_geolocation_target(dash_constants.LocationType.COUNTRY, target)

    @classmethod
    def _to_state_target(cls, value, _):
        return cls._to_geolocation_target(dash_constants.LocationType.REGION, value)

    @classmethod
    def _from_state_target(cls, target, _):
        return cls._from_geolocation_target(dash_constants.LocationType.REGION, target)

    @classmethod
    def _to_dma_target(cls, value, _):
        return cls._to_geolocation_target(dash_constants.LocationType.DMA, value)

    @classmethod
    def _from_dma_target(cls, target, _):
        return cls._from_geolocation_target(dash_constants.LocationType.DMA, target)

    @classmethod
    def _to_content_ad_target(cls, value, _):
        try:
            content_ad = models.ContentAd.objects.filter(id=value).only("id").first()
        except ValueError:
            raise exceptions.BidModifierTargetInvalid("Invalid Content Ad")

        if content_ad is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Content Ad")

        return str(content_ad.id)

    @classmethod
    def _from_content_ad_target(cls, target, _):
        return target

    @classmethod
    def _to_constant_target(cls, value, modifier_type):
        constant, name = helpers.modifier_type_to_constant_dimension(modifier_type)

        constant_value = constant.get_constant_value(value)
        if constant_value is None:
            raise exceptions.BidModifierTargetInvalid("Invalid {}".format(name))

        return str(constant_value)

    @classmethod
    def _from_constant_target(clas, target, modifier_type):
        constant, _ = helpers.modifier_type_to_constant_dimension(modifier_type)
        return constant.get_name(int(target) if isinstance(target, str) and target.isnumeric() else target)


class FileConverter(TargetConverter):
    pass

    @classmethod
    def _to_operating_system_target(cls, value, modifier_type):
        # map legacy file operating system values
        converted_legacy_value = dash_constants.OperatingSystem.get_value(value)
        if converted_legacy_value is not None:
            value = dash_constants.OperatingSystem.get_name(converted_legacy_value)

        return super()._to_operating_system_target(value, modifier_type)


class ApiConverter(TargetConverter):
    pass


class DashboardConverter(TargetConverter):
    @classmethod
    def _to_operating_system_target(cls, value, _):
        if value == "WinPhone":
            value = "Windows Phone"

        operating_system = dash_constants.OperatingSystem.get_value(value)
        if operating_system is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Operating System")

        return operating_system

    @classmethod
    def _from_operating_system_target(cls, target, _):
        value = dash_constants.OperatingSystem.get_text(target)
        if not value:
            raise ValueError("Invalid Operating System")

        if value == "Windows Phone":
            value = "WinPhone"

        return value

    @classmethod
    def _to_dma_target(cls, value, modifier_type):
        return TargetConverter._to_dma_target(str(value), modifier_type)

    @classmethod
    def _from_dma_target(cls, target, _):
        return int(target)

    @classmethod
    def _to_source_target(cls, value, _):
        try:
            return str(models.Source.objects.filter(name=value).only("id").get().id)
        except (models.Source.DoesNotExist, models.Source.MultipleObjectsReturned):
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

    @classmethod
    def _from_source_target(cls, target, _):
        return models.Source.objects.filter(id=int(target)).only("name").get().name

    @classmethod
    def _to_constant_target(cls, value, modifier_type):
        constant, name = helpers.modifier_type_to_constant_dimension(modifier_type)
        constant_text = constant.get_text(value)
        if constant_text is None:
            raise exceptions.BidModifierTargetInvalid("Invalid {}".format(name))

        return str(value)

    @classmethod
    def _from_constant_target(clas, target, modifier_type):
        constant, _ = helpers.modifier_type_to_constant_dimension(modifier_type)
        constant.get_name(int(target) if isinstance(target, str) and target.isnumeric() else target)
        return int(target) if isinstance(target, str) and target.isnumeric() else target


class StatsConverter(TargetConverter):
    @classmethod
    def _to_constant_target(cls, value, modifier_type):
        return DashboardConverter._to_constant_target(value, modifier_type)

    @classmethod
    def _from_constant_target(cls, target, modifier_type):
        return DashboardConverter._from_constant_target(target, modifier_type)

    @classmethod
    def _to_operating_system_target(cls, value, modifier_type):
        return DashboardConverter._to_operating_system_target(value, modifier_type)

    @classmethod
    def _from_operating_system_target(cls, target, modifier_type):
        return DashboardConverter._from_operating_system_target(target, modifier_type)

    @classmethod
    def _to_source_target(cls, value, _):
        source = models.Source.objects.filter(id=value).only("id").first()

        if source is None:
            raise exceptions.BidModifierTargetInvalid("Invalid Source")

        return str(source.id)

    @classmethod
    def _from_source_target(cls, target, _):
        return str(target)
