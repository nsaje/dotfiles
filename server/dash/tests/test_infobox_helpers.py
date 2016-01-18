import datetime

from django.test import TestCase

import zemauth.models

import dash.constants
import dash.models
import dash.infobox_helpers


class InfoBoxHelpersTest(TestCase):
    fixtures = ['test_io.yaml']

    def test_format_flight_time(self):
        start_date = datetime.datetime(2016, 1, 1).date()
        end_date = (datetime.datetime.today() + datetime.timedelta(days=1)).date()

        formatted_flight_time, days_left = dash.infobox_helpers.format_flight_time(start_date, end_date)

        self.assertTrue(formatted_flight_time.startswith('01/01 - '))
        self.assertEqual(2, days_left)

    def test_get_ideal_campaign_spend(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=100)

        credit = dash.models.CreditLineItem.objects.create(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=zemauth.models.User.objects.get(pk=3)
        )

        budget = dash.models.BudgetLineItem.objects.create(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=zemauth.models.User.objects.get(pk=3)
        )

    def test_get_total_campaign_spend(self):
        pass

    def test_get_yesterday_total_cost(self):
        pass

    def test_get_goal_value(self):
        pass

    def test_get_goal_difference(self):
        pass
