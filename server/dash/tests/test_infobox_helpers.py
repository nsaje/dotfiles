import datetime

from django.test import TestCase

import zemauth.models

import dash.constants
import dash.models
import dash.infobox_helpers


class InfoBoxHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_format_flight_time(self):
        start_date = datetime.datetime(2016, 1, 1).date()
        end_date = (datetime.datetime.today() + datetime.timedelta(days=1)).date()

        formatted_flight_time, days_left = dash.infobox_helpers.format_flight_time(start_date, end_date)

        self.assertTrue(formatted_flight_time.startswith('01/01 - '))
        self.assertEqual(2, days_left)

    def test_get_ideal_campaign_spend(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=100)

        credit = dash.models.CreditLineItem.objects.create(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        budget = dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(
            0,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        middle = (start_date + (end_date - start_date) / 2)

        self.assertEqual(
            budget.amount / 2,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle)
        )

        self.assertEqual(
            budget.amount,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date)
        )

    def test_get_ideal_campaign_spend_multiple_nonoverlapping_budgets(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=100)

        credit = dash.models.CreditLineItem.objects.create(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=30,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=30),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=30,
            start_date=start_date + datetime.timedelta(days=31),
            end_date=start_date + datetime.timedelta(days=61),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date + datetime.timedelta(days=62),
            end_date=start_date + datetime.timedelta(days=100),
            created_by=user,
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(
            0,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        middle = (start_date + (end_date - start_date) / 2)

        self.assertEqual(
            50,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle)
        )

        self.assertEqual(
            100,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date)
        )

    def test_get_ideal_campaign_spend_multiple_overlapping_budgets(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=100)

        credit = dash.models.CreditLineItem.objects.create(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=120,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=80),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date + datetime.timedelta(days=20),
            end_date=start_date + datetime.timedelta(days=100),
            created_by=user,
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(
            0,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        end_of_budget_1 = start_date + datetime.timedelta(days=80)
        self.assertEqual(
            60 + 60 / 5 * 4,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_of_budget_1)
        )

        self.assertEqual(
            120,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date)
        )


    def test_get_total_campaign_spend(self):
        pass

    def test_get_yesterday_total_cost(self):
        pass

    def test_get_goal_value(self):
        pass

    def test_get_goal_difference(self):
        pass
