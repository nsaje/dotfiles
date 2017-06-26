from decimal import Decimal
import datetime

from django.test import TestCase

from utils.magic_mixer import magic_mixer
import dash.models
import dash.constants

import service


class TestService(TestCase):

    def test_launch(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account)
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500
        )
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)

        campaign = service.launch(
            request=request,
            account=account,
            name='xyz',
            iab_category=dash.constants.IABCategory.IAB1_1,
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 1, 2),
            budget_amount=123,
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            goal_value=Decimal(30.0),
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            conversion_goal_goal_id=str(pixel.id),
            conversion_goal_window=dash.constants.ConversionWindows.LEQ_1_DAY
        )

        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign_settings.name, 'xyz')
        self.assertEqual(campaign_settings.iab_category, dash.constants.IABCategory.IAB1_1)

        budget = campaign.budgets.first()
        self.assertEqual(budget, credit.budgets.first())
        self.assertEqual(budget.start_date, datetime.date(2017, 1, 1))
        self.assertEqual(budget.end_date, datetime.date(2017, 1, 2))

        goal = campaign.campaigngoal_set.first()
        self.assertEqual(goal.type, dash.constants.CampaignGoalKPI.CPA)
        self.assertEqual(goal.conversion_goal.type, dash.constants.ConversionGoalType.PIXEL)
