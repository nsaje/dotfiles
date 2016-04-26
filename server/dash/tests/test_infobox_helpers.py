import datetime
import calendar

from decimal import Decimal
from django.test import TestCase, mock
from django.db import connection

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

        # use raw sql to bypass model restrictions
        q = 'DELETE FROM dash_adgroupsourcestate'
        cursor = connection.cursor()
        cursor.execute(q, [])

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

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting(110, 100)

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of daily budget", setting_1.description)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting(50, 0)

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)


class InfoBoxAccountHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        today = datetime.datetime.today().date()

        _, days_of_month = calendar.monthrange(today.year, today.month)

        start_date = today - datetime.timedelta(days=days_of_month-1)
        end_date = today + datetime.timedelta(days=days_of_month-1)

        self.credit = dash.models.CreditLineItem.objects.create(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=300,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        self.budget = dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=self.credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

    def test_get_yesterday_all_accounts_spend(self):
        self.assertEqual(0, dash.infobox_helpers.get_yesterday_all_accounts_spend())
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=yesterday,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
        )
        self.assertEqual(10, dash.infobox_helpers.get_yesterday_all_accounts_spend())

    def test_get_mtd_all_accounts_spend(self):
        self.assertEqual(0, dash.infobox_helpers.get_mtd_all_accounts_spend())

        today = datetime.datetime.utcnow()
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
        )
        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend())

        aproximately_one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=aproximately_one_month_ago,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
        )
        # shouldn't change because it's month to date
        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend())

    def test_count_active_accounts(self):
        today = datetime.datetime.utcnow()

        for adgss in dash.models.AdGroupSourceState.objects.all():
            adgss.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
            adgss.save()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts())

        all_adgset = dash.models.AdGroupSettings.objects.filter(
            ad_group__campaign__account__id=1
        )
        for adgset in all_adgset:
            new_adgset = adgset.copy_settings()
            new_adgset.start_date = today
            new_adgset.end_date = today + datetime.timedelta(days=1)
            new_adgset.save(None)

        all_adgs_1 = dash.models.AdGroupSource.objects.filter(
            ad_group__campaign__account__id=1
        )
        for adgs in all_adgs_1:
            dash.models.AdGroupSourceState.objects.create(
                ad_group_source=adgs,
                state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
                cpc_cc=10,
                daily_budget_cc=10
            )

        self.assertEqual(1, dash.infobox_helpers.count_active_accounts())

    def test_calculate_all_accounts_total_budget(self):
        today = datetime.datetime.utcnow().date()
        day_budget_span = (self.budget.end_date - self.budget.start_date).days

        self.assertEqual(
            100 * (Decimal(1) / day_budget_span),
            dash.infobox_helpers.calculate_all_accounts_total_budget(
                today,
                today + datetime.timedelta(days=1)
            )
        )
        self.assertEqual(0, dash.infobox_helpers.calculate_all_accounts_total_budget(
            today + datetime.timedelta(days=100), today + datetime.timedelta(days=100)
        ))
        # make a past budget and check if total holds
        user = zemauth.models.User.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        _, days_of_month = calendar.monthrange(today.year, today.month)
        today = datetime.datetime.today().date()
        start_date_1 = today - datetime.timedelta(days=days_of_month-1)
        end_date_1 = today + datetime.timedelta(days=(days_of_month-1)/2)
        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=self.credit,
            amount=100,
            start_date=start_date_1,
            end_date=end_date_1,
            created_by=user,
        )

        total_duration = days_of_month-1 + (days_of_month-1)/2

        self.assertEqual(
            (Decimal(50) + Decimal((days_of_month-1) / float(total_duration) * 100)).quantize(Decimal('.01')),
            dash.infobox_helpers.calculate_all_accounts_total_budget(
                today - datetime.timedelta(days=60),
                today
            ).quantize(Decimal('.01'))
        )

        # test with date after end of budget
        self.assertEqual(
            0,
            dash.infobox_helpers.calculate_all_accounts_total_budget(
                today + datetime.timedelta(days=365),
                today + datetime.timedelta(days=364)
            )
        )

        # test with date before start of budget
        self.assertEqual(
            0,
            dash.infobox_helpers.calculate_all_accounts_total_budget(
                today - datetime.timedelta(days=365),
                today - datetime.timedelta(days=364)
            )
        )

    def test_calculate_all_accounts_monthly_budget(self):
        today = datetime.datetime.utcnow()
        self.assertEqual(
            Decimal(50.0),
            dash.infobox_helpers.calculate_all_accounts_monthly_budget(today).quantize(Decimal('.01'))
        )

        user = zemauth.models.User.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        today = datetime.date.today()
        first_of = datetime.date(today.year, today.month, 1)

        start_date_1 = first_of
        end_date_1 = today
        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=self.credit,
            amount=50,
            start_date=start_date_1,
            end_date=end_date_1,
            created_by=user,
        )

        self.assertEqual(
            Decimal(100.0),
            dash.infobox_helpers.calculate_all_accounts_monthly_budget(today)
        )

    def _make_a_john(self):
        ordinary_john = zemauth.models.User.objects.create_user(
            username="Janez",
            email="janez.janez@arnes.si",
            password="janez"
        )
        ordinary_john.last_login = datetime.datetime.utcnow()
        ordinary_john.save()
        return ordinary_john

    def test_get_weekly_logged_in_users(self):
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users())

        for u in zemauth.models.User.objects.all():
            if 'zemanta' not in u.email:
                continue
            u.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            u.save()

        # zemanta mail should be skipped when counting mails
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users())

        john = self._make_a_john()
        john.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        john.save()
        self.assertEqual(1, dash.infobox_helpers.count_weekly_logged_in_users())

    def test_count_weekly_active_users(self):
        # should be 0 by default
        self.assertEqual(0, len(dash.infobox_helpers.get_weekly_active_users()))
        self.assertEqual(0, dash.infobox_helpers.count_weekly_selfmanaged_actions())

        for u in zemauth.models.User.objects.all():
            if 'zemanta' not in u.email:
                continue

            dash.models.UserActionLog.objects.create(
                action_type=dash.constants.UserActionType.UPLOAD_CONTENT_ADS,
                ad_group=dash.models.AdGroup.objects.get(pk=1),
                created_dt=datetime.datetime.utcnow() - datetime.timedelta(hours=24),
                created_by=u,
            )

        # zemanta mail should be skipped when counting mails
        self.assertEqual(0, len(dash.infobox_helpers.get_weekly_active_users()))
        self.assertEqual(0, dash.infobox_helpers.count_weekly_selfmanaged_actions())

        john = self._make_a_john()
        ual = dash.models.UserActionLog.objects.create(
            action_type=dash.constants.UserActionType.UPLOAD_CONTENT_ADS,
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            created_by=john,
        )
        ual.created_dt = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        ual.save()

        self.assertEqual(1, len(dash.infobox_helpers.get_weekly_active_users()))
        self.assertEqual(1, dash.infobox_helpers.count_weekly_selfmanaged_actions())

        ual = dash.models.UserActionLog.objects.create(
            action_type=dash.constants.UserActionType.SET_CAMPAIGN_SETTINGS,
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            created_dt=datetime.datetime.utcnow(),
            created_by=john
        )
        ual.created_dt = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        ual.save()

        self.assertEqual(1, len(dash.infobox_helpers.get_weekly_active_users()))
        self.assertEqual(2, dash.infobox_helpers.count_weekly_selfmanaged_actions())

    def test_calculate_yesterday_account_spend(self):
        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_yesterday_account_spend(account)
        self.assertEqual(0, available_credit)

        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            media_spend_nano=10 * 10**9,
            data_spend_nano=10 * 10**9,
            license_fee_nano=10 * 10**9,
        )

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.calculate_yesterday_account_spend(account)
        self.assertEqual(10, available_credit)

    def test_get_adgroup_running_status(self):
        # adgroup is inactive and no active sources
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.INACTIVE,
            created_dt=datetime.datetime.utcnow()
        )
        adgs.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        # adgroup is active and sources are active
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow()
        )
        adgs.save(None)

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        # adgroup is active, sources are active and campaign is in landing mode
        new_campaign_settings = ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.LANDING_MODE,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        new_campaign_settings = ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = False
        new_campaign_settings.save(None)

        # adgroup is active, sources are active and adgroup is on CPC autopilot
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        )
        adgs.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        # adgroup is active, sources are active and adgroup is on CPC+Budget autopilot
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )
        adgs.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        # adgroup is active but sources are inactive
        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()
        for agss in source_settings:
            agss.pk = None
            agss.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
            agss.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

        # adgroup is inactive but sources are active
        new_adgs = adgs.copy_settings()
        new_adgs.state = dash.constants.AdGroupSettingsState.INACTIVE
        new_adgs.save(None)

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_adgroup_running_status(ad_group_settings)
        )

    def test_get_campaign_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )
        adgs.save(None)

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        # campaign is in landing mode
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.LANDING_MODE,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        for adg in campaign.adgroup_set.all():
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )


    def test_get_account_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE,
            dash.infobox_helpers.get_account_running_status(campaign.account)
        )

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        adgs = dash.models.AdGroupSettings(
            ad_group=ad_group,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )
        adgs.save(None)

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE,
            dash.infobox_helpers.get_account_running_status(campaign.account)
        )

        for adg in dash.models.AdGroup.objects.filter(campaign__account=campaign.account) :
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )

class AllAccountsInfoboxHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

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

    def test_calculate_allocated_and_available_credit(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

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

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(40, allocated_credit)
        self.assertEqual(60, available_credit)

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, allocated_credit)
        self.assertEqual(00, available_credit)

    def test_calculate_allocated_and_available_credit_with_freed_budget(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

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

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
            freed_cc=10 * 1e4
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(30, allocated_credit)
        self.assertEqual(70, available_credit)

    def test_calculate_spend_and_available_budget(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(0, account_spend)
        self.assertEqual(0, budget_available)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create(
            account=account,
            start_date=start_date,
            end_date=end_date,
            license_fee=Decimal('0.1'),
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(0, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(0, budget_available)

        budget = dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(0, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(36, budget_available)

        dash.models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(0, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(90, budget_available)

        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=start_date,
            media_spend_nano=10 * 10**9,
            data_spend_nano=0,
            license_fee_nano=0
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(10, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(80, budget_available)
