from django.db import models

import core.models
from automation.campaignstop import constants


class CampaignEventProcessedAt(models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("campaign", "type")

    campaign = models.ForeignKey(core.models.Campaign, on_delete=models.CASCADE)
    type = models.TextField(choices=constants.CampaignUpdateType.get_choices(), blank=False, null=False)
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    def __str__(self):
        return "$(campaign: {} ({}), type {}, created dt: {})".format(
            self.campaign.name, self.campaign.id, self.type, self.created_dt
        )

    def update_modified_dt(self):
        self.save(None)
