from django.db import models

import core.entity
import constants


class CampaignStopState(models.Model):
    campaign = models.OneToOneField(core.entity.Campaign)
    state = models.IntegerField(
        choices=constants.CampaignStopState.get_choices(),
        default=constants.CampaignStopState.STOPPED,
    )

    def set_allowed_to_run(self, is_allowed):
        self.state = constants.CampaignStopState.STOPPED
        if is_allowed:
            self.state = constants.CampaignStopState.ACTIVE
        self.save()
