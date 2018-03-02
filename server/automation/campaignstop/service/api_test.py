from django.test import TestCase

from .. import constants, CampaignStopState
from . import api
import core.entity
from utils import dates_helper
from utils.magic_mixer import magic_mixer


class GetCampaignStopStatesTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

    def test_default(self):
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': False,
            'max_allowed_end_date': dates_helper.local_yesterday(),
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[self.campaign.id])

    def test_states_active(self):
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=dates_helper.local_today(),
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': True,
            'max_allowed_end_date': dates_helper.local_today(),
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[self.campaign.id])

    def test_max_end_date_set(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            max_allowed_end_date=today,
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': False,
            'max_allowed_end_date': today,
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[self.campaign.id])

    def test_state_active_max_end_date_past(self):
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=dates_helper.local_yesterday(),
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': False,  # inactive because end date past
            'max_allowed_end_date': dates_helper.local_yesterday(),
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[self.campaign.id])

    def test_almost_depleted(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            max_allowed_end_date=today,
            almost_depleted=True,
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': False,
            'max_allowed_end_date': today,
            'almost_depleted': True,
            'pending_budget_updates': False,
        }, states[self.campaign.id])

    def test_no_realtime_campaign_stop(self):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        magic_mixer.blend(
            CampaignStopState,
            campaign=campaign,
            state=constants.CampaignStopState.ACTIVE
        )
        states = api.get_campaignstop_states([campaign])
        self.assertEqual({
            'allowed_to_run': True,
            'max_allowed_end_date': None,
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[campaign.id])

    def test_pending_budget_updates(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            max_allowed_end_date=today,
            pending_budget_updates=True,
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': False,
            'max_allowed_end_date': today,
            'almost_depleted': False,
            'pending_budget_updates': True,
        }, states[self.campaign.id])

    def test_pending_budget_updates_and_active(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=today,
            pending_budget_updates=True,
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual({
            'allowed_to_run': True,
            'max_allowed_end_date': today,
            'almost_depleted': False,
            'pending_budget_updates': False,
        }, states[self.campaign.id])
