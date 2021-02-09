# -*- coding: utf-8 -*-
from collections import OrderedDict

import jsonfield
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models

import core.common
import core.features.audiences
import core.features.history
import core.models
import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from .. import helpers
from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from . import instance
from . import manager
from . import validation


class CampaignSettings(validation.CampaignSettingsValidatorMixin, instance.CampaignSettingsMixin, SettingsBase):
    class Meta:
        app_label = "dash"
        ordering = ("-created_dt",)

    objects = manager.CampaignSettingsManager()

    _demo_fields = {"name": utils.demo_anonymizer.campaign_name_from_pool}
    _settings_fields = [
        "name",
        "campaign_manager",
        "language",
        "iab_category",
        "campaign_goal",
        "promotion_goal",
        "archived",
        "target_devices",
        "target_os",
        "target_environments",
        "target_regions",
        "exclusion_target_regions",
        "autopilot",
        "enable_ga_tracking",
        "ga_tracking_type",
        "ga_property_id",
        "enable_adobe_tracking",
        "adobe_tracking_param",
        "whitelist_publisher_groups",
        "blacklist_publisher_groups",
        "frequency_capping",
    ]
    _clone_fields = [
        "campaign_manager",
        "language",
        "iab_category",
        "campaign_goal",
        "target_devices",
        "target_os",
        "target_environments",
        "target_regions",
        "exclusion_target_regions",
        "autopilot",
        "enable_ga_tracking",
        "ga_tracking_type",
        "ga_property_id",
        "enable_adobe_tracking",
        "adobe_tracking_param",
        "whitelist_publisher_groups",
        "blacklist_publisher_groups",
        "frequency_capping",
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, blank=False, null=False)
    campaign = models.ForeignKey("Campaign", on_delete=models.PROTECT)
    system_user = models.PositiveSmallIntegerField(
        choices=constants.SystemUserType.get_choices(), null=True, blank=True
    )
    campaign_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT
    )
    language = models.SlugField(default=constants.Language.ENGLISH, choices=constants.Language.get_choices(), null=True)
    iab_category = models.SlugField(
        max_length=10, default=constants.IABCategory.IAB24, choices=constants.IABCategory.get_choices()
    )
    promotion_goal = models.IntegerField(
        default=constants.PromotionGoal.BRAND_BUILDING, choices=constants.PromotionGoal.get_choices()
    )
    campaign_goal = models.IntegerField(
        default=constants.CampaignGoal.NEW_UNIQUE_VISITORS, choices=constants.CampaignGoal.get_choices()
    )
    goal_quantity = models.DecimalField(  # deprecated
        max_digits=20, decimal_places=2, blank=False, null=False, default=0
    )

    target_devices = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    target_environments = ArrayField(models.CharField(max_length=24), null=True, blank=True, verbose_name="Environment")
    target_os = JSONField(null=True, blank=True, verbose_name="Operating Systems")

    target_regions = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)
    exclusion_target_regions = jsonfield.JSONField(
        blank=True, null=False, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS
    )

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    automatic_campaign_stop = models.NullBooleanField(default=True, null=True, blank=True)
    landing_mode = models.NullBooleanField(default=False, blank=True, null=True)
    autopilot = models.BooleanField(default=False)

    enable_ga_tracking = models.BooleanField(default=True)
    ga_tracking_type = models.IntegerField(
        default=constants.GATrackingType.EMAIL, choices=constants.GATrackingType.get_choices()
    )
    ga_property_id = models.CharField(max_length=25, blank=True, default="")
    enable_adobe_tracking = models.BooleanField(default=False)
    adobe_tracking_param = models.CharField(max_length=10, blank=True, default="")

    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    frequency_capping = models.PositiveIntegerField(blank=True, null=True)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.campaign.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user,
        )

    def get_changes_text(self, changes, separator=", "):
        return core.features.history.helpers.get_changes_text_from_dict(self, changes, separator=separator)

    class QuerySet(SettingsQuerySet):
        pass

    @classmethod
    def get_defaults_dict(cls):
        return OrderedDict([("target_devices", constants.AdTargetDevice.get_all())])

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "name": "Name",
            "campaign_manager": "Campaign Manager",
            "language": "Language",
            "iab_category": "IAB Category",
            "campaign_goal": "Campaign Goal",
            "promotion_goal": "Promotion Goal",
            "archived": "Archived",
            "target_devices": "Device targeting",
            "target_environments": "Environment",
            "target_os": "Operating Systems",
            "target_regions": "Locations",
            "exclusion_target_regions": "Excluded Locations",
            "autopilot": "Campaign Budget Optimization",
            "enable_ga_tracking": "Enable GA tracking",
            "ga_tracking_type": "GA tracking type (via API or e-mail).",
            "ga_property_id": "GA web property ID",
            "enable_adobe_tracking": "Enable Adobe tracking",
            "adobe_tracking_param": "Adobe tracking parameter",
            "whitelist_publisher_groups": "Whitelist publisher groups",
            "blacklist_publisher_groups": "Blacklist publisher groups",
            "frequency_capping": "Frequency Capping",
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == "campaign_manager":
            # FIXME: circular dependency
            import dash.views.helpers

            value = dash.views.helpers.get_user_full_name_or_email(value)
        elif prop_name == "language":
            value = constants.Language.get_text(value)
        elif prop_name == "iab_category":
            value = constants.IABCategory.get_text(value)
        elif prop_name == "campaign_goal":
            value = constants.CampaignGoal.get_text(value)
        elif prop_name == "promotion_goal":
            value = constants.PromotionGoal.get_text(value)
        elif prop_name == "target_devices":
            value = ", ".join(constants.AdTargetDevice.get_text(x) for x in value)
        elif prop_name == "target_environments":
            value = ", ".join(constants.Environment.get_text(x) for x in value) if value else ""
        elif prop_name == "target_os":
            value = ", ".join(helpers.get_human_value_target_os(x) for x in value) if value else ""
        elif prop_name in ("target_regions", "exclusion_target_regions"):
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
        elif prop_name == "autopilot":
            value = str(value)
        elif prop_name == "archived":
            value = str(value)
        elif prop_name == "ga_tracking_type":
            value = constants.GATrackingType.get_text(value)
        elif prop_name in ("whitelist_publisher_groups", "blacklist_publisher_groups"):
            if not value:
                value = ""
            else:
                names = core.features.publisher_groups.PublisherGroup.objects.filter(pk__in=value).values_list(
                    "name", flat=True
                )
                value = ", ".join(names)

        return value
