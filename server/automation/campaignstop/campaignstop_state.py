from django.db import models

import core.models
import dash.constants
import zemauth.models
from utils import dates_helper
from utils import email_helper
from utils import k1_helper
from utils import url_helper
from utils import zlogging

from . import constants

logger = zlogging.getLogger(__name__)


class CampaignStopState(models.Model):
    campaign = models.OneToOneField(core.models.Campaign, on_delete=models.CASCADE)
    almost_depleted = models.BooleanField(default=False)
    state = models.IntegerField(
        choices=constants.CampaignStopState.get_choices(), default=constants.CampaignStopState.STOPPED
    )
    max_allowed_end_date = models.DateField(null=True, blank=True, default=None)
    min_allowed_start_date = models.DateField(null=True, blank=True, default=None)
    pending_budget_updates = models.BooleanField(default=False)
    almost_depleted_marked_dt = models.DateTimeField(null=True, blank=True)

    def set_allowed_to_run(self, is_allowed):
        previous = self.state
        self.state = constants.CampaignStopState.STOPPED
        if is_allowed:
            self.state = constants.CampaignStopState.ACTIVE

        if previous == constants.CampaignStopState.ACTIVE and self.state == constants.CampaignStopState.STOPPED:
            self.almost_depleted = False

        self.save()

        if self.state != previous:
            from .service import update_notifier

            update_notifier.notify_campaignstopstate_change(self.campaign)
            self._ping_k1_for_ad_groups("campaignstop.status_change", priority=True)

    def update_max_allowed_end_date(self, max_allowed_end_date):
        previous = self.max_allowed_end_date
        self.max_allowed_end_date = max_allowed_end_date
        self.save()

        if self.max_allowed_end_date != previous:
            self._ping_k1_for_ad_groups("campaignstop.end_date_change")

    def update_min_allowed_start_date(self, min_allowed_start_date):
        previous = self.min_allowed_start_date
        self.min_allowed_start_date = min_allowed_start_date
        self.save()

        if self.min_allowed_start_date != previous:
            self._ping_k1_for_ad_groups("campaignstop.start_date_change")

    def _ping_k1_for_ad_groups(self, message, priority=False):
        ad_groups = self.campaign.adgroup_set.all().exclude_archived().only("id")
        k1_helper.update_ad_groups(ad_groups, message, priority=priority)

    def update_almost_depleted(self, is_depleted):
        if is_depleted and not self.almost_depleted:
            self.almost_depleted_marked_dt = dates_helper.utc_now()
            self._send_budget_almost_depleted_email()
        self.almost_depleted = is_depleted
        self.save()

    def _send_budget_almost_depleted_email(self):
        manager_list = email_helper.email_manager_list(self.campaign)
        if not manager_list:
            return

        args = {
            "campaign": self.campaign,
            "account": self.campaign.account,
            "link_url": url_helper.get_full_z1_url(
                "/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings".format(
                    self.campaign.pk
                )
            ),
        }
        try:
            email_helper.send_official_email(
                recipient_list=manager_list,
                agency_or_user=zemauth.models.User.objects.get(email=manager_list[0]),
                **email_helper.params_from_template(dash.constants.EmailTemplateType.CAMPAIGNSTOP_DEPLETING, **args)
            )
        except Exception:
            logger.exception("Exception while sending campaign stop email")

    def update_pending_budget_updates(self, pending_updates):
        self.pending_budget_updates = pending_updates
        self.save()

    def __str__(self):
        return "{} ({}) (state: {}, almost_depleted: {}, min_allowed_start_date: {}, max_allowed_end_date: {}, pending_budget_updates: {})".format(
            self.campaign.name,
            self.campaign.id,
            self.state,
            self.almost_depleted,
            self.min_allowed_start_date,
            self.max_allowed_end_date,
            self.pending_budget_updates,
        )
