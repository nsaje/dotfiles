import datetime

from django.test import TestCase, mock

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
        end_date = start_date + datetime.timedelta(days=99)

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
            1,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        middle = (start_date + datetime.timedelta(days=49))

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
            end_date=start_date + datetime.timedelta(days=29),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=30,
            start_date=start_date + datetime.timedelta(days=30),
            end_date=start_date + datetime.timedelta(days=59),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date + datetime.timedelta(days=60),
            end_date=start_date + datetime.timedelta(days=99),
            created_by=user,
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(
            1,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        middle = (start_date + datetime.timedelta(days=49))
        self.assertEqual(
            50,
            round(dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle))
        )

        middle_1_1 = (start_date + datetime.timedelta(days=29))
        self.assertEqual(
            30,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle_1_1)
        )

        middle_1_2 = (start_date + datetime.timedelta(days=30))
        self.assertEqual(
            31,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle_1_2)
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
            end_date=start_date + datetime.timedelta(days=79),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date + datetime.timedelta(days=21),
            end_date=start_date + datetime.timedelta(days=100),
            created_by=user,
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(
            0.75,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date)
        )

        end_of_budget_1 = start_date + datetime.timedelta(days=80)
        self.assertEqual(
            60 + 60 / 4 * 3,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_of_budget_1)
        )

        self.assertEqual(
            120,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date)
        )

    @mock.patch('reports.api.query')
    def test_get_total_campaign_spend(self, mock_query):
        # very simple test since target func just retrieves data from Redshift
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        mock_query.return_value = {
            'cost': 50
        }

        self.assertEqual(
            50,
            dash.infobox_helpers.get_total_campaign_spend(user, campaign)
        )

    @mock.patch('reports.api.query')
    def test_get_yesterday_total_cost(self, mock_query):
        # very simple test since target func just retrieves data from Redshift
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        mock_query.return_value = {
            'cost': 50
        }

        self.assertEqual(
            50,
            dash.infobox_helpers.get_yesterday_total_cost(user, campaign)
        )

    @mock.patch('reports.api_contentads.query')
    def test_get_goal_value(self, mock_query):
        # very simple test since target func just retrieves data from Redshift
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        mock_query.return_value = {
            'bounce_rate': 0.01,
            'new_visits': 100,
            'avg_tos': 5,
            'pv_per_visit': 10,
        }

        self.assertEqual(
            0.01,
            dash.infobox_helpers.get_goal_value(
                user,
                campaign,
                campaign.get_current_settings(),
                dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE
            )
        )

        self.assertEqual(
            (-0.01, '-1.00% below planned', True),
            dash.infobox_helpers.get_goal_difference(
                dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,
                0.01,
                0.02
            )
        )

        self.assertEqual(
            100,
            dash.infobox_helpers.get_goal_value(
                user,
                campaign,
                campaign.get_current_settings(),
                dash.constants.CampaignGoal.NEW_UNIQUE_VISITORS
            )
        )

        self.assertEqual(
            (20, '20 below planned', False),
            dash.infobox_helpers.get_goal_difference(
                dash.constants.CampaignGoal.NEW_UNIQUE_VISITORS,
                100,
                80
            )
        )

        self.assertEqual(
            5,
            dash.infobox_helpers.get_goal_value(
                user,
                campaign,
                campaign.get_current_settings(),
                dash.constants.CampaignGoal.SECONDS_TIME_ON_SITE
            )
        )

        self.assertEqual(
            (4, '4 below planned', False),
            dash.infobox_helpers.get_goal_difference(
                dash.constants.CampaignGoal.SECONDS_TIME_ON_SITE,
                5,
                1
            )
        )

        self.assertEqual(
            10,
            dash.infobox_helpers.get_goal_value(
                user,
                campaign,
                campaign.get_current_settings(),
                dash.constants.CampaignGoal.PAGES_PER_SESSION
            )
        )

        self.assertEqual(
            (-10, '10 above planned', True),
            dash.infobox_helpers.get_goal_difference(
                dash.constants.CampaignGoal.PAGES_PER_SESSION,
                10,
                20
            )
        )
