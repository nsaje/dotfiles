from django.test import TestCase

from .. import constants, CampaignStopState
import api
import core.entity
from utils.magic_mixer import magic_mixer


class GetCampaignStopStatesTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

    def test_states_default(self):
        states = api.get_campaignstop_states([self.campaign])
        self.assertFalse(states[self.campaign])

    def test_states_active(self):
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertTrue(states[self.campaign])

    def test_no_realtime_campaign_stop(self):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        magic_mixer.blend(
            CampaignStopState,
            campaign=campaign,
            state=constants.CampaignStopState.ACTIVE
        )
        states = api.get_campaignstop_states([campaign])
        self.assertTrue(states[campaign])
