# -*- coding: utf-8 -*-
from collections import OrderedDict

import jsonfield
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

import utils.demo_anonymizer
import utils.string_helper
from dash import constants

import core.audiences
import core.common
import core.entity
import core.history
import core.source

from settings_base import SettingsBase
from settings_query_set import SettingsQuerySet


class CampaignSettings(SettingsBase):
    class Meta:
        app_label = 'dash'
        ordering = ('-created_dt',)

    _demo_fields = {
        'name': utils.demo_anonymizer.campaign_name_from_pool
    }
    _settings_fields = [
        'name',
        'campaign_manager',
        'iab_category',
        'campaign_goal',
        'goal_quantity',
        'promotion_goal',
        'archived',
        'target_devices',
        'target_regions',
        'exclusion_target_regions',
        'automatic_campaign_stop',
        'landing_mode',
        'enable_ga_tracking',
        'ga_tracking_type',
        'ga_property_id',
        'enable_adobe_tracking',
        'adobe_tracking_param',
        'whitelist_publisher_groups',
        'blacklist_publisher_groups',
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(
        core.entity.Campaign, related_name='settings', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT,
                                   null=True, blank=True)
    system_user = models.PositiveSmallIntegerField(choices=constants.SystemUserType.get_choices(),
                                                   null=True, blank=True)
    campaign_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    iab_category = models.SlugField(
        max_length=10,
        default=constants.IABCategory.IAB24,
        choices=constants.IABCategory.get_choices()
    )
    promotion_goal = models.IntegerField(
        default=constants.PromotionGoal.BRAND_BUILDING,
        choices=constants.PromotionGoal.get_choices()
    )
    campaign_goal = models.IntegerField(
        default=constants.CampaignGoal.NEW_UNIQUE_VISITORS,
        choices=constants.CampaignGoal.get_choices()
    )
    goal_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=False,
        null=False,
        default=0
    )
    target_devices = jsonfield.JSONField(blank=True, default=[])
    target_regions = jsonfield.JSONField(blank=True, default=[])
    exclusion_target_regions = jsonfield.JSONField(blank=True, null=False, default=[])

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    automatic_campaign_stop = models.BooleanField(default=True)
    landing_mode = models.BooleanField(default=False)

    enable_ga_tracking = models.BooleanField(default=True)
    ga_tracking_type = models.IntegerField(
        default=constants.GATrackingType.EMAIL,
        choices=constants.GATrackingType.get_choices()
    )
    ga_property_id = models.CharField(max_length=25, blank=True, default='')
    enable_adobe_tracking = models.BooleanField(default=False)
    adobe_tracking_param = models.CharField(
        max_length=10, blank=True, default='')

    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    objects = core.common.QuerySetManager()

    def save(self,
             request,
             action_type=None,
             *args, **kwargs):
        if self.pk is None:
            if request is None:
                self.created_by = None
            else:
                self.created_by = request.user
        super(CampaignSettings, self).save(*args, **kwargs)
        self.add_to_history(request and request.user, action_type)

    def add_to_history(self, user, action_type):
        changes = self.get_model_state_changes(
            self.get_settings_dict()
        )
        changes_text = self.get_changes_text_from_dict(changes)
        self.campaign.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user
        )

    @classmethod
    def get_changes_text(cls, old_settings, new_settings, separator=', '):
        changes = old_settings.get_setting_changes(
            new_settings) if old_settings is not None else None
        return core.history.helpers.get_changes_text_from_dict(cls, changes, separator=separator)

    class QuerySet(SettingsQuerySet):

        def group_current_settings(self):
            return self.order_by('campaign_id', '-created_dt').distinct('campaign')

    @classmethod
    def get_defaults_dict(cls):
        return OrderedDict([
            ('target_devices', constants.AdTargetDevice.get_all()),
            ('target_regions', ['US'])
        ])

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'name': 'Name',
            'campaign_manager': 'Campaign Manager',
            'iab_category': 'IAB Category',
            'campaign_goal': 'Campaign Goal',
            'goal_quantity': 'Goal Quantity',
            'promotion_goal': 'Promotion Goal',
            'archived': 'Archived',
            'target_devices': 'Device targeting',
            'target_regions': 'Locations',
            'exclusion_target_regions': 'Excluded Locations',
            'automatic_campaign_stop': 'Automatic Campaign Stop',
            'landing_mode': 'Landing Mode',
            'enable_ga_tracking': 'Enable GA tracking',
            'ga_tracking_type': 'GA tracking type (via API or e-mail).',
            'ga_property_id': 'GA web property ID',
            'enable_adobe_tracking': 'Enable Adobe tracking',
            'adobe_tracking_param': 'Adobe tracking parameter',
            'whitelist_publisher_groups': 'Whitelist publisher groups',
            'blacklist_publisher_groups': 'Blacklist publisher groups',
        }

        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'campaign_manager':
            # FIXME: circular dependency
            import dash.views.helpers
            value = dash.views.helpers.get_user_full_name_or_email(
                value).decode('utf-8')
        elif prop_name == 'iab_category':
            value = constants.IABCategory.get_text(value)
        elif prop_name == 'campaign_goal':
            value = constants.CampaignGoal.get_text(value)
        elif prop_name == 'promotion_goal':
            value = constants.PromotionGoal.get_text(value)
        elif prop_name == 'target_devices':
            value = ', '.join(constants.AdTargetDevice.get_text(x)
                              for x in value)
        elif prop_name in ('target_regions', 'exclusion_target_regions'):
            if value:
                # FIXME: circular dependency
                import dash.features.geolocation
                names = list(dash.features.geolocation.Geolocation.objects
                             .filter(key__in=value).values_list('name', flat=True))
                zips = [v for v in value if ':' in v]
                if zips:
                    names.append('%s postal codes' % len(zips))
                value = '; '.join(names)
            else:
                if prop_name == 'target_regions':
                    value = 'worldwide'
                elif prop_name == 'exclusion_target_regions':
                    value = 'none'
        elif prop_name == 'automatic_campaign_stop':
            value = str(value)
        elif prop_name == 'landing_mode':
            value = str(value)
        elif prop_name == 'archived':
            value = str(value)
        elif prop_name == 'ga_tracking_type':
            value = constants.GATrackingType.get_text(value)
        elif prop_name in ('whitelist_publisher_groups', 'blacklist_publisher_groups'):
            if not value:
                value = ''
            else:
                # FIXME: circular dependency
                import core.entity.settings
                names = core.entity.settings.PublisherGroup.objects.filter(pk__in=value).values_list('name', flat=True)
                value = ', '.join(names)

        return value
