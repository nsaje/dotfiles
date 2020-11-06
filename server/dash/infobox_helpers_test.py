import datetime
import decimal
from decimal import Decimal

import mock
from django.db import connection
from django.test.client import RequestFactory

import dash.constants
import dash.infobox_helpers
import dash.models
import zemauth.models
from utils import dates_helper
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User


class InfoBoxHelpersTestCase(BaseTestCase):
    fixtures = ["test_models.yaml"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.users = User.objects.all()
        for user in cls.users:
            user.refresh_entity_permissions()

    def test_format_flight_time(self):
        start_date = datetime.datetime(2016, 1, 1).date()
        end_date = dates_helper.local_today() + datetime.timedelta(days=1)

        formatted_flight_time, days_left = dash.infobox_helpers.format_flight_time(start_date, end_date, False)

        self.assertTrue(formatted_flight_time.startswith("01/01 - "))
        self.assertEqual(2, days_left)

    def test_filter_user_by_account_type(self):
        account = dash.models.Account.objects.get(pk=1)
        account.settings.update_unsafe(None, account_type=dash.constants.AccountType.PILOT)

        su = zemauth.models.User.objects.all().filter(is_superuser=True)
        fusers = dash.infobox_helpers._filter_user_by_account_type(su, [dash.constants.AccountType.PILOT])
        self.assertEqual(su.count(), fusers.count())

        fusers = dash.infobox_helpers._filter_user_by_account_type(
            account.users.all(), [dash.constants.AccountType.PILOT]
        )
        self.assertEqual(account.users.all().count(), fusers.count())

        rest = (
            zemauth.models.User.objects.all()
            .exclude(id__in=su.values_list("id", flat=True))
            .exclude(id__in=account.users.all().values_list("id", flat=True))
        )
        rusers = dash.infobox_helpers._filter_user_by_account_type(rest, [dash.constants.AccountType.PILOT])
        self.assertEqual(0, rusers.count())

    def test_get_ideal_campaign_spend(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = dates_helper.local_today()
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
            campaign=campaign, credit=credit, amount=100, start_date=start_date, end_date=end_date, created_by=user
        )

        # ideal spend should be 0, 50% at half and 100% at the end
        # of credit

        self.assertEqual(1, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date))

        middle = start_date + datetime.timedelta(days=49)

        self.assertEqual(budget.amount / 2, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle))

        self.assertEqual(budget.amount, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date))

    def test_get_ideal_campaign_spend_multiple_nonoverlapping_budgets(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = dates_helper.local_today()
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

        self.assertEqual(1, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date))

        middle = start_date + datetime.timedelta(days=49)
        self.assertEqual(20, round(dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, middle)))

        end = start_date + datetime.timedelta(days=29)
        self.assertEqual(30, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end))

    def test_get_ideal_campaign_spend_multiple_overlapping_budgets(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        user = zemauth.models.User.objects.get(pk=1)

        start_date = dates_helper.local_today()
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
        self.assertEqual(0.75, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, start_date))

        end_of_budget_1 = start_date + datetime.timedelta(days=80)
        self.assertEqual(45, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_of_budget_1))

        self.assertEqual(60, dash.infobox_helpers.get_ideal_campaign_spend(user, campaign, end_date))

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.datetime(year=2014, month=6, day=4))
    def test_calculate_daily_campaign_cap(self, mock_local_today):
        ags = dash.models.AdGroupSource.objects.get(id=2)

        ags.settings.update(
            None,
            daily_budget_cc=Decimal("200"),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            skip_validation=True,
        )

        campaign = dash.models.Campaign.objects.get(pk=1)
        self.assertEqual(600, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

        # use raw sql to bypass model restrictions
        q = "UPDATE dash_adgroupsettings SET state=2"
        cursor = connection.cursor()
        cursor.execute(q, [])

        self.assertEqual(0, dash.infobox_helpers.calculate_daily_campaign_cap(campaign))

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.datetime(year=2014, month=6, day=4))
    def test_calculate_daily_account_cap(self, mock_local_today):
        account = dash.models.Account.objects.get(pk=1)

        self.assertEqual(600, dash.infobox_helpers.calculate_daily_account_cap(account))

    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_get_yesterday_adgroup_spend(self, mock_query):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        mock_query.return_value = [{"ad_group_id": "1", "local_yesterday_etfm_cost": 140}]

        self.assertEqual({"yesterday_etfm_cost": 140}, dash.infobox_helpers.get_yesterday_adgroup_spend(ad_group))

    def test_create_yesterday_spend_setting(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(
            {"yesterday_etfm_cost": 50}, 100, dash.constants.Currency.USD
        )

        self.assertEqual("$50.00", setting.value)
        self.assertEqual("50.00% of $100.00 Daily Spend Cap", setting.description)

        setting_1 = dash.infobox_helpers.create_yesterday_spend_setting(
            {"yesterday_etfm_cost": 110}, 100, dash.constants.Currency.USD
        )

        self.assertEqual("$110.00", setting_1.value)
        self.assertEqual("110.00% of $100.00 Daily Spend Cap", setting_1.description)

        setting_0 = dash.infobox_helpers.create_yesterday_spend_setting(
            {"yesterday_etfm_cost": 50}, 0, dash.constants.Currency.USD
        )

        self.assertEqual("$50.00", setting_0.value)
        self.assertEqual("N/A", setting_0.description)

    def test_create_yesterday_spend_setting_local_currency(self):
        setting = dash.infobox_helpers.create_yesterday_spend_setting(
            {"yesterday_etfm_cost": 50}, 100, dash.constants.Currency.EUR
        )

        self.assertEqual("€50.00", setting.value)
        self.assertEqual("50.00% of €100.00 Daily Spend Cap", setting.description)

    def test_calculate_flight_dates_all_none(self):
        start_date, end_date = dash.infobox_helpers.calculate_flight_dates(None, None, None, None)
        self.assertEqual(start_date, None)
        self.assertEqual(end_date, None)

    def test_calculate_flight_dates_ags_dates_none(self):
        mocked_budgets_start_date = datetime.date(2018, 1, 1)
        mocked_budgets_end_date = datetime.date(2018, 1, 2)
        start_date, end_date = dash.infobox_helpers.calculate_flight_dates(
            None, None, mocked_budgets_start_date, mocked_budgets_end_date
        )
        self.assertEqual(start_date, mocked_budgets_start_date)
        self.assertEqual(end_date, mocked_budgets_end_date)

    def test_calculate_flight_dates_budgets_dates_none(self):
        mocked_ags_start_date = datetime.date(2018, 1, 1)
        mocked_ags_end_date = datetime.date(2018, 1, 2)
        start_date, end_date = dash.infobox_helpers.calculate_flight_dates(
            mocked_ags_start_date, mocked_ags_end_date, None, None
        )
        self.assertEqual(start_date, mocked_ags_start_date)
        self.assertEqual(end_date, mocked_ags_end_date)

    def test_calculate_flight_dates(self):
        mocked_ags_start_date = datetime.date(2018, 1, 1)
        mocked_ags_end_date = datetime.date(2018, 1, 3)
        mocked_budgets_start_date = datetime.date(2018, 1, 2)
        mocked_budgets_end_date = datetime.date(2018, 1, 4)
        start_date, end_date = dash.infobox_helpers.calculate_flight_dates(
            mocked_ags_start_date, mocked_ags_end_date, mocked_budgets_start_date, mocked_budgets_end_date
        )
        self.assertEqual(start_date, mocked_budgets_start_date)
        self.assertEqual(end_date, mocked_ags_end_date)

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 1, 7))
    def test_calculate_budgets_flight_dates_for_date_range_no_budgets(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 15)
        )
        self.assertEqual(start_date, None)
        self.assertEqual(end_date, None)

    @mock.patch("utils.dates_helper.local_today")
    def test_calculate_budgets_flight_dates_for_date_range(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=campaign.account,
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2118, 1, 1),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=100000,
            license_fee=decimal.Decimal("0.1"),
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2018, 1, 3),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 2),
            end_date=datetime.date(2018, 1, 4),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 6),
            end_date=datetime.date(2018, 1, 8),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 8),
            end_date=datetime.date(2018, 1, 10),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 12),
            end_date=datetime.date(2018, 1, 13),
            amount=100,
        )

        mock_local_today.return_value = datetime.date(2018, 1, 7)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 15)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 6))
        self.assertEqual(end_date, datetime.date(2018, 1, 10))

        mock_local_today.return_value = datetime.date(2018, 1, 11)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 15)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 12))
        self.assertEqual(end_date, datetime.date(2018, 1, 13))

    @mock.patch("utils.dates_helper.local_today")
    def test_calculate_budgets_flight_dates_for_date_range_upcoming(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=campaign.account,
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2118, 1, 1),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=100000,
            license_fee=decimal.Decimal("0.1"),
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 4),
            end_date=datetime.date(2018, 1, 8),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 8),
            end_date=datetime.date(2018, 1, 12),
            amount=100,
        )
        magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2018, 1, 16),
            end_date=datetime.date(2018, 1, 20),
            amount=100,
        )

        mock_local_today.return_value = datetime.date(2018, 1, 1)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 30)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 4))
        self.assertEqual(end_date, datetime.date(2018, 1, 12))

        mock_local_today.return_value = datetime.date(2018, 1, 9)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 30)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 4))
        self.assertEqual(end_date, datetime.date(2018, 1, 12))

        mock_local_today.return_value = datetime.date(2018, 1, 15)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 30)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 16))
        self.assertEqual(end_date, datetime.date(2018, 1, 20))

        mock_local_today.return_value = datetime.date(2018, 1, 17)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 30)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 16))
        self.assertEqual(end_date, datetime.date(2018, 1, 20))

        mock_local_today.return_value = datetime.date(2018, 1, 24)
        start_date, end_date = dash.infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, datetime.date(2017, 12, 15), datetime.date(2018, 1, 30)
        )
        self.assertEqual(start_date, datetime.date(2018, 1, 16))
        self.assertEqual(end_date, datetime.date(2018, 1, 20))


