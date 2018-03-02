from django.db import models

import core.entity
from . import constants

from utils import k1_helper


class CampaignStopState(models.Model):
    campaign = models.OneToOneField(core.entity.Campaign)
    almost_depleted = models.BooleanField(default=False)
    state = models.IntegerField(
        choices=constants.CampaignStopState.get_choices(),
        default=constants.CampaignStopState.STOPPED,
    )
    max_allowed_end_date = models.DateField(null=True, blank=True, default=None)
    pending_budget_updates = models.BooleanField(default=False)

    def set_allowed_to_run(self, is_allowed):
        previous = self.state
        self.state = constants.CampaignStopState.STOPPED
        if is_allowed:
            self.state = constants.CampaignStopState.ACTIVE

        if previous == constants.CampaignStopState.ACTIVE and\
           self.state == constants.CampaignStopState.STOPPED:
            self.almost_depleted = False

        self.save()

        if self.state != previous:
            ad_group_ids = self.campaign.adgroup_set.all().exclude_archived().values_list('id', flat=True)
            k1_helper.update_ad_groups(
                ad_group_ids,
                'campaignstop.status_change',
                priority=True
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

    def update_almost_depleted(self, is_depleted):
        self.almost_depleted = is_depleted
        self.save()

    def update_pending_budget_updates(self, pending_updates):
        self.pending_budget_updates = pending_updates
        self.save()

    def __str__(self):
        return '{} ({}) (state: {}, almost_depleted: {}, max_allowed_end_date: {})'.format(
            self.campaign.name,
            self.campaign.id,
            self.state,
            self.almost_depleted,
            self.max_allowed_end_date
        )
