import datetime
import decimal
import mock

from django.test import TestCase

import core.bcm
import core.entity
import core.source
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import CampaignStopState, RealTimeCampaignDataHistory, constants
import update_campaignstop_state


class UpdateCampaignStopStateTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

        today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(today, 7),
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            license_fee=decimal.Decimal('0.1'),
        )
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(today, 7),
            end_date=today,
            credit=self.credit,
            amount=500,
        )

    def test_create_campaign_state(self):
        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).exists())

        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.ACTIVE, campaign_stop_state.state)

    def test_stop_campaign_without_budget(self):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)
        update_campaignstop_state.update_campaigns_state(
            campaigns=[campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    def test_stop_campaign_with_realtime_spend(self):
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('500.0'),
        )
        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    @mock.patch.object(core.bcm.BudgetLineItem, 'get_available_etfm_amount')
    def test_stop_campaign_with_high_yday_spend(self, mock_available_amount):
        mock_available_amount.return_value = 0
        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    @mock.patch.object(core.bcm.BudgetLineItem, 'get_available_etfm_amount')
    def test_stop_campaign_rt_and_budget_spend(self, mock_available_amount):
        mock_available_amount.return_value = 200
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('200.0'),
        )
        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    def test_stop_campaign_high_spend_rate(self):
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('100.0'),
        )
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('400.0'),
        )
        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    def test_stop_campaign_with_yesterday_realtime_data(self):
        today = dates_helper.local_today()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(
                update_campaignstop_state.HOURS_DELAY - 1)
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_yesterday(),
                etfm_spend=decimal.Decimal('400.0'),
            )
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_today(),
                etfm_spend=decimal.Decimal('100.0'),
            )
            update_campaignstop_state.update_campaigns_state(
                campaigns=[self.campaign])

            campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
            self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    def test_stop_campaign_with_yesterday_realtime_data_and_spend_rate(self):
        today = dates_helper.local_today()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(
                update_campaignstop_state.HOURS_DELAY - 1)
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_yesterday(),
                etfm_spend=decimal.Decimal('200.0'),
            )
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_yesterday(),
                etfm_spend=decimal.Decimal('200.0'),
            )
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_today(),
                etfm_spend=decimal.Decimal('0.0'),
            )
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_today(),
                etfm_spend=decimal.Decimal('150.0'),
            )
            update_campaignstop_state.update_campaigns_state(
                campaigns=[self.campaign])

            campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
            self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)
