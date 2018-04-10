import datetime
import decimal
import calendar

from decimal import Decimal
from django.test import TestCase, mock
from django.db import connection

import zemauth.models

import dash.constants
import dash.models
import dash.infobox_helpers

from utils import dates_helper
from utils.magic_mixer import magic_mixer
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
        account.settings.update_unsafe(None, account_type=dash.constants.AccountType.PILOT)

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

        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        budget = dash.models.BudgetLineItem.objects.create_unsafe(
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

        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=30,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=29),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=30,
            start_date=start_date + datetime.timedelta(days=30),
            end_date=start_date + datetime.timedelta(days=59),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create_unsafe(
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

        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=120,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=79),
            created_by=user,
        )

        dash.models.BudgetLineItem.objects.create_unsafe(
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

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_get_yesterday_campaign_spend(self, mock_query):
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        mock_query.return_value = [{
            'campaign_id': '1',
            'e_yesterday_cost': 50,
            'yesterday_et_cost': 60,
            'yesterday_etfm_cost': 70,
        }]

        self.assertEqual({
            'e_yesterday_cost': 50,
            'yesterday_et_cost': 60,
            'yesterday_etfm_cost': 70,
        }, dash.infobox_helpers.get_yesterday_campaign_spend(user, campaign, False))

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_get_yesterday_campaign_spend_local_currency(self, mock_query):
        campaign = dash.models.Campaign.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)

        mock_query.return_value = [{
            'campaign_id': '1',
            'local_e_yesterday_cost': 100,
            'local_yesterday_et_cost': 120,
            'local_yesterday_etfm_cost': 140,
        }]
        self.assertEqual({
            'e_yesterday_cost': 100,
            'yesterday_et_cost': 120,
            'yesterday_etfm_cost': 140,
        }, dash.infobox_helpers.get_yesterday_campaign_spend(user, campaign, True))

    def test_calculate_daily_cap(self):
        ags = dash.models.AdGroupSource.objects.get(id=2)

        ags.settings.update(
            None,
            daily_budget_cc=Decimal('200'),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE
        )

        campaign = dash.models.Campaign.objects.get(pk=1)
        self.assertEqual(600, dash.infobox_helpers.calculate_daily_campaign_cap(
            campaign, False))
        self.assertEqual(600, dash.infobox_helpers.calculate_daily_campaign_cap(
            campaign, True))

        # use raw sql to bypass model restrictions
        q = 'UPDATE dash_adgroupsettings SET state=2'
        cursor = connection.cursor()
        cursor.execute(q, [])

        self.assertEqual(0, dash.infobox_helpers.calculate_daily_campaign_cap(
            campaign, False))
        self.assertEqual(0, dash.infobox_helpers.calculate_daily_campaign_cap(
            campaign, True))

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_get_yesterday_adgroup_spend(self, mock_query):
        user = zemauth.models.User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        mock_query.return_value = [{
            'ad_group_id': '1',
            'e_yesterday_cost': 50,
            'yesterday_et_cost': 60,
            'yesterday_etfm_cost': 70,
        }]

        self.assertEqual({
            'e_yesterday_cost': 50,
            'yesterday_et_cost': 60,
            'yesterday_etfm_cost': 70,
        }, dash.infobox_helpers.get_yesterday_adgroup_spend(user, ad_group, False))

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_get_yesterday_adgroup_spend_local_currency(self, mock_query):
        user = zemauth.models.User.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        mock_query.return_value = [{
            'ad_group_id': '1',
            'local_e_yesterday_cost': 100,
            'local_yesterday_et_cost': 120,
            'local_yesterday_etfm_cost': 140,
        }]

        self.assertEqual({
            'e_yesterday_cost': 100,
            'yesterday_et_cost': 120,
            'yesterday_etfm_cost': 140,
        }, dash.infobox_helpers.get_yesterday_adgroup_spend(user, ad_group, True))

    def test_create_yesterday_spend_setting(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(
            {'e_yesterday_cost': 50}, 100, dash.constants.Currency.USD)

        self.assertEqual("$50.00", setting.value)
        self.assertEqual("50.00% of $100.00 Daily Spend Cap", setting.description)

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting(
            {'e_yesterday_cost': 110}, 100, dash.constants.Currency.USD)

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of $100.00 Daily Spend Cap", setting_1.description)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting(
            {'e_yesterday_cost': 50}, 0, dash.constants.Currency.USD)

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)

    def test_create_yesterday_spend_setting_bcm_v2(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting({
            'e_yesterday_cost': 10,
            'yesterday_etfm_cost': 50,
        }, 100, dash.constants.Currency.USD, uses_bcm_v2=True)

        self.assertEqual("$50.00", setting.value)
        self.assertEqual("50.00% of $100.00 Daily Spend Cap", setting.description)

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting({
            'e_yesterday_cost': 10,
            'yesterday_etfm_cost': 110,
        }, 100, dash.constants.Currency.USD, uses_bcm_v2=True)

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of $100.00 Daily Spend Cap", setting_1.description)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting({
            'e_yesterday_cost': 10,
            'yesterday_etfm_cost': 50,
        }, 0, dash.constants.Currency.USD, uses_bcm_v2=True)

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)

    def test_create_yesterday_spend_setting_local_currency(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(
            {'e_yesterday_cost': 50}, 100, dash.constants.Currency.EUR)

        self.assertEqual("€50.00", setting.value)
        self.assertEqual("50.00% of €100.00 Daily Spend Cap", setting.description)


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

        self.credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=300,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        self.budget = dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=self.credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        self._set_up_local_currency_bcm()

    def _set_up_local_currency_bcm(self):
        self.agency_local = magic_mixer.blend(dash.models.Agency)
        self.account_local = magic_mixer.blend(
            dash.models.Account,
            currency=dash.constants.Currency.EUR,
            agency=self.agency_local,
        )
        self.credit_local = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account_local,
            currency=self.account_local.currency,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal('1000.0'),
            flat_fee_cc=0,
            license_fee=decimal.Decimal('0.2'))

        self.campaign_local = magic_mixer.blend(
            dash.models.Campaign, account=self.account_local)
        self.budget_local = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=self.campaign_local,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=self.credit_local,
            amount=decimal.Decimal('200'),
            margin=decimal.Decimal('0'))

    def _set_up_local_currency_daily_statement(self):
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget_local,
            date=dates_helper.local_yesterday(),
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )

    def test_get_yesterday_all_accounts_spend(self):
        self.assertEqual({
            'e_yesterday_cost': 0,
            'yesterday_et_cost': 0,
            'yesterday_etfm_cost': 0,
        }, dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.all(), False))
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=yesterday,
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.all(), False))

        account = dash.models.Account.objects.get(pk=1)
        account.agency = self.agency
        account.save(fake_request(self.user))

        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.filter(agency=self.agency), False))

        res = dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.filter(settings__account_type=dash.constants.AccountType.PILOT), False)
        self.assertEqual({
            'e_yesterday_cost': 0,
            'yesterday_et_cost': 0,
            'yesterday_etfm_cost': 0,
        }, res)

        new_acs = account.get_current_settings().copy_settings()
        new_acs.account_type = dash.constants.AccountType.PILOT
        new_acs.save(fake_request(self.user))

        res = dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.filter(settings__account_type=dash.constants.AccountType.PILOT), False)
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, res)

    def test_get_yesterday_all_accounts_spend_local_currency(self):
        self._set_up_local_currency_daily_statement()
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.filter(id=self.account_local.id), False))
        self.assertEqual({
            'e_yesterday_cost': 24,
            'yesterday_et_cost': 24,
            'yesterday_etfm_cost': 36,
        }, dash.infobox_helpers.get_yesterday_all_accounts_spend(
            dash.models.Account.objects.filter(id=self.account_local.id), True))

    def test_get_mtd_agency_spend(self):
        accounts = dash.models.Account.objects.all().filter_by_user(self.user)
        self.assertEqual({
            'e_media_cost': 0,
            'et_cost': 0,
            'etfm_cost': 0,
        }, dash.infobox_helpers.get_mtd_agency_spend(
            accounts, False))

        today = datetime.datetime.utcnow()
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today,
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )
        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_agency_spend(
            accounts, False))

    def test_get_mtd_agency_spend_local_currency(self):
        self._set_up_local_currency_daily_statement()
        accounts = dash.models.Account.objects.filter(
            agency=self.agency_local,
        ).filter_by_user(self.user)
        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_agency_spend(
            accounts, False))
        self.assertEqual({
            'e_media_cost': 12,
            'et_cost': 24,
            'etfm_cost': 36,
        }, dash.infobox_helpers.get_mtd_agency_spend(
            accounts, True))

    def test_yesterday_agency_spend(self):
        accounts = dash.models.Account.objects.all().filter_by_user(self.user)
        self.assertEqual({
            'e_yesterday_cost': 0,
            'yesterday_et_cost': 0,
            'yesterday_etfm_cost': 0,
        }, dash.infobox_helpers.get_yesterday_agency_spend(
            accounts, False))

        today = datetime.datetime.utcnow()
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, dash.infobox_helpers.get_yesterday_agency_spend(
            accounts, False))

    def test_yesterday_agency_spend_local_currency(self):
        self._set_up_local_currency_daily_statement()
        accounts = dash.models.Account.objects.filter(
            agency=self.agency_local
        ).filter_by_user(self.user)
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, dash.infobox_helpers.get_yesterday_agency_spend(
            accounts, False))
        self.assertEqual({
            'e_yesterday_cost': 24,
            'yesterday_et_cost': 24,
            'yesterday_etfm_cost': 36,
        }, dash.infobox_helpers.get_yesterday_agency_spend(
            accounts, True))

    def test_get_mtd_all_accounts_spend(self):
        self.assertEqual({
            'e_media_cost': 0,
            'et_cost': 0,
            'etfm_cost': 0,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.all(), False))

        today = datetime.datetime.utcnow()
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=today,
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )
        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.all(), False))

        aproximately_one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=aproximately_one_month_ago,
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )
        # shouldn't change because it's month to date
        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(dash.models.Account.objects.all(), False))

        self.assertEqual({
            'e_media_cost': 0,
            'et_cost': 0,
            'etfm_cost': 0,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.filter(agency=self.agency), False))

        account = dash.models.Account.objects.get(pk=1)
        account.agency = self.agency
        account.save(fake_request(self.user))

        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.filter(agency=self.agency), False))

        self.assertEqual({
            'e_media_cost': 0,
            'et_cost': 0,
            'etfm_cost': 0,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.filter(settings__account_type=dash.constants.AccountType.PILOT), False))

        new_acs = account.get_current_settings().copy_settings()
        new_acs.account_type = dash.constants.AccountType.PILOT
        new_acs.save(fake_request(self.user))

        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(
            dash.models.Account.objects.filter(settings__account_type=dash.constants.AccountType.PILOT), False))

    def test_get_mtd_all_accounts_spend_local_currency(self):
        self._set_up_local_currency_daily_statement()
        accounts = dash.models.Account.objects.filter(
            agency=self.agency_local
        ).filter_by_user(self.user)
        self.assertEqual({
            'e_media_cost': 10,
            'et_cost': 20,
            'etfm_cost': 30,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(accounts, False))
        self.assertEqual({
            'e_media_cost': 12,
            'et_cost': 24,
            'etfm_cost': 36,
        }, dash.infobox_helpers.get_mtd_all_accounts_spend(accounts, True))

    def test_count_active_accounts(self):
        today = datetime.datetime.utcnow()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

        all_adgset = dash.models.AdGroupSettings.objects.filter(
            ad_group__campaign__account__id=1
        )
        for adgset in all_adgset:
            new_adgset = adgset.copy_settings()
            new_adgset.start_date = today
            new_adgset.end_date = today + datetime.timedelta(days=1)
            new_adgset.save(None)

        self.assertEqual(1, dash.infobox_helpers.count_active_accounts(None, None))

    def test_count_active_agency_accounts(self):
        today = datetime.datetime.utcnow()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

        all_adgset = dash.models.AdGroupSettings.objects.filter(
            ad_group__campaign__account__id=1
        )
        for adgset in all_adgset:
            new_adgset = adgset.copy_settings()
            new_adgset.start_date = today
            new_adgset.end_date = today + datetime.timedelta(days=1)
            new_adgset.save(None)

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

    def test_get_yesterday_account_spend(self):
        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.get_yesterday_account_spend(
            account, False)
        self.assertEqual({
            'e_yesterday_cost': 0,
            'yesterday_et_cost': 0,
            'yesterday_etfm_cost': 0,
        }, available_credit)

        dash.models.BudgetDailyStatement.objects.create(
            budget=self.budget,
            date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            media_spend_nano=decimal.Decimal('10e9'),
            data_spend_nano=decimal.Decimal('10e9'),
            license_fee_nano=decimal.Decimal('10e9'),
            margin_nano=0,
        )

        account = dash.models.Account.objects.get(pk=1)
        available_credit = dash.infobox_helpers.get_yesterday_account_spend(
            account, False)
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, available_credit)

    def test_get_yesterday_account_spend_local_currency(self):
        self._set_up_local_currency_daily_statement()
        available_credit = dash.infobox_helpers.get_yesterday_account_spend(
            self.account_local, False)
        self.assertEqual({
            'e_yesterday_cost': 20,
            'yesterday_et_cost': 20,
            'yesterday_etfm_cost': 30,
        }, available_credit)
        available_credit = dash.infobox_helpers.get_yesterday_account_spend(
            self.account_local, True)
        self.assertEqual({
            'e_yesterday_cost': 24,
            'yesterday_et_cost': 24,
            'yesterday_etfm_cost': 36,
        }, available_credit)

    def test_get_adgroup_running_status(self):
        # adgroup is inactive and no active sources
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.INACTIVE,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            created_dt=datetime.datetime.utcnow()
        )

        normal_user = zemauth.models.User.objects.get(id=2)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        # adgroup is active and sources are active
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow()
        )

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        with mock.patch('automation.campaignstop.get_campaignstop_state') as mock_get_campaignstop_state:
            old_value = ad_group.campaign.real_time_campaign_stop
            ad_group.campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': False, 'almost_depleted': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True, 'almost_depleted': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': True, 'almost_depleted': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': False, 'almost_depleted': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # adgroup is in landing mode and active, sources are active
        ad_group.settings.update_unsafe(None, landing_mode=True)
        self.assertEqual(
            dash.constants.InfoboxStatus.LANDING_MODE,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )
        ad_group.settings.update_unsafe(None, landing_mode=False)

        # campaign is on autopilot
        ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )
        ad_group.campaign.settings.update_unsafe(None, autopilot=False)

        # adgroup is active, sources are active and adgroup is on CPC autopilot
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        )

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        # adgroup is active, sources are active and adgroup is on CPC+Budget autopilot
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )

        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        with mock.patch('automation.campaignstop.get_campaignstop_state') as mock_get_campaignstop_state:
            old_value = ad_group.campaign.real_time_campaign_stop
            ad_group.campaign.set_real_time_campaign_stop(None, True)

            # adgroup is active and on CPC autopilot with pending budget updates
            start_date = datetime.datetime.today().date()
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=datetime.datetime.utcnow(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,  # price_discovery
            )
            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            # adgroup is active and on CPC+Budget autopilot with pending budget updates
            start_date = datetime.datetime.today().date()
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=datetime.datetime.utcnow(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,  # autopilot
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # adgroup is active but sources are inactive
        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()
        for agss in source_settings:
            agss.update_unsafe(
                None,
                state=dash.constants.AdGroupSourceSettingsState.INACTIVE,
            )

        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        # adgroup is inactive but sources are active
        ad_group.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSettingsState.INACTIVE,
        )

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).all()
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
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
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )

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

        campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            dash.constants.InfoboxStatus.AUTOPILOT,
            dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        campaign.settings.update_unsafe(None, autopilot=True)

        with mock.patch('automation.campaignstop.get_campaignstop_state') as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        campaign.settings.update_unsafe(None, autopilot=False)

        with mock.patch('automation.campaignstop.get_campaignstop_state') as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': False, 'pending_budget_updates': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': False, 'almost_depleted': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': False, 'almost_depleted': True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            mock_get_campaignstop_state.return_value = {'allowed_to_run': True, 'pending_budget_updates': True, 'almost_depleted': False}
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        for adg in campaign.adgroup_set.all():
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED,
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

    def test_get_account_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE,
            dash.infobox_helpers.get_account_running_status(campaign.account)
        )

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )

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
            dash.infobox_helpers.get_account_running_status(campaign.account)
        )


class AllAccountsInfoboxHelpersTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self._set_up_local_currency_settings()

    def _set_up_local_currency_settings(self):
        self.agency_local = magic_mixer.blend(dash.models.Agency)
        self.account_local = magic_mixer.blend(
            dash.models.Account,
            currency=dash.constants.Currency.EUR,
            agency=self.agency_local,
        )
        self.credit_local = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account_local,
            currency=self.account_local.currency,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal('1000.0'),
            flat_fee_cc=0,
            license_fee=decimal.Decimal('0.2'))

        self.campaign_local = magic_mixer.blend(
            dash.models.Campaign,
            account=self.account_local
        )
        magic_mixer.blend(dash.models.CampaignGoal, campaign=self.campaign_local, primary=True)
        self.budget_local = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=self.campaign_local,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=self.credit_local,
            amount=decimal.Decimal('200'),
            margin=decimal.Decimal('0'))

        self.campaign_local.settings.update(
            None,
            automatic_campaign_stop=False,
        )
        self.ad_group_local = magic_mixer.blend(
            dash.models.AdGroup,
            campaign=self.campaign_local,
        )
        self.ad_group_local.settings.update(
            None,
            b1_sources_group_daily_budget=Decimal('120'),
            b1_sources_group_enabled=True,
            b1_sources_group_state=dash.constants.AdGroupSettingsState.ACTIVE,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            skip_automation=True,
        )
        self.ad_group_source_local = magic_mixer.blend(
            dash.models.AdGroupSource,
            ad_group=self.ad_group_local
        )
        self.ad_group_source_local.settings.update(
            None,
            daily_budget_cc=Decimal('25'),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
        )
        b1_source = dash.models.Source.objects.get(id=2)
        self.b1_ad_group_source_local = magic_mixer.blend(
            dash.models.AdGroupSource,
            ad_group=self.ad_group_local,
            source=b1_source,
        )
        self.b1_ad_group_source_local.settings.update(
            None,
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
        )

    def test_calculate_daily_account_cap(self):
        account = dash.models.Account.objects.get(pk=1)
        self.assertEqual(
            600, dash.infobox_helpers.calculate_daily_account_cap(account, False))

    def test_calculate_daily_account_cap_local_currency(self):
        self.assertEqual(
            145, dash.infobox_helpers.calculate_daily_account_cap(self.account_local, False))
        self.assertEqual(
            174, dash.infobox_helpers.calculate_daily_account_cap(self.account_local, True))

    def test_calculate_allocated_and_available_credit(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(40, allocated_credit)
        self.assertEqual(60, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(100, allocated_credit)
        self.assertEqual(00, available_credit)

    def test_calculate_allocated_and_available_credit_local_currency(self):
        magic_mixer.blend(
            dash.models.CreditLineItem,
            agency=self.agency_local,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal('7300.0'),
            flat_fee_cc=0,
            license_fee=decimal.Decimal('0.2')
        )  # non local agency credit

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            self.account_local, False)
        self.assertEqual(0, allocated_credit)
        self.assertEqual(7300, available_credit)

        allocated_credit_local, available_credit_local = dash.infobox_helpers.calculate_allocated_and_available_credit(
            self.account_local, True)
        self.assertEqual(200, allocated_credit_local)
        self.assertEqual(800, available_credit_local)

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
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            agency=agency,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(40, allocated_credit)
        self.assertEqual(60, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=60,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(100, allocated_credit)
        self.assertEqual(00, available_credit)

    def test_calculate_allocated_and_available_credit_with_freed_budget(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
            freed_cc=10 * 1e4
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            account, False)
        self.assertEqual(30, allocated_credit)
        self.assertEqual(70, available_credit)
