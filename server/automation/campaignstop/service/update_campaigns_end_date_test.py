import datetime
from django.test import TestCase
from mock import patch

from .. import CampaignStopState
from .update_campaigns_end_date import update_campaigns_end_date

import core.bcm
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper


class UpdateCampaignEndDateTestCase(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

        self.today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 30),
            end_date=dates_helper.days_after(self.today, 30),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            license_fee='0.1',
        )
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            credit=self.credit,
            amount=500,
        )

    def test_current_budget(self):
        self.assertFalse(CampaignStopState.objects.exists())
        update_campaigns_end_date([self.campaign])

        self.assertEqual(1, CampaignStopState.objects.count())
        campaign_stop_state = CampaignStopState.objects.get()

        self.assertEqual(campaign_stop_state.campaign, self.campaign)
        self.assertEqual(campaign_stop_state.max_allowed_end_date, self.budget.end_date)

    @patch('utils.dates_helper.utc_now')
    def test_past_budget(self, mock_utc_now):
        mock_utc_now.return_value = dates_helper.days_after(datetime.datetime.utcnow(), 100)
        update_campaigns_end_date([self.campaign])

        self.assertEqual(1, CampaignStopState.objects.count())
        campaign_stop_state = CampaignStopState.objects.get()

        self.assertEqual(campaign_stop_state.campaign, self.campaign)
        self.assertEqual(campaign_stop_state.max_allowed_end_date, self.budget.end_date)

    def test_future_budget(self):
        magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_after(self.today, 7),
            end_date=dates_helper.days_after(self.today, 7),
            credit=self.credit,
            amount=500,
        )
        update_campaigns_end_date([self.campaign])

        self.assertEqual(1, CampaignStopState.objects.count())
        campaign_stop_state = CampaignStopState.objects.get()

        self.assertEqual(campaign_stop_state.campaign, self.campaign)
        self.assertEqual(campaign_stop_state.max_allowed_end_date, self.budget.end_date)

    def test_no_current_budget(self):
        with patch('django.utils.timezone.now') as mock_now:
            yday = dates_helper.day_before(self.today)
            mock_now.return_value = datetime.datetime(yday.year, yday.month, yday.day, 12)

            campaign = magic_mixer.blend(
                core.entity.Campaign,
                account=self.campaign.account,  # uses the same credit
                real_time_campaign_stop=True
            )
            magic_mixer.blend(
                core.bcm.BudgetLineItem,
                campaign=campaign,
                start_date=dates_helper.days_after(self.today, 7),
                end_date=dates_helper.days_after(self.today, 7),
                credit=self.credit,
                amount=500,
            )

        update_campaigns_end_date([campaign])

        self.assertEqual(1, CampaignStopState.objects.count())
        campaign_stop_state = CampaignStopState.objects.get()

        self.assertEqual(campaign_stop_state.campaign, campaign)
        self.assertEqual(
            campaign_stop_state.max_allowed_end_date,
            dates_helper.day_before(campaign.created_dt.date())
        )
