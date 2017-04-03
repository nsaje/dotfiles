# -*- coding: utf-8 -*-

from decimal import Decimal

from django.conf import settings
from django.db import models

from dash import constants


class CampaignGoal(models.Model):
    class Meta:
        app_label = 'dash'
        unique_together = ('campaign', 'type', 'conversion_goal')

    campaign = models.ForeignKey('Campaign')
    type = models.PositiveSmallIntegerField(
        default=constants.CampaignGoalKPI.TIME_ON_SITE,
        choices=constants.CampaignGoalKPI.get_choices(),
    )
    primary = models.BooleanField(default=False)
    conversion_goal = models.ForeignKey(
        'ConversionGoal', null=True, blank=True, on_delete=models.PROTECT)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    def to_dict(self, with_values=False):
        campaign_goal = {
            'campaign_id': self.campaign.id,
            'type': self.type,
            'primary': self.primary,
            'id': self.pk,
            'conversion_goal': None,
        }

        if self.conversion_goal:
            campaign_goal['conversion_goal'] = {
                'id': self.conversion_goal.pk,
                'type': self.conversion_goal.type,
                'name': self.conversion_goal.name,
                'conversion_window': self.conversion_goal.conversion_window,
                'goal_id': self.conversion_goal.goal_id,
                'pixel_url': None,
            }
            if self.conversion_goal.pixel:
                campaign_goal['conversion_goal'][
                    'goal_id'] = self.conversion_goal.pixel.id

        if with_values:
            default_rounding_format = '1.00'
            rounding_format = {
                constants.CampaignGoalKPI.CPC: '1.000'
            }

            campaign_goal['values'] = [
                {'datetime': str(value.created_dt),
                 'value': Decimal(value.value).quantize(Decimal(
                     rounding_format.get(self.type, default_rounding_format)
                 ))}
                for value in self.values.all()
            ]

        return campaign_goal

    def get_view_key(self):
        return 'campaign_goal_' + str(self.id)
