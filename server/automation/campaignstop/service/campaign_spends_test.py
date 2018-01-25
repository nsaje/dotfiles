import datetime
import decimal
import mock

from django.test import TestCase

import core.bcm
import core.entity
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import RealTimeCampaignDataHistory
import update_campaignstop_state
import campaign_spends


class LogMock(object):

    def add_context(self, context):
        pass


class GetPredictionTest(TestCase):

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

    def test_get_prediction(self):
        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
        self.assertEqual(500, prediction)

    def test_get_prediction_no_budget(self):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), campaign)
        self.assertEqual(0, prediction)

    def test_get_prediction_with_realtime_spend(self):
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('300.0'),
        )

        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
        self.assertEqual(200, prediction)

    @mock.patch.object(core.bcm.BudgetLineItem, 'get_available_etfm_amount')
    def test_get_prediction_with_spent_budget(self, mock_available_amount):
        mock_available_amount.return_value = 0

        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
        self.assertEqual(0, prediction)

    @mock.patch.object(core.bcm.BudgetLineItem, 'get_available_etfm_amount')
    def test_get_prediction_with_rt_and_budget_spend(self, mock_available_amount):
        mock_available_amount.return_value = 200
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('80.0'),
        )

        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
        self.assertEqual(120, prediction)

    def test_get_prediction_with_estimation(self):
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('50.0'),
        )
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('200.0'),
        )

        prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
        self.assertEqual(150, prediction)

    def test_get_prediction_with_yesterday_realtime_data(self):
        today = dates_helper.local_today()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(
                hours=update_campaignstop_state.HOURS_DELAY-1)
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_yesterday(),
                etfm_spend=decimal.Decimal('300.0'),
            )
            magic_mixer.blend(
                RealTimeCampaignDataHistory,
                campaign=self.campaign,
                date=dates_helper.local_today(),
                etfm_spend=decimal.Decimal('50.0'),
            )

            prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
            self.assertEqual(150, prediction)

    def test_get_prediction_with_yesterday_realtime_data_and_spend_rate(self):
        today = dates_helper.local_today()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(
                hours=update_campaignstop_state.HOURS_DELAY-1)
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
                etfm_spend=decimal.Decimal('50.0'),
            )

            prediction = campaign_spends.get_predicted_remaining_budget(LogMock(), self.campaign)
            self.assertEqual(200, prediction)


class GetBudgetSpendEstimateTest(TestCase):

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

    def test_no_spend(self):
        estimate = campaign_spends.get_budget_spend_estimates(LogMock(), self.campaign)
        self.assertEqual({
            self.budget: 0
        }, estimate)

    def test_past_budget_spend(self):
        magic_mixer.blend(
            core.bcm.BudgetDailyStatement,
            budget=self.budget,
            date=dates_helper.local_yesterday(),
            media_spend_nano=150 * (10**9),
            data_spend_nano=0,
            license_fee_nano=50 * (10**9),
            margin_nano=0,
        )

        estimate = campaign_spends.get_budget_spend_estimates(LogMock(), self.campaign)
        self.assertEqual({
            self.budget: 200
        }, estimate)

    def test_real_time_data_spend(self):
        today = dates_helper.local_today()
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_yesterday(),
            etfm_spend=decimal.Decimal('50.0'),
        )
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('100.0'),
        )

        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(hours=12)

            estimate = campaign_spends.get_budget_spend_estimates(LogMock(), self.campaign)
            self.assertEqual({
                self.budget: 100
            }, estimate)

            mock_utc_now.return_value = midnight + datetime.timedelta(hours=campaign_spends.HOURS_DELAY-1)

            estimate = campaign_spends.get_budget_spend_estimates(LogMock(), self.campaign)
            self.assertEqual({
                self.budget: 150
            }, estimate)

    def test_multiple_budgets(self):
        today = dates_helper.local_today()
        new_budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(today, 7),
            end_date=today,
            credit=self.credit,
            amount=500,
        )
        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=dates_helper.local_today(),
            etfm_spend=decimal.Decimal('600.0'),
        )

        magic_mixer.blend(
            core.bcm.BudgetDailyStatement,
            budget=self.budget,
            date=dates_helper.local_yesterday(),
            media_spend_nano=150 * (10**9),
            data_spend_nano=0,
            license_fee_nano=50 * (10**9),
            margin_nano=0,
        )

        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            midnight = datetime.datetime(today.year, today.month, today.day)
            mock_utc_now.return_value = midnight + datetime.timedelta(hours=12)

            estimate = campaign_spends.get_budget_spend_estimates(LogMock(), self.campaign)
            self.assertEqual({
                self.budget: 500,
                new_budget: 300,
            }, estimate)
