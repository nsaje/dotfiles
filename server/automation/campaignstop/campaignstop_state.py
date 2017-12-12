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
    max_allowed_end_date = models.DateField(null=True, blank=True, default=None)

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

    def update_max_allowed_end_date(self, max_allowed_end_date):
        previous = self.max_allowed_end_date
        self.max_allowed_end_date = max_allowed_end_date
        self.save()

        if self.max_allowed_end_date != previous:
            ad_group_ids = self.campaign.adgroup_set.all().exclude_archived().values_list('id', flat=True)
            k1_helper.update_ad_groups(
                ad_group_ids,
                'campaignstop.end_date_change'
            )