class InfoBoxAccountHelpersTestCase(BaseTestCase):
    fixtures = ["test_models.yaml"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.accounts = magic_mixer.cycle(2).blend(dash.models.Account, currency=dash.constants.Currency.EUR)
        cls.mock_stats_yesterday = [
            {"account_id": cls.accounts[0].id, "yesterday_etfm_cost": 70, "local_yesterday_etfm_cost": 30},
            {"account_id": cls.accounts[1].id, "yesterday_etfm_cost": 70, "local_yesterday_etfm_cost": 30},
        ]
        cls.mock_stats_mtd = [
            {
                "account_id": cls.accounts[0].id,
                "e_media_cost": 50,
                "et_cost": 60,
                "etfm_cost": 70,
                "local_e_media_cost": 10,
                "local_et_cost": 20,
                "local_etfm_cost": 30,
            },
            {
                "account_id": cls.accounts[1].id,
                "e_media_cost": 50,
                "et_cost": 60,
                "etfm_cost": 70,
                "local_e_media_cost": 10,
                "local_et_cost": 20,
                "local_etfm_cost": 30,
            },
        ]

    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_get_yesterday_accounts_spend(self, mock_query):
        mock_query.return_value = self.mock_stats_yesterday
        self.assertEqual(
            {"yesterday_etfm_cost": 140}, dash.infobox_helpers.get_yesterday_accounts_spend(self.accounts, False)
        )

        # local
        self.assertEqual(
            {"yesterday_etfm_cost": 60}, dash.infobox_helpers.get_yesterday_accounts_spend(self.accounts, True)
        )

        yesterday = dates_helper.local_yesterday()
        constraints = {
            "account_id": [account.id for account in self.accounts],
            "date__gte": yesterday,
            "date__lte": yesterday,
        }
        self.assertEqual(mock_query.call_args[0], (["account_id"], constraints))

    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_get_mtd_accounts_spend(self, mock_query):
        mock_query.return_value = self.mock_stats_mtd
        self.assertEqual(
            {"e_media_cost": 100, "et_cost": 120, "etfm_cost": 140},
            dash.infobox_helpers.get_mtd_accounts_spend(self.accounts, False),
        )

        # local
        self.assertEqual(
            {"e_media_cost": 20, "et_cost": 40, "etfm_cost": 60},
            dash.infobox_helpers.get_mtd_accounts_spend(self.accounts, True),
        )

        month_start = dates_helper.local_today().replace(day=1)
        constraints = {"account_id": [account.id for account in self.accounts], "date__gte": month_start}
        self.assertEqual(mock_query.call_args[0], (["account_id"], constraints))

    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_get_yesterday_account_spend(self, mock_query):
        mock_query.return_value = [self.mock_stats_yesterday[0]]
        account = self.accounts[0]

        self.assertEqual({"yesterday_etfm_cost": 30}, dash.infobox_helpers.get_yesterday_account_spend(account))

        yesterday = dates_helper.local_yesterday()
        constraints = {"account_id": [account.id], "date__gte": yesterday, "date__lte": yesterday}
        self.assertEqual(mock_query.call_args[0], (["account_id"], constraints))

    def test_count_active_accounts(self):
        today = dates_helper.local_today()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

        all_adgset = dash.models.AdGroupSettings.objects.filter(ad_group__campaign__account__id=1)
        for adgset in all_adgset:
            new_adgset = adgset.copy_settings()
            new_adgset.start_date = today
            new_adgset.end_date = today + datetime.timedelta(days=1)
            new_adgset.save(None)

        self.assertEqual(1, dash.infobox_helpers.count_active_accounts(None, None))

    def _make_a_john(self, email=None):
        ordinary_john = zemauth.models.User.objects.create_user(
            username=email or "Janez", email=email or "janez.janez@arnes.si", password="janez"
        )
        ordinary_john.last_login = datetime.datetime.utcnow()
        ordinary_john.save()
        return ordinary_john

    def test_get_weekly_logged_in_users(self):
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

        for u in zemauth.models.User.objects.all():
            if "zemanta" not in u.email:
                continue
            u.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            u.save()

        # zemanta mail should be skipped when counting mails
        self.assertEqual(0, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

        john = self._make_a_john()
        john.last_login = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        john.save()
        self.assertEqual(1, dash.infobox_helpers.count_weekly_logged_in_users(None, None))

    def test_get_disabled_running_status_account(self):
        # adgroup is inactive and no active sources
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        ad_group.campaign.account.is_disabled = True
        ad_group.campaign.account.save(None)
        normal_user = zemauth.models.User.objects.get(id=2)

        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED, dash.infobox_helpers.get_campaign_running_status(ad_group.campaign)
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED,
            dash.infobox_helpers.get_account_running_status(ad_group.campaign.account),
        )

    def test_get_disabled_running_status_agency(self):
        # adgroup is inactive and no active sources
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        ad_group.campaign.account.agency = dash.models.Agency()
        ad_group.campaign.account.agency.is_disabled = True
        ad_group.campaign.account.agency.save(None)
        normal_user = zemauth.models.User.objects.get(id=2)

        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED, dash.infobox_helpers.get_campaign_running_status(ad_group.campaign)
        )
        self.assertEqual(
            dash.constants.InfoboxStatus.DISABLED,
            dash.infobox_helpers.get_account_running_status(ad_group.campaign.account),
        )

    def test_get_adgroup_running_status(self):
        # adgroup is inactive and no active sources
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.INACTIVE,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            created_dt=datetime.datetime.utcnow(),
        )

        normal_user = zemauth.models.User.objects.get(id=2)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED, dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        # adgroup is active and sources are active
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
        )

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE, dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = ad_group.campaign.real_time_campaign_stop
            ad_group.campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": False}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": False,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": False,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": True,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # campaign is on autopilot
        ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            dash.constants.InfoboxStatus.BUDGET_OPTIMIZATION,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )
        ad_group.campaign.settings.update_unsafe(None, autopilot=False)

        # adgroup is active, sources are active and adgroup is on CPC autopilot
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
        )

        self.assertEqual(
            dash.constants.InfoboxStatus.OPTIMAL_BID,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )

        # adgroup is active, sources are active and adgroup is on CPC+Budget autopilot
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )

        self.assertEqual(
            dash.constants.InfoboxStatus.OPTIMAL_BID,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = ad_group.campaign.real_time_campaign_stop
            ad_group.campaign.set_real_time_campaign_stop(None, True)

            # adgroup is active and on CPC autopilot with pending budget updates
            start_date = dates_helper.local_today()
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=datetime.datetime.utcnow(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,  # price_discovery
            )
            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            # adgroup is active and on CPC+Budget autopilot with pending budget updates
            start_date = dates_helper.local_today()
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=datetime.datetime.utcnow(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,  # autopilot
            )

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID,
                dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # adgroup is active but sources are inactive
        source_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).all()
        for agss in source_settings:
            agss.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)

        self.assertEqual(
            dash.constants.InfoboxStatus.OPTIMAL_BID,
            dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group),
        )

        # adgroup is inactive but sources are active
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).all()
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED, dash.infobox_helpers.get_adgroup_running_status(normal_user, ad_group)
        )

    def test_get_campaign_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE, dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE, dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            dash.constants.InfoboxStatus.BUDGET_OPTIMIZATION, dash.infobox_helpers.get_campaign_running_status(campaign)
        )

        campaign.settings.update_unsafe(None, autopilot=True)

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION,
                dash.infobox_helpers.get_campaign_running_status(campaign),
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        campaign.settings.update_unsafe(None, autopilot=False)

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": False}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED,
                dash.infobox_helpers.get_campaign_running_status(campaign),
            )

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
                dash.infobox_helpers.get_campaign_running_status(campaign),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": False,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE, dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": True,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET,
                dash.infobox_helpers.get_campaign_running_status(campaign),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                dash.constants.InfoboxStatus.ACTIVE, dash.infobox_helpers.get_campaign_running_status(campaign)
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        for adg in campaign.adgroup_set.all():
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED, dash.infobox_helpers.get_campaign_running_status(campaign)
        )

    def test_get_account_running_status(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(
            dash.constants.InfoboxStatus.INACTIVE, dash.infobox_helpers.get_account_running_status(campaign.account)
        )

        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )

        source_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).all()[:1]
        for agss in source_settings:
            new_agss = agss.copy_settings()
            new_agss.state = dash.constants.AdGroupSourceSettingsState.ACTIVE
            new_agss.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.ACTIVE, dash.infobox_helpers.get_account_running_status(campaign.account)
        )

        for adg in dash.models.AdGroup.objects.filter(campaign__account=campaign.account):
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            dash.constants.InfoboxStatus.STOPPED, dash.infobox_helpers.get_account_running_status(campaign.account)
        )


