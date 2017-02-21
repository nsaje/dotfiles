import datetime
import calendar

from decimal import Decimal
from django.test import TestCase, mock
from django.db import connection
from django.utils import timezone

import zemauth.models

import reports.models
import dash.constants
import dash.models
import dash.infobox_helpers

from utils.test_helper import fake_request
from django.test.client import RequestFactory


class InfoBoxHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_format_flight_time(self):
        start_date = datetime.datetime(2016, 1, 1).date()
        end_date = (datetime.datetime.today() + datetime.timedelta(days=1)).date()

        formatted_flight_time, days_left = dash.infobox_helpers.format_flight_time(start_date, end_date)

        self.assertTrue(formatted_flight_time.startswith('01/01 - '))
        self.assertEqual(2, days_left)

    def test_filter_user_by_account_type(self):
        account = dash.models.Account.objects.get(pk=1)

        acs = account.get_current_settings()
        acs.account_type = dash.constants.AccountType.PILOT
        acs.save(fake_request(zemauth.models.User.objects.get(pk=1)))

        su = zemauth.models.User.objects.all().filter(is_superuser=True)
        fusers = dash.infobox_helpers._filter_user_by_account_type(
            su, [dash.constants.AccountType.PILOT])
        self.assertEqual(su.count(), fusers.count())

        fusers = dash.infobox_helpers._filter_user_by_account_type(
            account.users.all(), [dash.constants.AccountType.PILOT])
        self.assertEqual(account.users.all().count(), fusers.count())

        rest = zemauth.models.User.objects.all().exclude(
            id__in=su.values_list('id', flat=True)
        ).exclude(
            id__in=account.users.all().values_list('id', flat=True)
        )
        rusers = dash.infobox_helpers._filter_user_by_account_type(
            rest, [dash.constants.AccountType.PILOT])
        self.assertEqual(0, rusers.count())

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
            license_fee_nano=0,
            margin_nano=0,
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
            license_fee_nano=0,
            margin_nano=0,
        )

        self.assertEqual(
            50,
            dash.infobox_helpers.get_yesterday_campaign_spend(user, campaign)
        )

    def test_calculate_daily_cap(self):
        ad_group_sources = dash.models.AdGroupSource.objects.filter(
            ad_group__id=1
        )

        dash.models.AdGroupSourceState.objects.create(
            ad_group_source=ad_group_sources[0],
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            daily_budget_cc=100
        )
        new_settings = ad_group_sources[0].get_current_settings().copy_settings()
        new_settings.daily_budget_cc = 200
        new_settings.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
        new_settings.save(None)

        new_settings = ad_group_sources[0].ad_group.get_current_settings().copy_settings()
        new_settings.state = dash.constants.AdGroupSettingsState.ACTIVE
        new_settings.save(None)

        # Test also for ad group sources with daily_budget_cc not set in AdGroupSourceSettings.
        dash.models.AdGroupSourceState.objects.create(
            ad_group_source=ad_group_sources[1],
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            daily_budget_cc=300
        )
        new_settings = ad_group_sources[1].get_current_settings().copy_settings()
        new_settings.daily_budget_cc = None
        new_settings.save(None)

        campaign = dash.models.Campaign.objects.get(pk=1)
        self.assertEqual(550, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

        # use raw sql to bypass model restrictions
        q = 'DELETE FROM dash_adgroupsourcestate; DELETE FROM dash_adgroupsourcesettings; '\
            'DELETE FROM dash_adgroupsettings'
        cursor = connection.cursor()
        cursor.execute(q, [])

        self.assertEqual(0, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

    @mock.patch('reports.redshift.get_cursor')
    def test_get_yesterday_adgroup_spend(self, cursor):
        user = zemauth.models.User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        cursor().dictfetchall.return_value = [{
            'adgroup_id': u'1',
            'media_cost_cc_sum': 500000,
        }]

        self.assertEqual(
            50,
            dash.infobox_helpers.get_yesterday_adgroup_spend(user, ad_group)
        )

    def test_create_yesterday_spend_setting(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(50, 100)

        self.assertEqual("$50.00", setting.value)
        self.assertEqual("50.00% of $100.00 Daily Spend Cap", setting.description)

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting(110, 100)

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of $100.00 Daily Spend Cap", setting_1.description)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting(50, 0)

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)


class InfoBoxAccountHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        self.user = user
        self.agency = dash.models.Agency(name='test')
        self.agency.save(fake_request(user))

        today = datetime.datetime.today().date()

        _, days_of_month = calendar.monthrange(today.year, today.month)

        start_date = today - datetime.timedelta(days=days_of_month - 1)
        end_date = today + datetime.timedelta(days=days_of_month - 1)

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
        self.assertEqual(0, dash.infobox_helpers.get_yesterday_all_accounts_spend(None, None))
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=yesterday,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
            margin_nano=0,
        )
        self.assertEqual(10, dash.infobox_helpers.get_yesterday_all_accounts_spend(None, None))

        account = dash.models.Account.objects.get(pk=1)
        account.agency = self.agency
        account.save(fake_request(self.user))

        self.assertEqual(10, dash.infobox_helpers.get_yesterday_all_accounts_spend([self.agency], None))

        res = dash.infobox_helpers.get_yesterday_all_accounts_spend([], [dash.constants.AccountType.UNKNOWN])
        self.assertEqual(0, res)

        new_acs = account.get_current_settings().copy_settings()
        new_acs.account_type = dash.constants.AccountType.UNKNOWN
        new_acs.save(fake_request(self.user))

        res = dash.infobox_helpers.get_yesterday_all_accounts_spend([], [dash.constants.AccountType.UNKNOWN])
        self.assertEqual(10, res)

    def test_get_mtd_agency_spend(self):
        self.assertEqual(0, dash.infobox_helpers.get_mtd_agency_spend(self.user))

        today = datetime.datetime.utcnow()
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
            margin_nano=0,
        )
        self.assertEqual(Decimal('10.0000'), dash.infobox_helpers.get_mtd_agency_spend(self.user))

    def test_yesterday_agency_spend(self):
        self.assertEqual(0, dash.infobox_helpers.get_yesterday_agency_spend(self.user))

        today = datetime.datetime.utcnow()
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
            margin_nano=0,
        )
        self.assertEqual(Decimal('10.0000'), dash.infobox_helpers.get_yesterday_agency_spend(
            self.user)
        )

    def test_get_mtd_all_accounts_spend(self):
        self.assertEqual(0, dash.infobox_helpers.get_mtd_all_accounts_spend(None, None))

        today = datetime.datetime.utcnow()
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
            margin_nano=0,
        )
        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend(None, None))

        aproximately_one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=aproximately_one_month_ago,
            media_spend_nano=10e9,
            data_spend_nano=10e9,
            license_fee_nano=10e9,
            margin_nano=0,
        )
        # shouldn't change because it's month to date
        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend(None, None))

        self.assertEqual(0, dash.infobox_helpers.get_mtd_all_accounts_spend(
            [self.agency], None))

        account = dash.models.Account.objects.get(pk=1)
        account.agency = self.agency
        account.save(fake_request(self.user))

        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend(
            [self.agency], None))

        self.assertEqual(0, dash.infobox_helpers.get_mtd_all_accounts_spend(
            [], [dash.constants.AccountType.PILOT]))

        new_acs = account.get_current_settings().copy_settings()
        new_acs.account_type = dash.constants.AccountType.PILOT
        new_acs.save(fake_request(self.user))

        self.assertEqual(10, dash.infobox_helpers.get_mtd_all_accounts_spend(
            [], [dash.constants.AccountType.PILOT]))

    def test_count_active_accounts(self):
        today = datetime.datetime.utcnow()

        for adgss in dash.models.AdGroupSourceState.objects.all():
            adgss.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
            adgss.save()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

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

        self.assertEqual(1, dash.infobox_helpers.count_active_accounts(None, None))

    def test_count_active_agency_accounts(self):
        today = datetime.datetime.utcnow()

        for adgss in dash.models.AdGroupSourceState.objects.all():
            adgss.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
            adgss.save()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

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

        user1 = self._make_a_john()
        self.assertEqual(0, dash.infobox_helpers.count_active_agency_accounts(user1))

        account = dash.models.Account.objects.get(pk=1)
        account.users.add(user1)
        self.assertEqual(1, dash.infobox_helpers.count_active_agency_accounts(user1))

        r = RequestFactory().get('')
        r.user = user1
        user2 = self._make_a_john('john2@example.com')

        agency = dash.models.Agency(name='Test Agency')
        agency.save(r)
        account.agency = agency
        account.save(r)
        self.assertEqual(0, dash.infobox_helpers.count_active_agency_accounts(user2))
        agency.users.add(user2)
        self.assertEqual(1, dash.infobox_helpers.count_active_agency_accounts(user2))

    def _make_a_john(self, email=None):
        ordinary_john = zemauth.models.User.objects.create_user(
            username=email or "Janez",
            email=email or "janez.janez@arnes.si",
            password="janez"
        )
        ordinary_john.last_login = datetime.datetime.utcnow()
        ordinary_john.save()
        return ordinary_john

    def test_get_weekly_logged_in_users(self):
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

        for u in zemauth.models.User.objects.all():
            if 'zemanta' not in u.email:
                continue
            u.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            u.save()

        # zemanta mail should be skipped when counting mails
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

        john = self._make_a_john()
        john.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        john.save()
        self.assertEqual(1, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

    @mock.patch('django.utils.timezone.now')
    def test_count_weekly_active_users(self, mock_now):
        # should be 0 by default
        self.assertEqual(0, len(dash.infobox_helpers.get_weekly_active_users(None, None)))
        self.assertEqual(0, dash.infobox_helpers.count_weekly_selfmanaged_actions(None, None))

        for u in zemauth.models.User.objects.all():
            if 'zemanta' not in u.email:
                continue

            mock_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
            dash.models.History.objects.create(
                action_type=dash.constants.HistoryActionType.CONTENT_AD_CREATE,
                level=dash.constants.HistoryLevel.AD_GROUP,
                ad_group=dash.models.AdGroup.objects.get(pk=1),
                created_by=u,
            )

        # zemanta mail should be skipped when counting mails
        self.assertEqual(0, len(dash.infobox_helpers.get_weekly_active_users(None, None)))
        self.assertEqual(0, dash.infobox_helpers.count_weekly_selfmanaged_actions(None, None))

        mock_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        john = self._make_a_john()
        ual = dash.models.History.objects.create(
            action_type=dash.constants.HistoryActionType.CONTENT_AD_CREATE,
            level=dash.constants.HistoryLevel.AD_GROUP,
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            created_by=john,
        )
        self.assertEqual(1, len(dash.infobox_helpers.get_weekly_active_users(None, None)))
        self.assertEqual(1, dash.infobox_helpers.count_weekly_selfmanaged_actions(None, None))

        mock_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        ual = dash.models.History.objects.create(
            action_type=dash.constants.HistoryActionType.SETTINGS_CHANGE,
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            level=dash.constants.HistoryLevel.AD_GROUP,
            created_by=john
        )

        self.assertEqual(1, len(dash.infobox_helpers.get_weekly_active_users(None, None)))
        self.assertEqual(2, dash.infobox_helpers.count_weekly_selfmanaged_actions(None, None))

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
            margin_nano=0,
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

        superuser = zemauth.models.User.objects.get(id=1)
        normal_user = zemauth.models.User.objects.get(id=2)

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_adgroup_running_status(superuser, ad_group_settings)
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
            dash.infobox_helpers.get_adgroup_running_status(superuser, ad_group_settings)
        )

        # adgroup is in landing mode and active, sources are active
        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.landing_mode = True
        new_ad_group_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.LANDING_MODE,
            dash.infobox_helpers.get_adgroup_running_status(superuser, new_ad_group_settings)
        )

        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.landing_mode = False
        new_ad_group_settings.save(None)

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
            dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY,
            dash.infobox_helpers.get_adgroup_running_status(superuser, ad_group_settings)
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group_settings)
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
            dash.infobox_helpers.get_adgroup_running_status(superuser, ad_group_settings)
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group_settings)
        )

        ad_group_settings = ad_group.get_current_settings()
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(superuser, ad_group_settings)
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
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group_settings)
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
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group_settings)
        )

    def test_get_campaign_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE,
            dash.infobox_helpers.get_campaign_running_status(campaign, campaign.get_current_settings())
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
            dash.infobox_helpers.get_campaign_running_status(campaign, campaign.get_current_settings())
        )

        for adg in campaign.adgroup_set.all():
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_campaign_running_status(campaign, campaign.get_current_settings())
        )

        # campaign is in landing mode
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.LANDING_MODE,
            dash.infobox_helpers.get_campaign_running_status(campaign, campaign.get_current_settings())
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

        for adg in dash.models.AdGroup.objects.filter(campaign__account=campaign.account):
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_campaign_running_status(campaign, campaign.get_current_settings())
        )


class AllAccountsInfoboxHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_calculate_daily_account_cap(self):
        account = dash.models.Account.objects.get(pk=1)
        cap = dash.infobox_helpers.calculate_daily_account_cap(account)
        self.assertEqual(100, cap)

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

    def test_calculate_allocated_and_available_agency_credit(self):
        user = zemauth.models.User.objects.get(pk=1)
        r = RequestFactory().get('')
        r.user = user

        agency = dash.models.Agency(
            name='SOVA'
        )
        agency.save(r)

        account = dash.models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(r)

        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create(
            agency=agency,
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
            license_fee_nano=0,
            margin_nano=0,
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(10, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(80, budget_available)

    def test_calculate_spend_and_available_agency_budget(self):
        user = zemauth.models.User.objects.get(pk=1)
        r = RequestFactory().get('')
        r.user = user

        agency = dash.models.Agency(
            name='SOVA'
        )
        agency.save(r)

        account = dash.models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(r)

        campaign = dash.models.Campaign.objects.get(pk=1)
        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(0, account_spend)
        self.assertEqual(0, budget_available)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create(
            agency=agency,
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
            license_fee_nano=0,
            margin_nano=0,
        )

        account_spend, budget_available = dash.infobox_helpers.calculate_spend_and_available_budget(account)
        self.assertEqual(10, account_spend)
        # as long as there are no budgets available there-s nothing to spend
        self.assertEqual(80, budget_available)
