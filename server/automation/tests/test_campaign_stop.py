import datetime
from decimal import Decimal
from mock import patch

from django.test import TestCase

from automation import campaign_stop
import dash.models


class GetMinimumRemainingBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def _configure_datetime_utcnow_mock(self, mock_datetime, utcnow_value):
        class DatetimeMock(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return utcnow_value

        mock_datetime.datetime = DatetimeMock
        mock_datetime.timedelta = datetime.timedelta

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_no_budget_changes(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 1, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('1475'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('50'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('100'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_exhausted(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 5, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('615'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_ends_today(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 12, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('900'), available_tomorrow)  # budget that will get the spend today expires tomorrow
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 15, 12))
        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('715'), available_tomorrow)  # one budget gets spend today the other expires tomorrow
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_no_budget_tomorrow(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 31, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('0'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_new_budget_tomorrow(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 1, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('900'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_different_license_fee_pcts(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 11, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('715'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)

        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 13, 12))
        available_today, available_tomorrow, max_daily_budget = campaign_stop.get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('615'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
        }, max_daily_budget)


class SwitchToLandingModeTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.email_helper.send_notification_mail')
    @patch('automation.campaign_stop.get_minimum_remaining_budget')
    def test_send_stop_campaign_email(self, mock_get_mrb, mock_send_email):
        mock_get_mrb.return_value = Decimal('100'), Decimal('150')

        dash.models.Campaign.objects.all().update(landing_mode=True)
        c1 = dash.models.Campaign.objects.get(id=1)
        c1.landing_mode = False
        c1.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertTrue(mock_send_email.called)

    @patch('utils.email_helper.send_notification_mail')
    @patch('automation.campaign_stop.get_minimum_remaining_budget')
    def test_send_depleting_budget_notification_email(self, mock_get_mrb, mock_send_email):
        mock_get_mrb.return_value = Decimal('150'), Decimal('100')

        dash.models.Campaign.objects.all().update(landing_mode=True)
        c1 = dash.models.Campaign.objects.get(id=1)
        c1.landing_mode = False
        c1.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertTrue(mock_send_email.called)


class GetMaxSettableDailyBudget(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_max_settiable_daily_budget(self):
        self.assertEqual(Decimal('585'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=1)))
        self.assertEqual(Decimal('560'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=2)))
        self.assertEqual(Decimal('530'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=3)))


class GetMaximumDailyBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_get_max_daily_budget(self):
        c = dash.models.Campaign.objects.get(id=1)
        date = datetime.date(2016, 3, 1)

        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('50'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('100'),
        }, campaign_stop._get_max_daily_budget_per_ags(date, c))

    def test_get_active_ad_groups_on_date(self):
        c1 = dash.models.Campaign.objects.get(id=1)  # ad group started on date
        c2 = dash.models.Campaign.objects.get(id=2)  # ad group stopped date before
        c3 = dash.models.Campaign.objects.get(id=3)  # active ad group from day before, stopped mid-day
        c4 = dash.models.Campaign.objects.get(id=4)  # active ad group but end date past

        date = datetime.date(2016, 3, 1)
        self.assertEqual(campaign_stop._get_ad_groups_active_on_date(date, c1), set(c1.adgroup_set.all()))
        self.assertEqual(campaign_stop._get_ad_groups_active_on_date(date, c2), set())
        self.assertEqual(campaign_stop._get_ad_groups_active_on_date(date, c3), set(c3.adgroup_set.all()))
        self.assertEqual(campaign_stop._get_ad_groups_active_on_date(date, c4), set())

    def test_get_source_max_daily_budget(self):
        ags_settings = dash.models.AdGroupSourceSettings.objects.all().order_by('-created_dt')
        ags1 = dash.models.AdGroupSource.objects.get(id=1)  # highest daily budget set on date
        ags2 = dash.models.AdGroupSource.objects.get(id=2)  # highest daily budget from day before
        ags3 = dash.models.AdGroupSource.objects.get(id=3)  # inactive since day before
        ags4 = dash.models.AdGroupSource.objects.get(id=4)  # UTC-9
        ags5 = dash.models.AdGroupSource.objects.get(id=5)  # UTC+9

        date = datetime.date(2016, 3, 1)
        self.assertEqual(Decimal('55'), campaign_stop._get_source_max_daily_budget(date, ags1, ags_settings))
        self.assertEqual(Decimal('50'), campaign_stop._get_source_max_daily_budget(date, ags2, ags_settings))
        self.assertEqual(Decimal('0'), campaign_stop._get_source_max_daily_budget(date, ags3, ags_settings))
        self.assertEqual(Decimal('20'), campaign_stop._get_source_max_daily_budget(date, ags4, ags_settings))
        self.assertEqual(Decimal('100'), campaign_stop._get_source_max_daily_budget(date, ags5, ags_settings))
