import datetime
import json
from collections import OrderedDict
from decimal import Decimal

import jsonfield
import pytz
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models

import core.common
import core.features.audiences
import core.features.history
import core.features.multicurrency
import core.features.publisher_groups
import core.models
import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from dash import region_targeting_helper
from utils import dates_helper
from utils import lc_helper
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from . import instance
from . import manager
from . import queryset
from . import validation
from .. import helpers
from .. import multicurrency_mixin
from ..settings_base import SettingsBase


class AdGroupSettings(
    validation.AdGroupSettingsValidatorMixin,
    multicurrency_mixin.MulticurrencySettingsMixin,
    instance.AdGroupSettingsMixin,
    SettingsBase,
):
    class Meta:
        ordering = ("-created_dt",)
        permissions = (("settings_view", "Can view settings in dashboard."),)
        app_label = "dash"

    objects = manager.AdGroupSettingsManager()
    QuerySet = queryset.QuerySet

    _demo_fields = {
        "display_url": utils.demo_anonymizer.fake_display_url,
        "ad_group_name": utils.demo_anonymizer.ad_group_name_from_pool,
        "brand_name": utils.demo_anonymizer.fake_brand,
        "description": utils.demo_anonymizer.fake_sentence,
    }
    _settings_fields = [
        "ad_group_name",
        "state",
        "start_date",
        "end_date",
        "cpc_cc",
        "local_cpc_cc",
        "daily_budget_cc",
        "target_devices",
        "target_os",
        "target_browsers",
        "target_placements",
        "target_regions",
        "exclusion_target_regions",
        "retargeting_ad_groups",
        "exclusion_retargeting_ad_groups",
        "bluekai_targeting",
        "interest_targeting",
        "exclusion_interest_targeting",
        "audience_targeting",
        "exclusion_audience_targeting",
        "whitelist_publisher_groups",
        "blacklist_publisher_groups",
        "redirect_pixel_urls",
        "redirect_javascript",
        "notes",
        "tracking_code",
        "archived",
        "display_url",
        "brand_name",
        "description",
        "call_to_action",
        "autopilot_state",
        "autopilot_daily_budget",
        "local_autopilot_daily_budget",
        "b1_sources_group_enabled",
        "b1_sources_group_daily_budget",
        "local_b1_sources_group_daily_budget",
        "b1_sources_group_cpc_cc",
        "local_b1_sources_group_cpc_cc",
        "b1_sources_group_cpm",
        "local_b1_sources_group_cpm",
        "b1_sources_group_state",
        "dayparting",
        "max_cpm",
        "local_max_cpm",
        "delivery_type",
        "click_capping_daily_ad_group_max_clicks",
        "click_capping_daily_click_budget",
        "frequency_capping",
    ]
    _permissioned_fields = {
        "click_capping_daily_ad_group_max_clicks": "zemauth.can_set_click_capping",
        "click_capping_daily_click_budget": "zemauth.can_set_click_capping",
        "max_cpm": "zemauth.fea_can_use_cpm_buying",
        "local_max_cpm": "zemauth.fea_can_use_cpm_buying",
        "b1_sources_group_cpm": "zemauth.fea_can_use_cpm_buying",
        "local_b1_sources_group_cpm": "zemauth.fea_can_use_cpm_buying",
        "frequency_capping": "zemauth.can_set_frequency_capping",
    }
    multicurrency_fields = [
        "cpc_cc",
        "max_cpm",
        "autopilot_daily_budget",
        "b1_sources_group_daily_budget",
        "b1_sources_group_cpc_cc",
        "b1_sources_group_cpm",
    ]
    history_fields = list(set(_settings_fields) - set(multicurrency_fields))

    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(core.models.AdGroup, on_delete=models.PROTECT)
    system_user = models.PositiveSmallIntegerField(
        choices=constants.SystemUserType.get_choices(), null=True, blank=True
    )
    state = models.IntegerField(
        default=constants.AdGroupSettingsState.INACTIVE, choices=constants.AdGroupSettingsState.get_choices()
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPC"
    )  # max CPC
    local_cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPC"
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Daily spend cap"
    )

    target_devices = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    target_placements = ArrayField(models.CharField(max_length=24), null=True, blank=True, verbose_name="Placement")
    target_os = JSONField(null=True, blank=True, verbose_name="Operating System")
    target_browsers = JSONField(null=True, blank=True, verbose_name="Browsers")

    target_regions = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    exclusion_target_regions = jsonfield.JSONField(
        blank=True, null=False, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS
    )
    retargeting_ad_groups = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    exclusion_retargeting_ad_groups = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    bluekai_targeting = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)

    interest_targeting = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    exclusion_interest_targeting = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    audience_targeting = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    exclusion_audience_targeting = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    redirect_pixel_urls = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    redirect_javascript = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tracking_code = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    display_url = models.CharField(max_length=25, blank=True, default="")
    brand_name = models.CharField(max_length=25, blank=True, default="")
    description = models.CharField(max_length=140, blank=True, default="")
    call_to_action = models.CharField(max_length=25, blank=True, default="")
    ad_group_name = models.CharField(max_length=127, blank=True, default="")
    autopilot_state = models.IntegerField(
        blank=True,
        null=True,
        default=constants.AdGroupSettingsAutopilotState.INACTIVE,
        choices=constants.AdGroupSettingsAutopilotState.get_choices(),
    )
    autopilot_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Autopilot's Daily Spend Cap", default=0
    )
    local_autopilot_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Autopilot's Daily Spend Cap", default=0
    )
    landing_mode = models.NullBooleanField(default=False, blank=True, null=True)

    changes_text = models.TextField(blank=True, null=True)

    # MVP for all-RTB-sources-as-one
    b1_sources_group_enabled = models.BooleanField(default=False)
    b1_sources_group_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Bidder's Daily Cap", default=0
    )
    local_b1_sources_group_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Bidder's Daily Cap", blank=True, null=True, default=0
    )
    # TODO (multicurrency): Handle fields' default values for local fields
    b1_sources_group_cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, default=core.models.AllRTBSourceType.min_cpc, verbose_name="Bidder's Bid CPC"
    )
    local_b1_sources_group_cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Bidder's Bid CPC", blank=True, null=True
    )
    b1_sources_group_cpm = models.DecimalField(
        max_digits=10, decimal_places=4, default=core.models.AllRTBSourceType.min_cpm, verbose_name="Bidder's Bid CPM"
    )
    local_b1_sources_group_cpm = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Bidder's Bid CPM", blank=True, null=True
    )
    b1_sources_group_state = models.IntegerField(
        default=constants.AdGroupSourceSettingsState.INACTIVE,
        choices=constants.AdGroupSourceSettingsState.get_choices(),
    )

    dayparting = jsonfield.JSONField(blank=True, default=dict, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    max_cpm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPM")
    local_max_cpm = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPM"
    )

    delivery_type = models.IntegerField(
        default=constants.AdGroupDeliveryType.STANDARD, choices=constants.AdGroupDeliveryType.get_choices()
    )

    click_capping_daily_ad_group_max_clicks = models.PositiveIntegerField(blank=True, null=True)

    click_capping_daily_click_budget = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)

    frequency_capping = models.PositiveIntegerField(blank=True, null=True)

    @classmethod
    def get_defaults_dict(cls, currency=None):
        defaults = OrderedDict(
            [
                ("state", constants.AdGroupSettingsState.INACTIVE),
                ("start_date", dates_helper.utc_today()),
                ("cpc_cc", None),
                ("max_cpm", None),
                ("daily_budget_cc", 10.0000),
                ("target_devices", constants.AdTargetDevice.get_all()),
                ("target_regions", ["US"]),
                ("exclusion_target_regions", []),
                ("autopilot_state", constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET),
                ("autopilot_daily_budget", Decimal("100.00")),
                ("b1_sources_group_enabled", True),
                ("b1_sources_group_state", constants.AdGroupSourceSettingsState.ACTIVE),
                ("b1_sources_group_daily_budget", Decimal("50.00")),
                ("b1_sources_group_cpc_cc", Decimal("0.45")),
                ("b1_sources_group_cpm", Decimal("1.00")),
            ]
        )

        exchange_rate = Decimal("1.0")
        if currency:
            exchange_rate = core.features.multicurrency.get_current_exchange_rate(currency)
        for field in cls.multicurrency_fields:
            if not defaults.get(field):
                continue
            defaults["local_%s" % field] = defaults[field] * exchange_rate

        return defaults

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "start_date": "Start date",
            "end_date": "End date",
            "cpc_cc": "Max CPC bid",
            "local_cpc_cc": "Max CPC bid",
            "max_cpm": "Max CPM bid",
            "local_max_cpm": "Max CPM bid",
            "daily_budget_cc": "Daily spend cap",
            "target_devices": "Device targeting",
            "target_placements": "Placement",
            "target_os": "Operating Systems",
            "target_browsers": "Browser targeting",
            "target_regions": "Locations",
            "exclusion_target_regions": "Excluded Locations",
            "retargeting_ad_groups": "Retargeting ad groups",
            "exclusion_retargeting_ad_groups": "Exclusion ad groups",
            "whitelist_publisher_groups": "Whitelist publisher groups",
            "blacklist_publisher_groups": "Blacklist publisher groups",
            "bluekai_targeting": "Data targeting",
            "interest_targeting": "Interest targeting",
            "exclusion_interest_targeting": "Exclusion interest targeting",
            "audience_targeting": "Custom audience targeting",
            "exclusion_audience_targeting": "Exclusion custom audience targeting",
            "redirect_pixel_urls": "Pixel retargeting tags",
            "redirect_javascript": "Pixel retargeting JavaScript",
            "notes": "Notes",
            "tracking_code": "Tracking code",
            "state": "State",
            "archived": "Archived",
            "display_url": "Display URL",
            "brand_name": "Brand name",
            "description": "Description",
            "call_to_action": "Call to action",
            "ad_group_name": "Ad group name",
            "autopilot_state": "Autopilot",
            "autopilot_daily_budget": "Autopilot's Daily Spend Cap",
            "local_autopilot_daily_budget": "Autopilot's Daily Spend Cap",
            "dayparting": "Dayparting",
            "b1_sources_group_enabled": "Group all RTB sources",
            "b1_sources_group_daily_budget": "Daily budget for all RTB sources",
            "local_b1_sources_group_daily_budget": "Daily budget for all RTB sources",
            "b1_sources_group_cpc_cc": "Bid CPC for all RTB sources",
            "local_b1_sources_group_cpc_cc": "Bid CPC for all RTB sources",
            "b1_sources_group_cpm": "Bid CPM for all RTB sources",
            "local_b1_sources_group_cpm": "Bid CPM for all RTB sources",
            "b1_sources_group_state": "State of all RTB sources",
            "delivery_type": "Delivery type",
            "click_capping_daily_ad_group_max_clicks": "Daily maximum number of clicks for ad group",
            "click_capping_daily_click_budget": "Daily click budget for ad group",
            "frequency_capping": "Frequency Capping",
        }

        return NAMES[prop_name]

    def get_human_value(self, prop_name, value):
        currency_symbol = core.features.multicurrency.get_currency_symbol(self.get_currency())
        if prop_name == "state":
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == "autopilot_state":
            value = constants.AdGroupSettingsAutopilotState.get_text(value)
        elif prop_name == "local_autopilot_daily_budget" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=2, curr=currency_symbol)
        elif prop_name == "end_date" and value is None:
            value = "I'll stop it myself"
        elif prop_name == "local_cpc_cc" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "local_max_cpm" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "daily_budget_cc" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=2, curr=currency_symbol)
        elif prop_name == "target_devices":
            value = ", ".join(constants.AdTargetDevice.get_text(x) for x in value)
        elif prop_name == "target_placements":
            value = ", ".join(constants.Placement.get_text(x) for x in value) if value else ""
        elif prop_name == "target_os":
            value = ", ".join(helpers.get_human_value_target_os(x) for x in value) if value else ""
        elif prop_name == "target_browsers":
            value = ", ".join(constants.BrowserFamily.get_text(x["family"]) for x in value if "family" in x)
        elif prop_name in ("target_regions", "exclusion_target_regions"):
            value = AdGroupSettings._get_human_value_for_target_regions(prop_name, value)
        elif prop_name in ("retargeting_ad_groups", "exclusion_retargeting_ad_groups"):
            value = AdGroupSettings._get_human_value_for_retargeting_adgroups(value)
        elif prop_name in ("whitelist_publisher_groups", "blacklist_publisher_groups"):
            value = AdGroupSettings._get_human_value_for_publisher_groups(value)
        elif prop_name == "bluekai_targeting":
            value = json.dumps(value)
        elif prop_name in ("interest_targeting", "exclusion_interest_targeting"):
            value = AdGroupSettings._get_human_value_for_interests_targeting(value)
        elif prop_name in ("audience_targeting", "exclusion_audience_targeting"):
            value = AdGroupSettings._get_human_value_for_audience_targeting(value)
        elif prop_name == "redirect_pixel_urls":
            value = ", ".join(value)
        elif prop_name == "dayparting":
            value = AdGroupSettings._get_dayparting_human_value(value)
        elif prop_name == "b1_sources_group_state":
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == "local_b1_sources_group_daily_budget" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=2, curr=currency_symbol)
        elif prop_name == "local_b1_sources_group_cpc_cc" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "local_b1_sources_group_cpm" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "click_capping_daily_click_budget" and value is not None:
            value = lc_helper.default_currency(Decimal(value))

        return value

    @staticmethod
    def _get_human_value_for_target_regions(prop_name, value):
        if value:
            # FIXME: circular dependency
            import dash.features.geolocation

            names = list(
                dash.features.geolocation.Geolocation.objects.filter(key__in=value).values_list("name", flat=True)
            )
            zips = [v for v in value if ":" in v]
            if zips:
                names.append("%s postal codes" % len(zips))
            value = "; ".join(names)
        else:
            if prop_name == "target_regions":
                value = "worldwide"
            elif prop_name == "exclusion_target_regions":
                value = "none"
        return value

    @staticmethod
    def _get_human_value_for_retargeting_adgroups(value):
        if not value:
            value = ""
        else:
            names = core.models.AdGroup.objects.filter(pk__in=value).values_list("name", flat=True)
            value = ", ".join(names)
        return value

    @staticmethod
    def _get_human_value_for_publisher_groups(value):
        if not value:
            value = ""
        else:
            names = core.features.publisher_groups.PublisherGroup.objects.filter(pk__in=value).values_list(
                "name", flat=True
            )
            value = ", ".join(names)
        return value

    @staticmethod
    def _get_human_value_for_interests_targeting(value):
        if value:
            value = ", ".join(category.capitalize() for category in value)
        else:
            value = ""
        return value

    @staticmethod
    def _get_human_value_for_audience_targeting(value):
        if not value:
            value = ""
        else:
            names = core.features.audiences.Audience.objects.filter(pk__in=value).values_list("name", flat=True)
            value = ", ".join(names)
        return value

    @staticmethod
    def _get_dayparting_human_value(value):
        joined = []
        for k in value:
            if isinstance(value[k], list):
                val = ", ".join(str(v) for v in value[k])
            else:
                val = str(value[k])
            joined.append(k.capitalize() + ": " + val)
        value = "; ".join(joined)
        return value

    def get_changes_text(self, old_settings, new_settings, user, separator=", "):
        changes = old_settings.get_setting_changes(new_settings) if old_settings is not None else None
        if changes is None:
            return "Created settings"

        excluded_keys = set()
        if user is not None and not user.has_perm("zemauth.can_view_retargeting_settings"):
            excluded_keys.update(["retargeting_ad_groups", "exclusion_retargeting_ad_groups"])

        if user is not None and not user.has_perm("zemauth.can_set_white_blacklist_publisher_groups"):
            excluded_keys.update(["whitelist_publisher_groups", "blacklist_publisher_groups"])

        if user is not None and not user.has_perm("zemauth.can_set_advanced_device_targeting"):
            excluded_keys.update(["target_os", "target_placements"])

        valid_changes = {key: value for key, value in changes.items() if key not in excluded_keys}
        return core.features.history.helpers.get_changes_text_from_dict(self, valid_changes, separator=separator)

    def get_settings_dict(self):
        # ad group settings form expects 'name' instead of 'ad_group_name'
        settings_dict = super(AdGroupSettings, self).get_settings_dict()
        settings_dict["name"] = settings_dict["ad_group_name"]
        return settings_dict

    def _convert_date_utc_datetime(self, date):
        dt = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.timezone(settings.DEFAULT_TIME_ZONE))
        return dt.astimezone(pytz.timezone("UTC")).replace(tzinfo=None)

    def get_utc_start_datetime(self):
        if self.start_date is None:
            return None

        return self._convert_date_utc_datetime(self.start_date)

    def get_utc_end_datetime(self):
        if self.end_date is None:
            return None

        dt = self._convert_date_utc_datetime(self.end_date)
        dt += datetime.timedelta(days=1)
        return dt

    def targets_region_type(self, region_type):
        regions = region_targeting_helper.get_list_for_region_type(region_type)

        return any(target_region in regions for target_region in self.target_regions or [])

    def get_target_names_for_region_type(self, region_type):
        regions_of_type = region_targeting_helper.get_list_for_region_type(region_type)

        return [
            regions_of_type[target_region]
            for target_region in self.target_regions or []
            if target_region in regions_of_type
        ]

    def is_mobile_only(self):
        return (
            bool(self.target_devices)
            and len(self.target_devices) == 1
            and constants.AdTargetDevice.MOBILE in self.target_devices
        )

    def get_tracking_codes(self):
        # Strip the first '?' as we don't want to send it as a part of query
        # string
        return self.tracking_code.lstrip("?")
