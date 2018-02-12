# -*- coding: utf-8 -*-

from django.db import models

from dash import constants
import dash.models
import dash.features.performance_tracking.constants

from . import manager
from . import validator


class ConversionGoal(validator.ConversionGoalValidator, models.Model):
    class Meta:
        app_label = 'dash'
        unique_together = (('campaign', 'name'),
                           ('campaign', 'type', 'goal_id'))
        ordering = ['pk']

    campaign = models.ForeignKey('Campaign', on_delete=models.PROTECT)
    type = models.PositiveSmallIntegerField(
        choices=constants.ConversionGoalType.get_choices()
    )
    name = models.CharField(max_length=100)

    pixel = models.ForeignKey(
        'ConversionPixel', null=True, on_delete=models.PROTECT, blank=True)
    conversion_window = models.PositiveSmallIntegerField(null=True, blank=True)
    goal_id = models.CharField(max_length=100, null=True, blank=True)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created on')

    objects = manager.ConversionGoalManager()

    def get_stats_key(self):
        # map conversion goal to the key under which they are stored in stats
        # database
        if self.type == constants.ConversionGoalType.GA:
            prefix = dash.features.performance_tracking.constants.ReportType.GOOGLE_ANALYTICS
        elif self.type == constants.ConversionGoalType.OMNITURE:
            prefix = dash.features.performance_tracking.constants.ReportType.OMNITURE
        else:
            raise Exception('Invalid conversion goal type')

        return prefix + '__' + self.goal_id

    def get_view_key(self, conversion_goals):
        if self.type == constants.ConversionGoalType.PIXEL:
            return self.pixel.get_view_key(self.conversion_window)

        for i, cg in enumerate(sorted(conversion_goals, key=lambda x: x.id)):
            if cg.id == self.id:
                return 'conversion_goal_' + str(i + 1)

        raise Exception('Conversion goal not found')
