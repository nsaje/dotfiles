import datetime
from decimal import Decimal
from mock import call, patch

from django.test import TestCase

from automation import campaign_stop
import dash.models
import reports.models

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
        now = datetime.datetime(2016, 3, 1, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('1415'), remaining_today)
        self.assertEqual(Decimal('1415'), available_tomorrow)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_exhausted(self, mock_datetime):
        now = datetime.datetime(2016, 3, 5, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('535'), remaining_today)
        self.assertEqual(Decimal('535'), available_tomorrow)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_one_budget_ends_today(self, mock_datetime):
        now = datetime.datetime(2016, 3, 12, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('1535'), remaining_today)
        self.assertEqual(Decimal('900'), available_tomorrow)  # budget that will get the spend today expires tomorrow

        now = datetime.datetime(2016, 3, 15, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('1535'), remaining_today)
        self.assertEqual(Decimal('635'), available_tomorrow)  # one budget gets spend today the other expires tomorrow

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_no_budget_tomorrow(self, mock_datetime):
        now = datetime.datetime(2016, 3, 31, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('635'), remaining_today)
        self.assertEqual(Decimal('0'), available_tomorrow)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_new_budget_tomorrow(self, mock_datetime):
        now = datetime.datetime(2016, 4, 1, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('0'), remaining_today)
        self.assertEqual(Decimal('900'), available_tomorrow)

    @patch('utils.dates_helper.datetime')
    def test_get_mrb_different_license_fee_pcts(self, mock_datetime):
        now = datetime.datetime(2016, 4, 11, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)
        c1 = dash.models.Campaign.objects.get(id=1)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('635'), remaining_today)
        self.assertEqual(Decimal('635'), available_tomorrow)

        now = datetime.datetime(2016, 4, 13, 12)
        self._configure_datetime_utcnow_mock(mock_datetime, now)

        max_daily_budget = campaign_stop._get_max_daily_budget(now.date(), c1)
        remaining_today, available_tomorrow, unattributed_budget = campaign_stop._get_minimum_remaining_budget(
            c1, max_daily_budget)
        self.assertEqual(Decimal('535'), remaining_today)
        self.assertEqual(Decimal('535'), available_tomorrow)


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
    @patch('automation.campaign_stop._get_max_daily_budget')
    @patch('automation.campaign_stop._get_current_daily_budget')
    @patch('automation.campaign_stop._switch_campaign_to_landing_mode')
    @patch('utils.k1_helper.update_ad_group')
    def test_depleting_budget(self, mock_k1_ping, mock_switch, mock_current_daily_budget, mock_max_daily_budget,
                              mock_get_mrb, mock_send_email):
        mock_get_mrb.return_value = Decimal('200'), Decimal('150'), Decimal('0')
        mock_max_daily_budget.return_value = Decimal('100')
        mock_current_daily_budget.return_value = Decimal('100')

        campaign_stop.switch_low_budget_campaigns_to_landing_mode(dash.models.Campaign.objects.all().exclude_landing())
        self.assertTrue(mock_send_email.called)
        self.assertFalse(mock_switch.called)
        self.assertEqual(mock_k1_ping.call_count, 0)

    @patch('actionlog.zwei_actions.send')
    @patch('utils.email_helper.send_notification_mail')
    @patch('automation.campaign_stop._get_max_daily_budget')
    @patch('automation.campaign_stop._get_current_daily_budget')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    @patch('utils.k1_helper.update_ad_group')
    def test_switch_to_landing_mode(self, mock_k1_ping, mock_get_mrb, mock_current_daily_budget, mock_max_daily_budget,
                                    mock_send_email, mock_send_actions):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), Decimal('0')
        mock_max_daily_budget.return_value = Decimal('150')
        mock_current_daily_budget.return_value = Decimal('150')

        in_30_days = dates_helper.local_today() + datetime.timedelta(days=30)
        campaign = dash.models.Campaign.objects.get(id=1)
        for ad_group in campaign.adgroup_set.all():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = in_30_days
            new_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode(dash.models.Campaign.objects.all().exclude_landing())
        self.assertTrue(mock_send_email.called)
        self.assertEqual(mock_k1_ping.call_count, 4)

        current_campaign_settings = campaign.get_current_settings()
        self.assertTrue(current_campaign_settings.landing_mode)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_campaign_settings.system_user)

        for ad_group in campaign.adgroup_set.all():
            current_ad_group_settings = ad_group.get_current_settings()
            if current_ad_group_settings.state == dash.constants.AdGroupSettingsState.ACTIVE:
                self.assertEqual(dates_helper.local_today(), current_ad_group_settings.end_date)
                self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_ad_group_settings.system_user)
            else:
                self.assertEqual(in_30_days, current_ad_group_settings.end_date)
                self.assertEqual(None, current_ad_group_settings.system_user)

        active_ad_group_sources = set()
        for ad_group in campaign.adgroup_set.all().exclude_archived():
            for ags in ad_group.adgroupsource_set.all():
                if ags.get_current_settings().state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
                    active_ad_group_sources.add(ags)

    @patch('automation.campaign_stop._set_end_date_to_today')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode_manual(self, mock_get_mrb, mock_send_email, mock_set_end_date):
        mock_get_mrb.return_value = Decimal('100'), Decimal('150'), Decimal('0')

        campaign = dash.models.Campaign.objects.get(id=1)
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = False
        new_campaign_settings.save(None)

        has_changed = campaign_stop.perform_landing_mode_check(
            campaign,
            campaign.get_current_settings()
        )
        self.assertFalse(has_changed)
        self.assertFalse(mock_get_mrb.called)
        self.assertFalse(mock_send_email.called)
        self.assertFalse(mock_set_end_date.called)

    @patch('automation.campaign_stop._set_end_date_to_today')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_switch_to_landing_mode_already_landing(self, mock_get_mrb, mock_send_email, mock_set_end_date):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), Decimal('0')

        campaign = dash.models.Campaign.objects.get(id=1)
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = True
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        campaign_stop.perform_landing_mode_check(
            campaign,
            campaign.get_current_settings()
        )
        self.assertTrue(mock_get_mrb.called)
        self.assertFalse(mock_send_email.called)
        self.assertFalse(mock_set_end_date.called)

    @patch('actionlog.zwei_actions.send')
    @patch('automation.campaign_stop._send_campaign_stop_notification_email')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    @patch('automation.campaign_stop._get_current_daily_budget')
    def test_switch_to_landing_mode_inactive_ad_group(self, mock_get_current, mock_get_mrb, mock_send_email,
                                                      mock_send_action):
        mock_get_mrb.return_value = Decimal('200'), Decimal('100'), Decimal('0')
        mock_get_current.return_value = Decimal('101')

        campaign = dash.models.Campaign.objects.get(id=1)
        in_30_days = dates_helper.local_today() + datetime.timedelta(days=30)
        for ad_group in campaign.adgroup_set.all():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = in_30_days
            new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            new_settings.save(None)

        campaign_stop.switch_low_budget_campaigns_to_landing_mode(dash.models.Campaign.objects.all().exclude_landing())
        self.assertTrue(mock_send_email.called)

        current_campaign_settings = campaign.get_current_settings()
        self.assertTrue(current_campaign_settings.landing_mode)
        self.assertEqual(dash.constants.SystemUserType.CAMPAIGN_STOP, current_campaign_settings.system_user)

        for ad_group in campaign.adgroup_set.all():
            current_ad_group_settings = ad_group.get_current_settings()
            self.assertEqual(in_30_days, current_ad_group_settings.end_date)


class CanChangeDailyBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.dates_helper.local_today')
    def test_get_max_settable_source_budget(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        ags1 = dash.models.AdGroupSource.objects.get(id=1)
        ags2 = dash.models.AdGroupSource.objects.get(id=2)
        ags3 = dash.models.AdGroupSource.objects.get(id=3)

        self.assertEqual(
            Decimal('425'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('400'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('425'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('450'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('400'),
            campaign_stop.get_max_settable_source_budget(
                ags2,
                Decimal('390'),
                ags2.ad_group.campaign,
                ags2.get_current_settings(),
                ags2.ad_group.get_current_settings(),
                ags2.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('400'),
            campaign_stop.get_max_settable_source_budget(
                ags2,
                Decimal('420'),
                ags2.ad_group.campaign,
                ags2.get_current_settings(),
                ags2.ad_group.get_current_settings(),
                ags2.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('370'),
            campaign_stop.get_max_settable_source_budget(
                ags3,
                Decimal('350'),
                ags3.ad_group.campaign,
                ags3.get_current_settings(),
                ags3.ad_group.get_current_settings(),
                ags3.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_no_budget_remaining_today(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 4, 16)
        ags1 = dash.models.AdGroupSource.objects.get(id=1)
        ags2 = dash.models.AdGroupSource.objects.get(id=2)
        ags3 = dash.models.AdGroupSource.objects.get(id=3)

        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('60'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags2,
                Decimal('40'),
                ags2.ad_group.campaign,
                ags2.get_current_settings(),
                ags2.ad_group.get_current_settings(),
                ags2.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags3,
                Decimal('10'),
                ags3.ad_group.campaign,
                ags3.get_current_settings(),
                ags3.ad_group.get_current_settings(),
                ags3.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_max_daily_budgets_higher(self, mock_local_today):
        today = datetime.date(2016, 4, 16)
        mock_local_today.return_value = today
        ags1 = dash.models.AdGroupSource.objects.get(id=1)
        ags2 = dash.models.AdGroupSource.objects.get(id=2)
        ags3 = dash.models.AdGroupSource.objects.get(id=3)

        max_daily_budgets = campaign_stop._get_max_daily_budget_per_ags(
            today, dash.models.Campaign.objects.get(id=1)
        )
        self.assertEqual({
            1: Decimal('55.0000'),
            2: Decimal('30.0000'),
            3: 0,
            4: Decimal('20.0000'),
            5: Decimal('80.0000'),
            6: Decimal('80.0000'),
            7: 0,
        }, max_daily_budgets)

        self.assertEqual(
            Decimal('55'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('50'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('30'),
            campaign_stop.get_max_settable_source_budget(
                ags2,
                Decimal('25'),
                ags2.ad_group.campaign,
                ags2.get_current_settings(),
                ags2.ad_group.get_current_settings(),
                ags2.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags3,
                Decimal('0'),
                ags3.ad_group.campaign,
                ags3.get_current_settings(),
                ags3.ad_group.get_current_settings(),
                ags3.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_no_budet_tomorrow(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 31)
        ags1 = dash.models.AdGroupSource.objects.get(id=1)
        ags2 = dash.models.AdGroupSource.objects.get(id=2)
        ags3 = dash.models.AdGroupSource.objects.get(id=3)

        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('60'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags2,
                Decimal('45'),
                ags2.ad_group.campaign,
                ags2.get_current_settings(),
                ags2.ad_group.get_current_settings(),
                ags2.ad_group.campaign.get_current_settings(),
            )
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop.get_max_settable_source_budget(
                ags3,
                Decimal('30'),
                ags3.ad_group.campaign,
                ags3.get_current_settings(),
                ags3.ad_group.get_current_settings(),
                ags3.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_ad_group_not_running(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        ags7 = dash.models.AdGroupSource.objects.get(id=7)

        self.assertEqual(
            Decimal('370'),
            campaign_stop.get_max_settable_source_budget(
                ags7,
                Decimal('30'),
                ags7.ad_group.campaign,
                ags7.get_current_settings(),
                ags7.ad_group.get_current_settings(),
                ags7.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_campaign_in_landing(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        ags8 = dash.models.AdGroupSource.objects.get(id=8)

        self.assertEqual(
            0,
            campaign_stop.get_max_settable_source_budget(
                ags8,
                Decimal('100'),
                ags8.ad_group.campaign,
                ags8.get_current_settings(),
                ags8.ad_group.get_current_settings(),
                ags8.ad_group.campaign.get_current_settings(),
            )
        )

        self.assertEqual(
            0,
            campaign_stop.get_max_settable_source_budget(
                ags8,
                Decimal('0'),
                ags8.ad_group.campaign,
                ags8.get_current_settings(),
                ags8.ad_group.get_current_settings(),
                ags8.ad_group.campaign.get_current_settings(),
            )
        )

    @patch('utils.dates_helper.local_today')
    def test_automatic_campaign_stop_disabled(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        ags1 = dash.models.AdGroupSource.objects.get(id=1)

        self.assertEqual(
            Decimal('425'),
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('500'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )

        new_campaign_settings = ags1.ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = False
        new_campaign_settings.save(None)

        self.assertEqual(
            None,
            campaign_stop.get_max_settable_source_budget(
                ags1,
                Decimal('500'),
                ags1.ad_group.campaign,
                ags1.get_current_settings(),
                ags1.ad_group.get_current_settings(),
                ags1.ad_group.campaign.get_current_settings(),
            )
        )


class CanEnableMediaSourcesTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_campaign_in_landing(self):
        campaign = dash.models.Campaign.objects.get(id=6)

        for ad_group in campaign.adgroup_set.all():
            can_enable = campaign_stop.can_enable_media_sources(
                ad_group, campaign, campaign.get_current_settings())
            for ad_group_source in ad_group.adgroupsource_set.all():
                self.assertFalse(can_enable[ad_group_source.id])

    def test_automatic_campaign_stop(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        new_campaign_settings = campaign.get_current_settings().copy_settings()
        new_campaign_settings.automatic_campaign_stop = False
        new_campaign_settings.save(None)

        for ad_group in campaign.adgroup_set.all():
            can_enable = campaign_stop.can_enable_media_sources(
                ad_group, campaign, campaign.get_current_settings())
            for ad_group_source in ad_group.adgroupsource_set.all():
                self.assertTrue(can_enable[ad_group_source.id])

    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_can_enable_media_sources(self, mock_get_min_remaining):
        campaign = dash.models.Campaign.objects.get(id=1)
        ad_group = dash.models.AdGroup.objects.get(id=1)

        mock_get_min_remaining.return_value = Decimal('50'), Decimal('20'), None
        can_enable = campaign_stop.can_enable_media_sources(
            ad_group, campaign, campaign.get_current_settings())
        self.assertEqual({
            1: True,
            2: True,
            3: False,  # the only inactive source
            4: True,
            5: True,
        }, can_enable)

        today = dates_helper.local_today()
        with test_helper.disable_auto_now_add(dash.models.AdGroupSourceSettings, 'created_dt'):
            # disable all sources
            for ad_group_source in ad_group.adgroupsource_set.all():
                current_settings = ad_group_source.get_current_settings()
                new_settings = current_settings.copy_settings()
                new_settings.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
                # set settings on this day for every tz
                new_settings.created_dt = datetime.datetime(today.year, today.month, today.day, 10)
                new_settings.save(None)

        can_enable = campaign_stop.can_enable_media_sources(
            ad_group, campaign, campaign.get_current_settings())
        self.assertEqual({
            1: False,
            2: False,
            3: False,
            4: True,  # the only source with enough budget for tomorrow
            5: False,
        }, can_enable)

        # sources that were active can be enabled with same budget again
        mock_get_min_remaining.return_value = Decimal('30'), Decimal('100'), None
        can_enable = campaign_stop.can_enable_media_sources(
            ad_group, campaign, campaign.get_current_settings())
        self.assertEqual({
            1: True,
            2: True,
            3: False,  # wasn't active, not enough budget for today
            4: True,
            5: True,
        }, can_enable)

        new_ags_settings = ad_group.adgroupsource_set.all().get(id=1).get_current_settings().copy_settings()
        new_ags_settings.daily_budget_cc += Decimal('5')

        with test_helper.disable_auto_now_add(dash.models.AdGroupSourceSettings, 'created_dt'):
            for ags in ad_group.adgroupsource_set.all().exclude(id=1):
                new_ags_settings = ags.get_current_settings().copy_settings()
                new_ags_settings.daily_budget_cc += Decimal('10')
                new_ags_settings.created_dt = datetime.datetime(today.year, today.month, today.day, 10, 1)
                new_ags_settings.save(None)

        mock_get_min_remaining.return_value = Decimal('5'), Decimal('100'), None
        can_enable = campaign_stop.can_enable_media_sources(
            ad_group, campaign, campaign.get_current_settings())
        self.assertEqual({
            1: True,  # will increase caps for only $5, can be enabled
            2: False,
            3: False,
            4: False,
            5: False,
        }, can_enable)

        # tomorrow's remaining budget must be fully covered
        mock_get_min_remaining.return_value = Decimal('100'), Decimal('55'), None
        can_enable = campaign_stop.can_enable_media_sources(
            ad_group, campaign, campaign.get_current_settings())
        self.assertEqual({
            1: True,
            2: True,
            3: False,
            4: True,
            5: False,
        }, can_enable)


class CanEnableAdGroupsTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def _get_ad_group_sources_settings_dict(self, ad_group):
        ret = {}
        for ags in ad_group.adgroupsource_set.all():
            ret[ags] = ags.get_current_settings()
        return ret

    def test_landing_mode(self):
        campaign = dash.models.Campaign.objects.get(id=6)
        can_enable = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
        for ad_group in campaign.adgroup_set.all():
            self.assertFalse(can_enable[ad_group.id])

    def test_automatic_campaign_stop(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        new_settings = campaign.get_current_settings().copy_settings()
        new_settings.automatic_campaign_stop = False
        new_settings.save(None)

        can_enable = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
        for ad_group in campaign.adgroup_set.all():
            self.assertTrue(can_enable[ad_group.id])

    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_can_enable_ad_groups(self, mock_get_min_remaining):
        campaign = dash.models.Campaign.objects.get(id=1)

        mock_get_min_remaining.return_value = Decimal('10'), Decimal('10'), None
        can_enable = campaign_stop.can_enable_ad_groups(campaign, campaign.get_current_settings())
        self.assertEqual({
            1: True,
            2: True,
            3: False,
        }, can_enable)

    def test_can_enable_ad_group(self):
        ad_group = dash.models.AdGroup.objects.get(id=1)

        can_enable = campaign_stop._can_enable_ad_group(
            ad_group,
            ad_group.get_current_settings(),
            self._get_ad_group_sources_settings_dict(ad_group),
            {},
            Decimal('0'),
            Decimal('0'),
        )
        self.assertTrue(can_enable)  # already enabled

        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
        new_settings.save(None)

        can_enable = campaign_stop._can_enable_ad_group(
            ad_group,
            ad_group.get_current_settings(),
            self._get_ad_group_sources_settings_dict(ad_group),
            {},
            Decimal('0'),
            Decimal('0'),
        )
        self.assertFalse(can_enable)

        max_daily_budget_per_ags = {
            1: Decimal('0'),
            2: Decimal('20'),
            3: Decimal('0'),
            4: Decimal('0'),
            5: Decimal('50'),
        }
        self.assertTrue(
            campaign_stop._can_enable_ad_group(
                ad_group,
                ad_group.get_current_settings(),
                self._get_ad_group_sources_settings_dict(ad_group),
                max_daily_budget_per_ags,
                Decimal('115'),
                Decimal('300'),
            )
        )
        self.assertFalse(
            campaign_stop._can_enable_ad_group(
                ad_group,
                ad_group.get_current_settings(),
                self._get_ad_group_sources_settings_dict(ad_group),
                max_daily_budget_per_ags,
                Decimal('114'),
                Decimal('300'),
            )
        )
        self.assertFalse(
            campaign_stop._can_enable_ad_group(
                ad_group,
                ad_group.get_current_settings(),
                self._get_ad_group_sources_settings_dict(ad_group),
                max_daily_budget_per_ags,
                Decimal('115'),
                Decimal('299'),
            )
        )


class GetMinBudgetIncreaseTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('automation.campaign_stop._get_user_daily_budget_per_ags')
    @patch('automation.campaign_stop._get_max_daily_budget_per_ags')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_min_for_today(self, mock_min_remaining, mock_max_budgets, mock_user_budgets):
        campaign = dash.models.Campaign.objects.get(id=1)

        mock_max_budgets.return_value = {
            1: Decimal('20.00'),
            2: Decimal('40.00'),
            4: Decimal('5.00')
        }

        mock_user_budgets.return_value = {
            1: Decimal('10.00'),
            3: Decimal('10.00'),
            4: Decimal('20.00')
        }

        mock_min_remaining.return_value = Decimal('0.0'), Decimal('10.0'), Decimal('50.0')

        min_budget_increase = campaign_stop.get_min_budget_increase(campaign)
        mock_min_remaining.assert_called_once_with(campaign, Decimal('90.00'))
        self.assertEqual(min_budget_increase, Decimal('50.0'))

    @patch('automation.campaign_stop._get_user_daily_budget_per_ags')
    @patch('automation.campaign_stop._get_max_daily_budget_per_ags')
    @patch('automation.campaign_stop._get_minimum_remaining_budget')
    def test_min_for_tomorrow(self, mock_min_remaining, mock_max_budgets, mock_user_budgets):
        campaign = dash.models.Campaign.objects.get(id=1)

        mock_max_budgets.return_value = {
            1: Decimal('20.00'),
            2: Decimal('40.00'),
            4: Decimal('5.00')
        }

        mock_user_budgets.return_value = {
            1: Decimal('10.00'),
            3: Decimal('10.00'),
            4: Decimal('20.00')
        }

        mock_min_remaining.return_value = Decimal('0.00'), Decimal('10.0'), Decimal('0')

        min_budget_increase = campaign_stop.get_min_budget_increase(campaign)
        mock_min_remaining.assert_called_once_with(campaign, Decimal('90.00'))
        self.assertEqual(min_budget_increase, Decimal('30.0'))


class GetUserDailyBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_get_user_daily_budget(self):
        campaign = dash.models.Campaign.objects.get(id=6)  # campaign in landing
        user_daily_budget = campaign_stop._get_user_daily_budget_per_ags(campaign)
        self.assertEqual(user_daily_budget, {
            8: Decimal('200.0000'),
            10: Decimal('100.0000'),
            11: Decimal('40.0000'),
            12: Decimal('15.0000')
        })


class GetMaximumDailyBudgetTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_get_max_daily_budget(self):
        c = dash.models.Campaign.objects.get(id=1)
        date = datetime.date(2016, 3, 1)

        self.assertEqual(campaign_stop._get_max_daily_budget_per_ags(date, c), {
            1: Decimal('55'),
            2: Decimal('30'),
            3: 0,
            4: Decimal('20'),
            5: Decimal('100'),
            6: Decimal('80'),
            7: 0,
        })

    def test_campaign_in_landing(self):
        c = dash.models.Campaign.objects.get(id=6)  # campaign in landing
        date = datetime.date(2016, 4, 6)

        self.assertEqual(campaign_stop._get_max_daily_budget_per_ags(date, c), {
            8: Decimal('50'),
            9: 0,
            10: Decimal('45'),
            11: 0,
            12: 0,
            13: 0,
        })  # only newly set budgets (end date set after budgets are set)

        date = datetime.date(2016, 4, 7)
        self.assertEqual(campaign_stop._get_max_daily_budget_per_ags(date, c), {
            8: 0,
            9: 0,
            10: 0,
            11: 0,
            12: 0,
            13: 0,
        })  # end date not moved yet

        # move end date
        with test_helper.disable_auto_now_add(dash.models.AdGroupSettings, 'created_dt'):
            for ag in c.adgroup_set.all().filter_active():
                new_settings = ag.get_current_settings().copy_settings()
                new_settings.end_date = date
                new_settings.created_dt = datetime.datetime(2016, 4, 7, 12)
                new_settings.save(None)

        self.assertEqual(campaign_stop._get_max_daily_budget_per_ags(date, c), {
            8: Decimal('50'),
            9: 0,
            10: Decimal('45'),
            11: 0,
            12: 0,
            13: 0,
        })

    def test_campaign_in_landing_paused(self):
        c = dash.models.Campaign.objects.get(id=6)  # campaign in landing
        date = datetime.date(2016, 4, 7)  # end date has not yet been set

        self.assertEqual(campaign_stop._get_max_daily_budget_per_ags(date, c), {
            8: 0,
            9: 0,
            10: 0,
            11: 0,
            12: 0,
            13: 0,
        })

    def test_get_running_ad_groups_on_date(self):
        c1 = dash.models.Campaign.objects.get(id=1)  # ad group started on date
        c2 = dash.models.Campaign.objects.get(id=2)  # ad group stopped date before
        c3 = dash.models.Campaign.objects.get(id=3)  # active ad group from day before, stopped mid-day
        c4 = dash.models.Campaign.objects.get(id=4)  # active ad group but end date past
        c5 = dash.models.Campaign.objects.get(id=5)  # switched to landing mode one day before (end dt on midnight)

        date = datetime.date(2016, 3, 1)
        self.assertEqual(
            campaign_stop._get_ad_groups_running_on_date(
                date, c1.adgroup_set.all()), set(c1.adgroup_set.all().exclude(id=3)))
        self.assertEqual(
            campaign_stop._get_ad_groups_running_on_date(date, c2.adgroup_set.all()), set())
        self.assertEqual(
            campaign_stop._get_ad_groups_running_on_date(date, c3.adgroup_set.all()), set(c3.adgroup_set.all()))
        self.assertEqual(
            campaign_stop._get_ad_groups_running_on_date(date, c4.adgroup_set.all()), set())
        self.assertEqual(
            campaign_stop._get_ad_groups_running_on_date(date, c5.adgroup_set.all()), set(c5.adgroup_set.all()))

    def test_get_source_max_daily_budget(self):
        ag_settings = dash.models.AdGroupSettings.objects.all().order_by('created_dt')
        ags_settings = dash.models.AdGroupSourceSettings.objects.all().order_by('created_dt')
        ags1 = dash.models.AdGroupSource.objects.get(id=1)  # highest daily budget set on date
        ags2 = dash.models.AdGroupSource.objects.get(id=2)  # highest daily budget from day before
        ags3 = dash.models.AdGroupSource.objects.get(id=3)  # inactive since day before
        ags4 = dash.models.AdGroupSource.objects.get(id=4)  # UTC-9
        ags5 = dash.models.AdGroupSource.objects.get(id=5)  # UTC+9

        date = datetime.date(2016, 3, 1)
        self.assertEqual(
            Decimal('55'),
            campaign_stop._get_source_max_daily_budget(
                date,
                ags1,
                campaign_stop._get_ag_settings_dict(date, [ags1.ad_group])[ags1.ad_group_id],
                campaign_stop._get_sources_settings_dict(date, [ags1])[ags1.id])
        )
        self.assertEqual(
            Decimal('30'),
            campaign_stop._get_source_max_daily_budget(
                date,
                ags2,
                campaign_stop._get_ag_settings_dict(date, [ags2.ad_group])[ags2.ad_group_id],
                campaign_stop._get_sources_settings_dict(date, [ags2])[ags2.id])
        )
        self.assertEqual(
            Decimal('0'),
            campaign_stop._get_source_max_daily_budget(
                date,
                ags3,
                campaign_stop._get_ag_settings_dict(date, [ags3.ad_group])[ags3.ad_group_id],
                campaign_stop._get_sources_settings_dict(date, [ags3])[ags3.id])
        )
        self.assertEqual(
            Decimal('20'),
            campaign_stop._get_source_max_daily_budget(
                date,
                ags4,
                campaign_stop._get_ag_settings_dict(date, [ags4.ad_group])[ags4.ad_group_id],
                campaign_stop._get_sources_settings_dict(date, [ags4])[ags4.id])
        )
        self.assertEqual(
            Decimal('100'),
            campaign_stop._get_source_max_daily_budget(
                date,
                ags5,
                campaign_stop._get_ag_settings_dict(date, [ags5.ad_group])[ags5.ad_group_id],
                campaign_stop._get_sources_settings_dict(date, [ags5])[ags5.id])
        )


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

    def test_existing_end_dates_in_the_past(self):
        campaign = dash.models.Campaign.objects.get(id=1)

        yesterday = dates_helper.local_today() - datetime.timedelta(days=1)

        active_before = list(campaign.adgroup_set.all().filter_active())
        self.assertTrue(active_before)
        for ad_group in active_before:
            new_ag_settings = ad_group.get_current_settings().copy_settings()
            new_ag_settings.end_date = yesterday
            new_ag_settings.save(None)

        campaign_stop._switch_campaign_to_landing_mode(campaign)
        self.assertFalse(campaign.adgroup_set.all().filter_active().exists())
        for ad_group in campaign.adgroup_set.all():
            current_settings = ad_group.get_current_settings()
            if ad_group in active_before:
                self.assertTrue(current_settings.landing_mode)
                self.assertEqual(current_settings.end_date, yesterday)
                self.assertEqual(current_settings.state, dash.constants.AdGroupSettingsState.INACTIVE)
            else:
                self.assertFalse(current_settings.landing_mode)


class SetAdGroupEndDateTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('actionlog.zwei_actions.send')
    def test_set_ad_group_end_date(self, mock_zwei_send):
        ad_group = dash.models.AdGroup.objects.get(id=1)

        current_settings = ad_group.get_current_settings()
        self.assertEqual(None, current_settings.end_date)

        today = dates_helper.utc_today()
        campaign_stop._set_ad_group_end_date(ad_group, today)

        new_settings = ad_group.get_current_settings()
        self.assertEqual(today, new_settings.end_date)

        self.assertFalse(mock_zwei_send.called)


class StopNonSpendingSourcesTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def setUp(self):
        patcher = patch('dash.api.k1_helper')
        self.k1_helper_mock = patcher.start()
        self.addCleanup(patcher.stop)

    @patch('utils.dates_helper.local_today')
    @patch('reports.api_contentads.query')
    def test_stop_non_spending_sources(self, mock_get_yesterday_spends, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        campaign = dash.models.Campaign.objects.get(id=1)
        ad_groups = campaign.adgroup_set.all().filter_active()
        non_spending_ags_ids = [1, 2]

        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        self.assertItemsEqual([ag1, ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [1, 2, 4, 5], ag1.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))

        mock_get_yesterday_spends.return_value = []
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups):
            row = {'ad_group': ags.ad_group_id, 'source': ags.source_id, 'cost': Decimal(100), 'data_cost': Decimal(0)}
            if ags.id in non_spending_ags_ids:
                row['cost'] = Decimal('0.5')
            mock_get_yesterday_spends.return_value.append(row)

        current_ags_settings = {
            ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group__campaign=campaign,
            ).group_current_settings()
        }

        for ags_id in non_spending_ags_ids:
            self.assertTrue(current_ags_settings[ags_id].state == dash.constants.AdGroupSourceSettingsState.ACTIVE)

        campaign_stop._stop_non_spending_sources(campaign)
        self.assertItemsEqual([ag1, ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [4, 5], ag1.adgroupsource_set.all().filter_active().values_list('id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))

    @patch('utils.dates_helper.local_today')
    @patch('reports.api_contentads.query')
    def test_stop_whole_ad_group(self, mock_get_yesterday_spends, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 3, 15)
        campaign = dash.models.Campaign.objects.get(id=1)
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)
        ad_groups = campaign.adgroup_set.all().filter_active()
        non_spending_ag_ids = [1]

        mock_get_yesterday_spends.return_value = []
        for ags in dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups):
            row = {'ad_group': ags.ad_group_id, 'source': ags.source_id, 'cost': Decimal(100), 'data_cost': Decimal(0)}
            if ags.ad_group_id in non_spending_ag_ids:
                row['cost'] = Decimal('0.5')
            mock_get_yesterday_spends.return_value.append(row)

        campaign_stop._stop_non_spending_sources(campaign)
        self.assertItemsEqual([2], campaign.adgroup_set.all().filter_active().values_list('id', flat=True))
        self.assertItemsEqual(
            [1, 2, 4, 5], ag1.adgroupsource_set.all().filter_active().values_list('id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))


class CalculateDailySpendsTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.dates_helper.local_today')
    def test_calculate_daily_caps(self, mock_local_today):
        today = datetime.date(2016, 4, 5)
        mock_local_today.return_value = today
        campaign = dash.models.Campaign.objects.get(id=1)

        active_ad_groups = campaign.adgroup_set.all().filter_active()
        for ad_group in active_ad_groups:
            # ad groups are stopped at the time of running the calculations
            new_settings = ad_group.get_current_settings().copy_settings()
            new_settings.end_date = datetime.date(2016, 4, 4)
            new_settings.save(None)

        max_daily_budget = campaign_stop._get_max_daily_budget(today, campaign)
        remaining_today, _, _ = campaign_stop._get_minimum_remaining_budget(campaign, max_daily_budget)
        self.assertEqual(Decimal(635), remaining_today)

        active_ad_groups = campaign.adgroup_set.all().filter_active()
        self.assertEqual(2, active_ad_groups.count())

        per_date_spend = {
            (1, datetime.date(2016, 4, 4)): Decimal('100'),
            (2, datetime.date(2016, 4, 4)): Decimal('100'),
        }

        daily_caps = campaign_stop._calculate_daily_caps(campaign, per_date_spend)

        self.assertEqual(318, daily_caps[1])
        self.assertEqual(318, daily_caps[2])

    @patch('utils.dates_helper.local_today')
    def test_calculate_daily_caps_ad_group_inactive(self, mock_local_today):
        today = datetime.date(2016, 4, 5)
        mock_local_today.return_value = today
        campaign = dash.models.Campaign.objects.get(id=1)

        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        new_settings = ag1.get_current_settings().copy_settings()
        new_settings.end_date = datetime.date(2016, 4, 4)
        new_settings.save(None)

        new_settings = ag2.get_current_settings().copy_settings()
        new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
        new_settings.save(None)

        max_daily_budget = campaign_stop._get_max_daily_budget(today, campaign)
        remaining_today, _, _ = campaign_stop._get_minimum_remaining_budget(campaign, max_daily_budget)
        self.assertEqual(Decimal(635), remaining_today)

        active_ad_groups = campaign.adgroup_set.all().filter_active()
        self.assertEqual(1, active_ad_groups.count())

        per_date_spend = {
            (1, datetime.date(2016, 4, 4)): Decimal('100'),
            (2, datetime.date(2016, 4, 4)): Decimal('100'),
        }

        daily_caps = campaign_stop._calculate_daily_caps(campaign, per_date_spend)
        self.assertEqual(635, daily_caps[1])


class UpdateAdGroupSettingsTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_ad_group_settings_values(self):
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        ag1_settings = ag1.get_current_settings()
        self.assertEqual(ag1_settings.autopilot_state,
                         dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.assertEqual(ag1_settings.autopilot_daily_budget, Decimal('0.0000'))

        ag2_settings = ag2.get_current_settings()
        self.assertEqual(ag2_settings.autopilot_state,
                         dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.assertEqual(ag2_settings.autopilot_daily_budget, Decimal('0.0000'))

        daily_caps = {
            1: 12,
            2: 15,
        }
        campaign_stop._persist_new_autopilot_settings(daily_caps)

        ag1_settings = ag1.get_current_settings()
        self.assertEqual(ag1_settings.autopilot_state,
                         dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        self.assertEqual(ag1_settings.autopilot_daily_budget, Decimal('12'))

        ag2_settings = ag2.get_current_settings()
        self.assertEqual(ag2_settings.autopilot_state,
                         dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        self.assertEqual(ag2_settings.autopilot_daily_budget, Decimal('15'))

    @patch('automation.campaign_stop._wrap_up_landing')
    @patch('automation.campaign_stop._stop_non_spending_sources')
    @patch('automation.campaign_stop._wrap_up_landing')
    @patch('automation.campaign_stop._run_autopilot')
    @patch('automation.campaign_stop._set_end_date_to_today')
    @patch('automation.campaign_stop._prepare_for_autopilot')
    @patch('automation.campaign_stop._get_past_7_days_data')
    @patch('automation.campaign_stop._calculate_daily_caps')
    @patch('automation.campaign_stop._persist_new_autopilot_settings')
    def test_update_ad_group_settings_called(self, mock_update_ags, mock_calc_caps,
                                             mock_past7, mock_prepare_ap, *mocks):
        caps = {
            1: 12,
            2: 15,
        }
        mock_past7.return_value = None, None
        mock_prepare_ap.return_value = [], None
        mock_calc_caps.return_value = caps
        campaign = dash.models.Campaign.objects.get(pk=1)
        campaign_stop._update_landing_campaign(campaign)
        self.assertTrue(mock_update_ags.called)
        mock_update_ags.assert_called_once_with(caps)


class PrepareActiveSourceForAutopilotTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def setUp(self):
        patcher = patch('dash.api.k1_helper')
        self.k1_helper_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_stop_ad_group_source(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        self.assertItemsEqual([ag1, ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [1, 2, 4, 5], ag1.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))

        per_source_spend = {
            (1, 1): Decimal('100'),
            (1, 2): Decimal('80'),
            (1, 4): Decimal('50'),
            (1, 5): Decimal('30'),
            (2, 1): Decimal('100'),
        }

        daily_caps = {
            1: 12,
            2: 12
        }

        campaign_stop._prepare_for_autopilot(campaign, daily_caps, per_source_spend)
        self.assertItemsEqual([ag1, ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [1, 2], ag1.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))

    def test_stop_whole_ad_group(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        self.assertItemsEqual([ag1, ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [1, 2, 4, 5], ag1.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))

        per_source_spend = {
            (1, 1): Decimal('100'),
            (1, 2): Decimal('80'),
            (1, 4): Decimal('50'),
            (1, 5): Decimal('30'),
            (2, 1): Decimal('100'),
        }

        daily_caps = {
            1: 4,
            2: 12
        }

        campaign_stop._prepare_for_autopilot(campaign, daily_caps, per_source_spend)
        self.assertItemsEqual([ag2], campaign.adgroup_set.all().filter_active())
        self.assertItemsEqual(
            [1, 2, 4, 5], ag1.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))
        self.assertItemsEqual([1], ag2.adgroupsource_set.all().filter_active().values_list('source_id', flat=True))


class RunAutopilotTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('automation.autopilot_plus.prefetch_autopilot_data')
    @patch('automation.autopilot_budgets.get_autopilot_daily_budget_recommendations')
    @patch('automation.autopilot_cpc.get_autopilot_cpc_recommendations')
    @patch('automation.autopilot_plus.set_autopilot_changes')
    def test_run_autopilot(self, mock_set_changes, mock_ap_cpc, mock_ap_budget, mock_ap_prefetch):
        campaign = dash.models.Campaign.objects.get(id=1)
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        daily_caps = {
            1: 100,
            2: 200,
        }

        mock_ap_prefetch.return_value = ({
            ag1: 'Mock ad group 1 prefetch data',
            ag2: 'Mock ad group 2 prefetch data',
        }, {
            campaign: 'Mock campaign goal'
        })

        ag1_budget_changes = {
            dash.models.AdGroupSource.objects.get(id=1): {'new_budget': Decimal('1'), 'old_budget': Decimal('2')},
            dash.models.AdGroupSource.objects.get(id=2): {'new_budget': Decimal('1'), 'old_budget': Decimal('2')},
            dash.models.AdGroupSource.objects.get(id=4): {'new_budget': Decimal('1'), 'old_budget': Decimal('2')},
            dash.models.AdGroupSource.objects.get(id=5): {'new_budget': Decimal('1'), 'old_budget': Decimal('2')},
        }
        ag2_budget_changes = {
            dash.models.AdGroupSource.objects.get(id=5): {'new_budget': Decimal('5'), 'old_budget': Decimal('10')},
        }

        def _budget_ap_return(ad_group, daily_cap, data, campaign_goal):
            ret = {
                1: ag1_budget_changes,
                2: ag2_budget_changes,
            }
            return ret[ad_group.id]
        mock_ap_budget.side_effect = _budget_ap_return

        ag1_cpc_changes = {
            dash.models.AdGroupSource.objects.get(id=1): {'new_cpc_cc': Decimal('0.15'), 'old_cpc_cc': Decimal('0.1')},
            dash.models.AdGroupSource.objects.get(id=2): {'new_cpc_cc': Decimal('0.15'), 'old_cpc_cc': Decimal('0.1')},
            dash.models.AdGroupSource.objects.get(id=4): {'new_cpc_cc': Decimal('0.15'), 'old_cpc_cc': Decimal('0.1')},
            dash.models.AdGroupSource.objects.get(id=5): {'new_cpc_cc': Decimal('0.15'), 'old_cpc_cc': Decimal('0.1')},
        }
        ag2_cpc_changes = {
            dash.models.AdGroupSource.objects.get(id=6): {'new_cpc_cc': Decimal('0.20'), 'old_cpc_cc': Decimal('0.05')},
        }

        def _cpc_ap_return(ad_group, data, budget_changes):
            ret = {
                1: ag1_cpc_changes,
                2: ag2_cpc_changes,
            }
            return ret[ad_group.id]
        mock_ap_cpc.side_effect = _cpc_ap_return

        campaign_stop._run_autopilot(campaign, daily_caps)

        budget_ap_calls = [
            call(ag1, 100, 'Mock ad group 1 prefetch data', campaign_goal=None),
            call(ag2, 200, 'Mock ad group 2 prefetch data', campaign_goal=None),
        ]
        mock_ap_budget.assert_has_calls(budget_ap_calls, any_order=True)

        cpc_ap_calls = [
            call(ag1, 'Mock ad group 1 prefetch data', ag1_budget_changes),
            call(ag2, 'Mock ad group 2 prefetch data', ag2_budget_changes),
        ]
        mock_ap_cpc.assert_has_calls(cpc_ap_calls, any_order=True)

        set_changes_calls = [
            call(budget_changes=ag1_budget_changes,
                 cpc_changes=ag1_cpc_changes,
                 system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
                 landing_mode=True),
            call(budget_changes=ag2_budget_changes,
                 cpc_changes=ag2_cpc_changes,
                 system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
                 landing_mode=True),
        ]
        mock_set_changes.assert_has_calls(set_changes_calls, any_order=True)

    @patch('automation.autopilot_plus.prefetch_autopilot_data')
    @patch('automation.autopilot_budgets.get_autopilot_daily_budget_recommendations')
    @patch('automation.autopilot_cpc.get_autopilot_cpc_recommendations')
    @patch('automation.autopilot_plus.set_autopilot_changes')
    def test_autopilot_data_not_available(self, mock_set_changes, mock_ap_cpc, mock_ap_budget, mock_ap_prefetch):
        campaign = dash.models.Campaign.objects.get(id=1)
        ag1 = dash.models.AdGroup.objects.get(id=1)
        ag2 = dash.models.AdGroup.objects.get(id=2)

        daily_caps = {
            1: 100,
            2: 200,
        }

        self.assertEqual(dash.constants.AdGroupSettingsState.ACTIVE, ag1.get_current_settings().state)
        self.assertEqual(dash.constants.AdGroupSettingsState.ACTIVE, ag2.get_current_settings().state)

        mock_ap_prefetch.return_value = ({}, {
            campaign: 'Mock campaign goal'
        })

        campaign_stop._run_autopilot(campaign, daily_caps)
        self.assertFalse(mock_ap_cpc.called)
        self.assertFalse(mock_ap_budget.called)

        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ag1.get_current_settings().state)
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ag2.get_current_settings().state)


class UpdateCampaignsInLandingTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.dates_helper.local_today')
    @patch('automation.campaign_stop._can_resume_campaign')
    @patch('automation.campaign_stop._run_autopilot')
    @patch('automation.campaign_stop._get_yesterday_source_spends')
    @patch('automation.campaign_stop._get_past_7_days_data')
    @patch('dash.api.order_ad_group_settings_update')
    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_update_campaigns_in_landing(self, mock_k1_ping, mock_zwei_send,
                                         mock_order_ad_group_update, mock_get_past_data,
                                         mock_get_yesterday_spends, mock_run_ap,
                                         mock_can_resume, mock_local_today):
        today = datetime.date(2016, 4, 5)

        yesterday = today - datetime.timedelta(days=1)
        mock_local_today.return_value = today

        mock_can_resume.return_value = False

        campaign = dash.models.Campaign.objects.get(id=1)
        campaign_stop._switch_campaign_to_landing_mode(campaign)

        mock_order_ad_group_update.reset_mock()
        mock_order_ad_group_update.return_value = []

        mock_run_ap.return_value = []

        ret = {}
        for ad_group in campaign.adgroup_set.all():
            for ags in ad_group.adgroupsource_set.all():
                ret[(ags.ad_group_id, ags.source_id)] = Decimal('100')
        mock_get_yesterday_spends.return_value = ret

        date_spend, source_spend = {}, {}
        for ad_group in campaign.adgroup_set.all():
            for ags in ad_group.adgroupsource_set.all():
                date_spend[(ags.ad_group_id, yesterday)] = Decimal('100')
                source_spend[(ags.ad_group_id, ags.source_id)] = Decimal('100')
        mock_get_past_data.return_value = (date_spend, source_spend)

        self.assertTrue(campaign.is_in_landing())
        campaign_stop.update_campaigns_in_landing(dash.models.Campaign.objects.all().filter_landing())
        self.assertEqual(mock_k1_ping.call_count, 6)

        for ad_group in campaign.adgroup_set.all().filter_active():
            current_settings = ad_group.get_current_settings()
            self.assertEqual(today, current_settings.end_date)

    @patch('utils.dates_helper.local_today')
    def test_check_ad_groups_end_date(self, mock_today):
        today = datetime.date(2016, 4, 5)
        mock_today.return_value = today

        campaign = dash.models.Campaign.objects.get(id=1)
        for ad_group in campaign.adgroup_set.all().filter_active():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = today - datetime.timedelta(1)
            new_settings.landing_mode = False
            new_settings.save(None)

        campaign_stop._check_ad_groups_end_date(campaign)
        self.assertFalse(campaign.adgroup_set.all().filter_active().count())

    @patch('utils.dates_helper.local_today')
    def test_check_ad_groups_end_date_today(self, mock_today):
        today = datetime.date(2016, 4, 5)
        mock_today.return_value = today

        campaign = dash.models.Campaign.objects.get(id=1)
        for ad_group in campaign.adgroup_set.all().filter_active():
            current_settings = ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.end_date = today
            new_settings.landing_mode = False
            new_settings.save(None)

        actions = campaign_stop._check_ad_groups_end_date(campaign)
        self.assertEqual(len(actions), 0)
        self.assertEqual(2, campaign.adgroup_set.all().filter_active().count())

    @patch('utils.dates_helper.local_today')
    @patch('automation.campaign_stop._can_resume_campaign')
    @patch('automation.campaign_stop._get_yesterday_source_spends')
    @patch('automation.campaign_stop._get_past_7_days_data')
    @patch('automation.campaign_stop._check_ad_groups_end_date')
    @patch('dash.api.order_ad_group_settings_update')
    @patch('actionlog.zwei_actions.send')
    def test_wrap_up_landing_mode(self, mock_zwei_send, mock_order_ad_group_update,
                                  mock_get_end_date, mock_get_past_data,
                                  mock_get_yesterday_spends, mock_can_resume, mock_local_today):
        today = datetime.date(2016, 4, 5)

        yesterday = today - datetime.timedelta(days=1)
        mock_local_today.return_value = today

        mock_can_resume.return_value = False

        campaign = dash.models.Campaign.objects.get(id=1)
        campaign_stop._switch_campaign_to_landing_mode(campaign)

        mock_order_ad_group_update.reset_mock()
        mock_order_ad_group_update.return_value = []

        ret = {}
        for ad_group in campaign.adgroup_set.all():
            for ags in ad_group.adgroupsource_set.all():
                ret[(ags.ad_group_id, ags.source_id)] = Decimal('100')
        mock_get_yesterday_spends.return_value = ret

        date_spend, source_spend = {}, {}
        for ad_group in campaign.adgroup_set.all():
            for ags in ad_group.adgroupsource_set.all():
                # all ad groups without spend
                date_spend[(ags.ad_group_id, yesterday)] = Decimal('0')
                source_spend[(ags.ad_group_id, ags.source_id)] = Decimal('0')
        mock_get_past_data.return_value = (date_spend, source_spend)

        mock_get_end_date.reset_mock()
        mock_get_end_date.return_value = []

        self.assertTrue(campaign.is_in_landing())

        campaign_stop.update_campaigns_in_landing(dash.models.Campaign.objects.all().filter_landing())
        self.assertTrue(mock_get_end_date.called)

        self.assertFalse(campaign.get_current_settings().landing_mode)
        for ad_group in campaign.adgroup_set.all():
            self.assertFalse(ad_group.get_current_settings().landing_mode)
            for ad_group_source in ad_group.adgroupsource_set.all():
                self.assertFalse(ad_group_source.get_current_settings().landing_mode)


class MinimumBudgetAmountTestCase(TestCase):
    fixtures = ['test_campaign_stop.yaml']

    @patch('utils.dates_helper.local_today')
    @patch('utils.dates_helper.utc_now')
    def test_is_current_time_valid_for_amount_editing(self, mock_utc_now, mock_local_today):
        campaign = dash.models.Campaign.objects.get(id=1)

        today = datetime.datetime(2016, 4, 5, 10, 10, 10)
        mock_utc_now.return_value = today
        mock_local_today.return_value = dates_helper.utc_datetime_to_local_date(today)
        self.assertFalse(
            campaign_stop.is_current_time_valid_for_amount_editing(campaign)
        )

        today = datetime.datetime(2016, 4, 5, 12, 10, 10)
        mock_utc_now.return_value = today
        mock_local_today.return_value = dates_helper.utc_datetime_to_local_date(today)
        self.assertTrue(
            campaign_stop.is_current_time_valid_for_amount_editing(campaign)
        )

        today = datetime.datetime(2016, 4, 5, 23, 10, 10)
        mock_utc_now.return_value = today
        mock_local_today.return_value = dates_helper.utc_datetime_to_local_date(today)
        self.assertTrue(
            campaign_stop.is_current_time_valid_for_amount_editing(campaign)
        )

        today = datetime.datetime(2016, 4, 5, 8, 10, 10)
        mock_utc_now.return_value = today
        mock_local_today.return_value = dates_helper.utc_datetime_to_local_date(today)
        self.assertFalse(
            campaign_stop.is_current_time_valid_for_amount_editing(campaign)
        )

        today = datetime.datetime(2016, 4, 5, 11, 10, 10)
        mock_utc_now.return_value = today
        mock_local_today.return_value = dates_helper.utc_datetime_to_local_date(today)
        self.assertFalse(
            campaign_stop.is_current_time_valid_for_amount_editing(campaign)
        )

    @patch('utils.dates_helper.local_today')
    def test_get_minimum_budget_amount(self, mock_local_today):
        mock_local_today.return_value = datetime.date(2016, 4, 5)

        budget = dash.models.BudgetLineItem.objects.get(pk=1)
        self.assertEqual(
            campaign_stop.get_minimum_budget_amount(budget),
            None  # not active
        )

        budget = dash.models.BudgetLineItem.objects.get(pk=6)
        campaign_settings = budget.campaign.get_current_settings().copy_settings()
        campaign_settings.automatic_campaign_stop = False
        campaign_settings.save(None)

        self.assertEqual(
            campaign_stop.get_minimum_budget_amount(budget),
            None,  # automatic campaign stop not enabled
        )

        campaign_settings = budget.campaign.get_current_settings().copy_settings()
        campaign_settings.automatic_campaign_stop = True
        campaign_settings.save(None)

        self.assertEqual(
            campaign_stop.get_minimum_budget_amount(budget),
            Decimal('294.4444444444444444444444444')  # max daily budgets without spend
        )

        reports.models.BudgetDailyStatement.objects.create(
            date=datetime.date(2016, 4, 4),
            media_spend_nano=225000000000,
            license_fee_nano=22500000000,
            data_spend_nano=0,
            budget=budget,
            margin_nano=0,
        )

        self.assertEqual(
            campaign_stop.get_minimum_budget_amount(budget),
            Decimal('541.9444444444444444444444444')  # max daily budgets without spend
        )

        reports.models.BudgetDailyStatement.objects.create(
            date=datetime.date(2016, 4, 5),
            media_spend_nano=125000000000,
            license_fee_nano=12500000000,
            data_spend_nano=0,
            budget=budget,
            margin_nano=0,
        )

        self.assertEqual(
            campaign_stop.get_minimum_budget_amount(budget),
            Decimal('679.4444444444444444444444444')  # max daily budgets without spend
        )


class GetMatchingPairsTestCase(TestCase):

    fixtures = ['test_campaign_stop.yaml']

    def test_many_ad_group_settings(self):
        from django.http.request import HttpRequest
        from zemauth.models import User
        r = HttpRequest()
        r.user = User.objects.get(id=1)

        acc = dash.models.Account()
        acc.save(r)

        c = dash.models.Campaign()
        c.account = acc
        c.save(r)

        ag = dash.models.AdGroup()
        ag.campaign = c
        ag.save(r)
        ags = dash.models.AdGroupSource.objects.create(ad_group=ag, source=dash.models.Source.objects.get(id=1))

        n_ags = ags.get_current_settings().copy_settings()
        n_ags.state = 2
        n_ags.daily_budget_cc = Decimal('20')
        n_ags.save(None)

        for i in range(100):
            n = ag.get_current_settings().copy_settings()
            n.state = 2
            n.changes_text = str(i)
            n.save(None)

        n_ags = ags.get_current_settings().copy_settings()
        n_ags.state = 1
        n_ags.save(None)

        n = ag.get_current_settings().copy_settings()
        n.state = 1
        n.changes_text = str(i)
        n.save(None)

        self.assertEqual(Decimal('20'), campaign_stop._get_max_daily_budget(dates_helper.local_today(), ag.campaign))
