from django.test import TestCase

from .. import constants, CampaignStopState
import api
import core.entity
from utils import dates_helper
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


class GetMaxEndDatesTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

    def test_default(self):
        end_dates = api.get_max_end_dates([self.campaign])
        self.assertEqual(None, end_dates[self.campaign])

    def test_max_end_date_set(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            max_allowed_end_date=today,
        )

        end_dates = api.get_max_end_dates([self.campaign])
        self.assertEqual(today, end_dates[self.campaign])

    def test_no_realtime_campaign_stop(self):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=campaign,
            max_allowed_end_date=today,
        )

        end_dates = api.get_max_end_dates([campaign])
        self.assertEqual(None, end_dates[campaign])