class CountActiveAgencyAccountsTestCase(BaseTestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        super().setUp()
        self.account_manager = magic_mixer.blend_user()
        self.agency_manager = magic_mixer.blend_user()

    def test_count_active_agency_accounts(self):
        today = dates_helper.local_today()

        self.assertEqual(0, dash.infobox_helpers.count_active_accounts(None, None))

        all_adgset = dash.models.AdGroupSettings.objects.filter(ad_group__campaign__account__id=1)
        for adgset in all_adgset:
            new_adgset = adgset.copy_settings()
            new_adgset.start_date = today
            new_adgset.end_date = today + datetime.timedelta(days=1)
            new_adgset.save(None)

        self.assertEqual(0, dash.infobox_helpers.count_active_agency_accounts(self.account_manager))

        account = dash.models.Account.objects.get(pk=1)
        test_helper.add_entity_permissions(self.account_manager, [Permission.READ, Permission.WRITE], account)
        self.assertEqual(1, dash.infobox_helpers.count_active_agency_accounts(self.account_manager))

        r = RequestFactory().get("")
        r.user = self.account_manager

        agency = dash.models.Agency(name="Test Agency")
        agency.save(r)
        account.agency = agency
        account.save(r)

        self.assertEqual(0, dash.infobox_helpers.count_active_agency_accounts(self.agency_manager))

        test_helper.add_entity_permissions(self.agency_manager, [Permission.READ, Permission.WRITE], agency)
        self.assertEqual(1, dash.infobox_helpers.count_active_agency_accounts(self.agency_manager))


class AllAccountsInfoboxHelpersTestCase(BaseTestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        self._set_up_local_currency_settings()

    def _set_up_local_currency_settings(self):
        self.agency_local = magic_mixer.blend(dash.models.Agency)
        self.account_local = magic_mixer.blend(
            dash.models.Account, currency=dash.constants.Currency.EUR, agency=self.agency_local
        )
        self.credit_local = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account_local,
            currency=self.account_local.currency,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            license_fee=decimal.Decimal("0.2"),
        )

        self.campaign_local = magic_mixer.blend(dash.models.Campaign, account=self.account_local)
        magic_mixer.blend(dash.models.CampaignGoal, campaign=self.campaign_local, primary=True)
        self.budget_local = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=self.campaign_local,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=self.credit_local,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0"),
        )

        self.campaign_local.settings.update(None)
        self.ad_group_local = magic_mixer.blend(dash.models.AdGroup, campaign=self.campaign_local)
        self.ad_group_local.settings.update(
            None,
            b1_sources_group_daily_budget=Decimal("120"),
            b1_sources_group_enabled=True,
            b1_sources_group_state=dash.constants.AdGroupSettingsState.ACTIVE,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            skip_automation=True,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
        )
        self.ad_group_source_local = magic_mixer.blend(
            dash.models.AdGroupSource,
            ad_group=self.ad_group_local,
            source__source_type__min_daily_budget=Decimal("0.0"),
            source__source_type__max_daily_budget=Decimal("1000.0"),
        )
        self.ad_group_source_local.settings.update(
            None,
            daily_budget_cc=Decimal("25"),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            skip_validation=True,
        )
        b1_source = dash.models.Source.objects.get(id=2)
        self.b1_ad_group_source_local = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group_local, source=b1_source
        )
        self.b1_ad_group_source_local.settings.update(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

    def test_calculate_daily_account_cap(self):
        self.assertEqual(174, dash.infobox_helpers.calculate_daily_account_cap(self.account_local))

    @mock.patch("utils.dates_helper.local_today", return_value=dates_helper.local_today() + datetime.timedelta(days=1))
    def test_calculate_daily_account_cap_expired(self, _):
        self.assertEqual(0, dash.infobox_helpers.calculate_daily_account_cap(self.account_local))

    def test_calculate_allocated_and_available_credit(self):
        account = dash.models.Account.objects.get(pk=1)
        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        user = zemauth.models.User.objects.get(pk=1)
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign, credit=credit, amount=40, start_date=start_date, end_date=end_date, created_by=user
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(40, allocated_credit)
        self.assertEqual(60, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign, credit=credit, amount=60, start_date=start_date, end_date=end_date, created_by=user
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, allocated_credit)
        self.assertEqual(00, available_credit)

    def test_calculate_allocated_and_available_credit_local_currency(self):
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(
            self.account_local
        )
        self.assertEqual(200, allocated_credit)
        self.assertEqual(800, available_credit)

    def test_calculate_allocated_and_available_agency_credit(self):
        user = zemauth.models.User.objects.get(pk=1)
        r = RequestFactory().get("")
        r.user = user

        agency = dash.models.Agency(name="SOVA")
        agency.save(r)

        account = dash.models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(r)

        campaign = dash.models.Campaign.objects.get(pk=1)
        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(0, available_credit)
        self.assertEqual(0, allocated_credit)

        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            agency=agency,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign, credit=credit, amount=40, start_date=start_date, end_date=end_date, created_by=user
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(40, allocated_credit)
        self.assertEqual(60, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign, credit=credit, amount=60, start_date=start_date, end_date=end_date, created_by=user
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
        start_date = dates_helper.local_today()
        end_date = start_date + datetime.timedelta(days=99)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(100, available_credit)

        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=40,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
            freed_cc=10 * 1e4,
        )

        allocated_credit, available_credit = dash.infobox_helpers.calculate_allocated_and_available_credit(account)
        self.assertEqual(30, allocated_credit)
        self.assertEqual(70, available_credit)

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 7, 20))
    def test_refunds(self, mock_local_today):
        account = dash.models.Account.objects.get(pk=1)
        user = zemauth.models.User.objects.get(pk=1)
        start_date = datetime.date(2018, 7, 7)
        end_date = datetime.date(2018, 8, 7)
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account=account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=user,
        )
        dash.models.RefundLineItem.objects.create_unsafe(
            account=account,
            credit=credit,
            start_date=start_date.replace(day=1),
            end_date=start_date.replace(day=31),
            amount=0,
            created_by=user,
        )
        refunded = dash.infobox_helpers.calculate_credit_refund(account)
        self.assertEqual(refunded, 0)

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_yesterday_data_complete(self):
        yesterday_data_settings = dash.infobox_helpers.create_yesterday_data_setting()
        self.assertEqual(yesterday_data_settings.flag, "Complete")
