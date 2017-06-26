import datetime

from django.test import TestCase

from utils.magic_mixer import magic_mixer
import dash.models
import dash.constants

import service


class TestService(TestCase):

    def test_launch(self):
        account = magic_mixer.blend(dash.models.Account)
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500
        )
        campaign = service.launch(
            user=None,
            account=account,
            name='xyz',
            iab_category=dash.constants.IABCategory.IAB1_1,
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 1, 2),
            budget_amount=123
        )
        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign_settings.name, 'xyz')
        self.assertEqual(campaign_settings.iab_category, dash.constants.IABCategory.IAB1_1)
        budget = campaign.budgets.first()
        self.assertEqual(budget, credit.budgets.first())
        self.assertEqual(budget.start_date, datetime.date(2017, 1, 1))
        self.assertEqual(budget.end_date, datetime.date(2017, 1, 2))
