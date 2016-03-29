import datetime
from decimal import Decimal
from mock import call, patch

from django.test import TestCase

import actionlog.constants
from automation import campaign_stop
import dash.models
from utils import dates_helper, test_helper


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

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('1395'), remaining_today)
        self.assertEqual(Decimal('1395'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('50'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('100'),
            6: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_exhausted(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 5, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('535'), remaining_today)
        self.assertEqual(Decimal('535'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_ends_today(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 12, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('1535'), remaining_today)
        self.assertEqual(Decimal('900'), available_tomorrow)  # budget that will get the spend today expires tomorrow
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 15, 12))
        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('1535'), remaining_today)
        self.assertEqual(Decimal('635'), available_tomorrow)  # one budget gets spend today the other expires tomorrow
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_no_budget_tomorrow(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 3, 31, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('635'), remaining_today)
        self.assertEqual(Decimal('0'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_new_budget_tomorrow(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 1, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('0'), remaining_today)
        self.assertEqual(Decimal('900'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_different_license_fee_pcts(self, mock_datetime):
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 11, 12))
        c1 = dash.models.Campaign.objects.get(id=1)

        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('635'), remaining_today)
        self.assertEqual(Decimal('635'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)

        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 4, 13, 12))
        remaining_today, available_tomorrow, max_daily_budget = campaign_stop._get_minimum_remaining_budget(c1)
        self.assertEqual(Decimal('535'), remaining_today)
        self.assertEqual(Decimal('535'), available_tomorrow)
        self.assertEqual({
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('80'),
            6: Decimal('80'),
        }, max_daily_budget)


class SwitchToLandingModeTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def setUp(self):
        for campaign in dash.models.Campaign.objects.exclude(id=1):
            new_settings = campaign.get_current_settings().copy_settings()
            new_settings.landing_mode = True
            new_settings.save(None)

        new_settings = dash.models.Campaign.objects.get(id=1).get_current_settings().copy_settings()
        new_settings.landing_mode = False
        new_settings.save(None)

    @patch('utils.email_helper.send_notification_mail')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_depleting_budget(self, mock_get_mrb, mock_send_email):
        mock_get_mrb.return_value = Decimal('200'), Decimal('150'), {1: Decimal('100')}

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertTrue(mock_send_email.called)

    @patch('actionlog.zwei_actions.send')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode(self, mock_get_mrb, mock_send_email, mock_send_actions):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), {1: Decimal('110')}

        in_30_days = datetime.datetime.utcnow().date() + datetime.timedelta(days=30)
        campaign = dash.models.Campaign.objects.get(id=1)
        for ad_group in campaign.adgroup_set.all():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = in_30_days
            new_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertTrue(mock_send_email.called)

        current_campaign_settings = campaign.get_current_settings()
        self.assertTrue(current_campaign_settings.landing_mode)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_campaign_settings.system_user)

        for ad_group in campaign.adgroup_set.all():
            current_ad_group_settings = ad_group.get_current_settings()
            if current_ad_group_settings.state == dash.constants.AdGroupSettingsState.ACTIVE:
                self.assertEqual(datetime.datetime.utcnow().date(), current_ad_group_settings.end_date)
                self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_ad_group_settings.system_user)
            else:
                self.assertEqual(in_30_days, current_ad_group_settings.end_date)
                self.assertEqual(None, current_ad_group_settings.system_user)

        active_ad_group_sources = set()
        for ad_group in campaign.adgroup_set.all().exclude_archived():
            for ags in ad_group.adgroupsource_set.all():
                if ags.get_current_settings().state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
                    active_ad_group_sources.add(ags)
        self.assertEqual(len(active_ad_group_sources), len(mock_send_actions.call_args[0][0]))

    @patch('automation.campaign_stop._set_end_date_to_today')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode_manual(self, mock_get_mrb, mock_send_email, mock_set_end_date):
        mock_get_mrb.return_value = Decimal('100'), Decimal('150')
        mock_get_mrb.return_value = Decimal('200'), Decimal('150'), {1: Decimal('100')}

        campaign = dash.models.Campaign.objects.get(id=1)
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = False
        new_campaign_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertFalse(mock_get_mrb.called)
        self.assertFalse(mock_send_email.called)
        self.assertFalse(mock_set_end_date.called)

    @patch('automation.campaign_stop._set_end_date_to_today')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode_already_landing(self, mock_get_mrb, mock_send_email, mock_set_end_date):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), {1: Decimal('150')}

        campaign = dash.models.Campaign.objects.get(id=1)
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = True
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertFalse(mock_get_mrb.called)
        self.assertFalse(mock_send_email.called)
        self.assertFalse(mock_set_end_date.called)

    @patch('actionlog.zwei_actions.send')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode_inactive_ad_group(self, mock_get_mrb, mock_send_email, mock_send_action):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), {1: Decimal('150')}

        campaign = dash.models.Campaign.objects.get(id=1)
        in_30_days = datetime.datetime.utcnow().date() + datetime.timedelta(days=30)
        for ad_group in campaign.adgroup_set.all():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = in_30_days
            new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            new_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
        self.assertTrue(mock_send_email.called)

        current_campaign_settings = campaign.get_current_settings()
        self.assertTrue(current_campaign_settings.landing_mode)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_campaign_settings.system_user)

        for ad_group in campaign.adgroup_set.all():
            current_ad_group_settings = ad_group.get_current_settings()
            self.assertEqual(in_30_days, current_ad_group_settings.end_date)


class GetMaxSettableDailyBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.dates_helper.local_today')
    def test_get_max_settable_daily_budget(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        self.assertEqual(Decimal('425'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=1)))
        self.assertEqual(Decimal('400'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=2)))
        self.assertEqual(Decimal('370'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=3)))

    @patch('utils.dates_helper.local_today')
    def test_no_budget_remaining_today(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 4, 16)
        self.assertEqual(Decimal('0'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=1)))
        self.assertEqual(Decimal('0'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=2)))
        self.assertEqual(Decimal('0'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=3)))

    @patch('utils.dates_helper.local_today')
    def test_no_budet_tomorrow(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 31)
        self.assertEqual(Decimal('0'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=1)))
        self.assertEqual(Decimal('0'),
                         campaign_stop.get_max_settable_daily_budget(dash.models.AdGroupSource.objects.get(id=2)))
        self.assertEqual(Decimal('0'),
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
            6: Decimal('80'),
        }, campaign_stop._get_max_daily_budget_per_ags(date, c))

    def test_get_running_ad_groups_on_date(self):
        c1 = dash.models.Campaign.objects.get(id=1)  # ad group started on date
        c2 = dash.models.Campaign.objects.get(id=2)  # ad group stopped date before
        c3 = dash.models.Campaign.objects.get(id=3)  # active ad group from day before, stopped mid-day
        c4 = dash.models.Campaign.objects.get(id=4)  # active ad group but end date past
        c5 = dash.models.Campaign.objects.get(id=5)  # switched to landing mode one day before (end dt on midnight)

        date = datetime.date(2016, 3, 1)
        self.assertEqual(campaign_stop._get_ad_groups_running_on_date(date, c1),
                         set(c1.adgroup_set.all().exclude(id=3)))
        self.assertEqual(campaign_stop._get_ad_groups_running_on_date(date, c2), set())
        self.assertEqual(campaign_stop._get_ad_groups_running_on_date(date, c3), set(c3.adgroup_set.all()))
        self.assertEqual(campaign_stop._get_ad_groups_running_on_date(date, c4), set())
        self.assertEqual(campaign_stop._get_ad_groups_running_on_date(date, c5), set(c5.adgroup_set.all()))

    def test_get_source_max_daily_budget(self):
        ags_settings = dash.models.AdGroupSourceSettings.objects.all().order_by('-created_dt')
        ags1 = dash.models.AdGroupSource.objects.get(id=1)  # highest daily budget set on date
        ags2 = dash.models.AdGroupSource.objects.get(id=2)  # highest daily budget from day before
        ags3 = dash.models.AdGroupSource.objects.get(id=3)  # inactive since day before
        ags4 = dash.models.AdGroupSource.objects.get(id=4)  # UTC-9
        ags5 = dash.models.AdGroupSource.objects.get(id=5)  # UTC+9

        date = datetime.date(2016, 3, 1)
        self.assertEqual(Decimal('55'), campaign_stop._get_source_max_daily_budget(
            date, ags1, ags_settings.filter(ad_group_source_id=ags1.id)))
        self.assertEqual(Decimal('50'), campaign_stop._get_source_max_daily_budget(
            date, ags2, ags_settings.filter(ad_group_source_id=ags2.id)))
        self.assertEqual(Decimal('0'), campaign_stop._get_source_max_daily_budget(
            date, ags3, ags_settings.filter(ad_group_source_id=ags3.id)))
        self.assertEqual(Decimal('20'), campaign_stop._get_source_max_daily_budget(
            date, ags4, ags_settings.filter(ad_group_source_id=ags4.id)))
        self.assertEqual(Decimal('100'), campaign_stop._get_source_max_daily_budget(
            date, ags5, ags_settings.filter(ad_group_source_id=ags5.id)))


class SwitchCampaignToLandingModeTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_switch_campaign_to_landing_mode(self):
        campaign = dash.models.Campaign.objects.get(id=1)

        current_settings = campaign.get_current_settings()
        self.assertTrue(current_settings.automatic_campaign_stop)
        self.assertFalse(current_settings.landing_mode)

        campaign_stop._switch_campaign_to_landing_mode(campaign)

        new_settings = campaign.get_current_settings()
        self.assertTrue(new_settings.landing_mode)

        for ad_group in campaign.adgroup_set.all():
            if ad_group.id in campaign.adgroup_set.all().filter_active().values_list('id', flat=True):
                self.assertTrue(ad_group.get_current_settings().landing_mode)
            else:
                self.assertFalse(ad_group.get_current_settings().landing_mode)


class SetAdGroupEndDateTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('actionlog.zwei_actions.send')
    def test_set_ad_group_end_date(self, mock_zwei_send):
        ad_group = dash.models.AdGroup.objects.get(id=1)

        current_settings = ad_group.get_current_settings()
        self.assertEqual(None, current_settings.end_date)

        today = dates_helper.utc_today()
        actions = campaign_stop._set_ad_group_end_date(ad_group, today)

        new_settings = ad_group.get_current_settings()
        self.assertEqual(today, new_settings.end_date)

        ad_group_source_ids = dash.models.AdGroupSource.objects.filter(ad_group=ad_group).values_list('id', flat=True)

        self.assertEqual(len(ad_group_source_ids), len(actions))
        for action in actions:
            self.assertTrue(action.ad_group_source_id in ad_group_source_ids)
            self.assertEqual(actionlog.constants.Action.SET_CAMPAIGN_STATE, action.action)

        self.assertFalse(mock_zwei_send.called)


class UpadateCampaignsInLandingTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('actionlog.zwei_actions.send')
    @patch('automation.autopilot_plus.prefetch_autopilot_data')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    @patch('automation.autopilot_budgets.get_autopilot_daily_budget_recommendations')
    def test_set_new_daily_budgets(self, mock_get_ap_rec, mock_get_mrb, mock_prefetch_ap_data, mock_zwei_send):
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        mock_get_mrb.return_value = Decimal(401), None, None
        mock_prefetch_ap_data.return_value = {
            ag1: "Ad group 1 mock data",
            ag2: "Ad group 2 mock data",
        }

        def ret_get_ap_rec(ad_group, daily_budget_cap, data, goal):
            # mock old daily budgets, they're not taken from fixtures
            ret = {
                ag1: {
                    dash.models.AdGroupSource.objects.get(id=1): {"old_budget": Decimal(10), "new_budget": Decimal(5)},
                    dash.models.AdGroupSource.objects.get(id=2): {"old_budget": Decimal(10), "new_budget": Decimal(10)},
                    dash.models.AdGroupSource.objects.get(id=4): {"old_budget": Decimal(8), "new_budget": Decimal(4)},
                    dash.models.AdGroupSource.objects.get(id=5): {"old_budget": Decimal(10), "new_budget": Decimal(10)}
                },
                ag2: {
                    dash.models.AdGroupSource.objects.get(id=6): {"old_budget": Decimal(15), "new_budget": Decimal(5)}
                },
            }

            return ret[ad_group]
        mock_get_ap_rec.side_effect = ret_get_ap_rec

        campaign = dash.models.Campaign.objects.get(id=1)
        new_actions = campaign_stop._set_new_daily_budgets(campaign)

        mock_prefetch_ap_data.assert_called_once_with(test_helper.QuerySetMatcher([ag1, ag2]))

        ap_rec_calls = [
            call(ag1, Decimal(200), "Ad group 1 mock data", goal=None),
            call(ag2, Decimal(200), "Ad group 2 mock data", goal=None),
        ]
        mock_get_ap_rec.assert_has_calls(ap_rec_calls, any_order=True)

        self.assertFalse(mock_zwei_send.called)
        self.assertEqual(3, len(new_actions))

        for action in new_actions:
            self.assertTrue(action.ad_group_source_id in [1, 4, 6])  # where new budget differs from old budget
            self.assertEqual(actionlog.constants.Action.SET_CAMPAIGN_STATE, action.action)

            current_settings = action.ad_group_source.get_current_settings()
            self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_settings.system_user)
