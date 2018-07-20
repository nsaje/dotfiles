from django.db import models
from django.contrib.postgres.fields import JSONField

import core.entity
from . import constants

from utils import json_helper


class RealTimeCampaignStopLog(models.Model):
    event = models.IntegerField(choices=constants.CampaignStopEvent.get_choices())
    campaign = models.ForeignKey(core.entity.Campaign)
    context = JSONField(encoder=json_helper.JSONEncoder)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)

    def add_context(self, d):
        if not self.context:
            self.context = {}
        self.context.update(d)
        self.save()
