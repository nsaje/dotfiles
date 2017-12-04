from django.db import models

import core.entity
import constants

from utils import k1_helper


class CampaignStopState(models.Model):
    campaign = models.OneToOneField(core.entity.Campaign)
    state = models.IntegerField(
        choices=constants.CampaignStopState.get_choices(),
        default=constants.CampaignStopState.STOPPED,
    )

    def set_allowed_to_run(self, is_allowed):
        previous = self.state
        self.state = constants.CampaignStopState.STOPPED
        if is_allowed:
            self.state = constants.CampaignStopState.ACTIVE
        self.save()

        if self.state != previous:
            ad_group_ids = self.campaign.adgroup_set.all().exclude_archived().values_list('id', flat=True)
            k1_helper.update_ad_groups(
                ad_group_ids,
                'campaignstop.status_change'
            )
