from django.contrib.postgres.fields import JSONField
from django.db import models

import core.models
from utils import json_helper

from . import constants


class RealTimeCampaignStopLog(models.Model):
    event = models.IntegerField(choices=constants.CampaignStopEvent.get_choices(), db_index=True)
    campaign = models.ForeignKey(core.models.Campaign, on_delete=models.CASCADE)
    context = JSONField(encoder=json_helper.JSONEncoder)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)

    def add_context(self, d):
        if not self.context:
            self.context = {}
        self.context.update(d)
        self.save()
