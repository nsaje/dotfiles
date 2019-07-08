from django.test import TestCase

import core.models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import CampaignStopState
from .. import constants
from . import api


class GetCampaignStopStatesTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)

    def test_default(self):
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,
                "max_allowed_end_date": dates_helper.local_yesterday(),
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_states_active(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=today,
            min_allowed_start_date=today,
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": True,
                "max_allowed_end_date": dates_helper.local_today(),
                "min_allowed_start_date": today,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_min_start_date_future(self):
        tomorrow = dates_helper.day_after(dates_helper.local_today())
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=dates_helper.days_after(dates_helper.local_today(), 7),
            min_allowed_start_date=tomorrow,
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": True,
                "max_allowed_end_date": dates_helper.days_after(dates_helper.local_today(), 7),
                "min_allowed_start_date": tomorrow,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_min_start_date_none(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=today,
            min_allowed_start_date=None,
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,
                "max_allowed_end_date": dates_helper.local_today(),
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_max_end_date_set(self):
        today = dates_helper.local_today()
        magic_mixer.blend(CampaignStopState, campaign=self.campaign, max_allowed_end_date=today)

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,
                "max_allowed_end_date": today,
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_state_active_max_end_date_past(self):
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=dates_helper.local_yesterday(),
        )
        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,  # inactive because end date past
                "max_allowed_end_date": dates_helper.local_yesterday(),
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_almost_depleted(self):
        today = dates_helper.local_today()
        magic_mixer.blend(CampaignStopState, campaign=self.campaign, max_allowed_end_date=today, almost_depleted=True)

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,
                "max_allowed_end_date": today,
                "min_allowed_start_date": None,
                "almost_depleted": True,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )

    def test_no_realtime_campaign_stop(self):
        campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=False)
        magic_mixer.blend(CampaignStopState, campaign=campaign, state=constants.CampaignStopState.ACTIVE)
        states = api.get_campaignstop_states([campaign])
        self.assertEqual(
            {
                "allowed_to_run": True,
                "max_allowed_end_date": None,
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[campaign.id],
        )

    def test_pending_budget_updates(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState, campaign=self.campaign, max_allowed_end_date=today, pending_budget_updates=True
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": False,
                "max_allowed_end_date": today,
                "min_allowed_start_date": None,
                "almost_depleted": False,
                "pending_budget_updates": True,
            },
            states[self.campaign.id],
        )

    def test_pending_budget_updates_and_active(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            CampaignStopState,
            campaign=self.campaign,
            state=constants.CampaignStopState.ACTIVE,
            max_allowed_end_date=today,
            min_allowed_start_date=today,
            pending_budget_updates=True,
        )

        states = api.get_campaignstop_states([self.campaign])
        self.assertEqual(
            {
                "allowed_to_run": True,
                "max_allowed_end_date": today,
                "min_allowed_start_date": today,
                "almost_depleted": False,
                "pending_budget_updates": False,
            },
            states[self.campaign.id],
        )
