import datetime

from django.test import TestCase, mock
from django.http.request import HttpRequest

import zemauth.models

import reports.models
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
            20,
            round(dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle))
        )

        end = (start_date + datetime.timedelta(days=29))
        self.assertEqual(
            30,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end)
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
            45,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_of_budget_1)
        )

        self.assertEqual(
            60,
            dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date)
        )

    def test_get_total_and_media_campaign_spend(self):
        # very simple test since target func just retrieves data from Redshift
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)

        credit = dash.models.CreditLineItem.objects.create(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=500,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )
        budget = dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=500,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=start_date,
            media_spend_nano=499 * 10**9,
            data_spend_nano=0,
            license_fee_nano=0
        )

        self.assertEqual(
            (499, 499),
            dash.infobox_helpers.get_total_and_media_campaign_spend(user, campaign)
        )

    def test_get_yesterday_total_spend(self):
        # very simple test since target func just retrieves data from Redshift
        campaign = dash.models.Campaign.objects.get(pk=1)
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

        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=datetime.datetime.today() - datetime.timedelta(days=1),
            media_spend_nano=50 * 10**9,
            data_spend_nano=0,
            license_fee_nano=0
        )

        self.assertEqual(
            50,
            dash.infobox_helpers.get_yesterday_campaign_spend(user, campaign)
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

    def test_calculate_daily_cap(self):
        dash.models.AdGroupSourceState.objects.create(
            ad_group_source=dash.models.AdGroupSource.objects.filter(
                ad_group__id=1
            ).first(),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            daily_budget_cc=50
        )

        campaign = dash.models.Campaign.objects.get(pk=1)
        self.assertEqual(50, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

        dash.models.AdGroupSourceState.objects.all().delete()
        for adgss in dash.models.AdGroupSourceState.objects.all():
            adgss.daily_budget_cc = 0
            adgss.save(None)

        self.assertEqual(0, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

    @mock.patch('reports.api_contentads.query')
    def test_goals_and_spend_settings(self, mock_query):
        mock_query.return_value = {
            'bounce_rate': 0.01,
            'new_visits': 100,
            'avg_tos': 5,
            'pv_per_visit': 10,
        }

        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)
        settings, is_delivering = dash.infobox_helpers.goals_and_spend_settings(user, campaign)

        self.assertEqual(1, len(settings))

    def test_format_goal_value(self):
        self.assertEqual(
            10,
            dash.infobox_helpers.format_goal_value(
                10.00,
                dash.constants.CampaignGoal.SECONDS_TIME_ON_SITE,
            )
        )

        self.assertEqual(
            0.15,
            dash.infobox_helpers.format_goal_value(
                0.15,
                dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,
            )
        )

    @mock.patch('reports.redshift.get_cursor')
    def test_get_yesterday_adgroup_spend(self, cursor):
        user = zemauth.models.User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        cursor().dictfetchall.return_value = [{
            'adgroup_id': u'1',
            'cost_cc_sum': 500000,
        }]

        self.assertEqual(
            50,
            dash.infobox_helpers.get_yesterday_adgroup_spend(user, ad_group)
        )

    def test_create_yesterday_spend_setting(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(50, 100)

        self.assertEqual("$50.00", setting.value)
        self.assertEqual("50.00% of daily budget", setting.description)
        self.assertEqual('sad', setting.icon)

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting(110, 100)

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of daily budget", setting_1.description)
        self.assertEqual('happy', setting_1.icon)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting(50, 0)

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)
        self.assertEqual('sad', setting_0.icon)

    def test_calculate_daily_account_cap(self):
        adgs = dash.models.AdGroupSource.objects.first()
        dash.models.AdGroupSourceState.objects.create(
            ad_group_source=adgs,
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            daily_budget_cc=50
        )

        account = dash.models.Account.objects.get(pk=1)
        cap = dash.infobox_helpers.calculate_daily_account_cap(account)
        self.assertEqual(50, cap)

    def test_calculate_available_credit(self):
        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_available_credit(account)
        self.assertEqual(0, available_credit)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        available_credit = dash.infobox_helpers.calculate_available_credit(account)
        self.assertEqual(80, available_credit)


class InfoBoxAccountHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date() - datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )


    @mock.patch('dash.models.BudgetLineItem.get_spend_data')
    def test_calculate_spend_credit(self, mock_get_spend_data):
        mock_get_spend_data.return_value = {
            'media': 0,
            'data': 0,
            'license_fee': 0,
            'total': 0
        }

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_spend_credit(account)
        self.assertEqual(0, available_credit)

        mock_get_spend_data.return_value = {
            'media': 10,
            'data': 10,
            'license_fee': 10,
            'total': 30
        }

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_spend_credit(account)
        self.assertEqual(10, available_credit)


    @mock.patch('dash.models.BudgetLineItem.get_daily_spend')
    def test_calculate_yesterday_account_spend(self, mock_get_daily_spend):

        mock_get_daily_spend.return_value = {
            'media': 0,
            'data': 0,
            'license_fee': 0,
            'total': 0
        }

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_yesterday_account_spend(account)
        self.assertEqual(0, available_credit)

        mock_get_daily_spend.return_value = {
            'media': 10,
            'data': 10,
            'license_fee': 10,
            'total': 30
        }

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_yesterday_account_spend(account)
        self.assertEqual(10, available_credit)
