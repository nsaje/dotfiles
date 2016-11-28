import datetime
from mock import patch, call, MagicMock

from django.test import TestCase
from django.contrib.auth.models import Permission

import dash.constants
from integrations.bizwire import config, models
from integrations.bizwire.internal import actions, helpers

from utils.test_helper import ListMatcher
from zemauth.models import User


class StopAdsTestCase(TestCase):

    @patch('utils.dates_helper.utc_now')
    @patch('dash.api.update_content_ads_state')
    def test_check_midnight_and_stop_ads_pst_time(self, mock_update_content_ads_state, mock_utc_now):
        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 6)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 8)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 7)
        actions.check_midnight_and_stop_ads()
        self.assertEqual(
            call(ListMatcher([]), dash.constants.ContentAdSourceState.INACTIVE, None),
            mock_update_content_ads_state.call_args)

    @patch('utils.dates_helper.utc_now')
    @patch('dash.api.update_content_ads_state')
    def test_check_midnight_and_stop_ads_pdt_time(self, mock_update_content_ads_state, mock_utc_now):
        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 7)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 9)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 8)
        actions.check_midnight_and_stop_ads()
        self.assertEqual(
            call(ListMatcher([]), dash.constants.ContentAdSourceState.INACTIVE, None),
            mock_update_content_ads_state.call_args)


@patch('integrations.bizwire.config.AUTOMATION_CAMPAIGN', 1)
@patch('integrations.bizwire.config.AUTOMATION_USER_EMAIL', 'user@test.com')
@patch('utils.redirector_helper.insert_adgroup', MagicMock())
class RotateAdGroupsTestCase(TestCase):

    fixtures = ['test_bizwire.yaml']

    def setUp(self):
        permissions = ['can_use_restapi', 'settings_view', 'can_control_ad_group_state_in_table',
                       'add_media_sources_automatically']
        u = User.objects.get(email='user@test.com')
        for permission in permissions:
            u.user_permissions.add(Permission.objects.get(codename=permission))
        u.save()

        # make sure budgets exist
        self.utc_now_patcher = patch('utils.dates_helper.utc_now')
        mock_utc_now = self.utc_now_patcher.start()
        mock_utc_now.return_value = datetime.datetime(2016, 11, 2)

    def tearDown(self):
        self.utc_now_patcher.stop()

    @patch('integrations.bizwire.config.INTEREST_TARGETING_GROUPS', [])
    def test_rotate_ad_groups(self):
        start_date = helpers.get_pacific_now().date() + datetime.timedelta(days=1)
        ad_groups_before = list(dash.models.AdGroup.objects.all())

        actions._rotate_ad_groups(start_date)
        ad_groups_after = list(dash.models.AdGroup.objects.all())

        ad_groups_added = [ag for ag in ad_groups_after if not any(agb.id == ag.id for agb in ad_groups_before)]
        self.assertEqual(1, len(ad_groups_added))

        ad_group = ad_groups_added[0]
        ad_group_settings = ad_group.get_current_settings()

        self.assertEqual(ad_group.name, config.AD_GROUP_NAME_TEMPLATE.format(
            start_date=start_date,
            interest_targeting_str=actions.DEFAULT_TARGETING_STR)
        )
        self.assertEqual(config.AUTOMATION_CAMPAIGN, ad_group.campaign_id)
        self.assertEqual(dash.constants.AdGroupRunningStatus.ACTIVE, ad_group_settings.state)
        self.assertEqual(start_date, ad_group_settings.start_date)
        self.assertEqual(
            set(config.INTEREST_TARGETING_OPTIONS),
            set(ad_group_settings.interest_targeting)
        )
        self.assertEqual(
            set([dash.constants.AdTargetDevice.DESKTOP,
                 dash.constants.AdTargetDevice.MOBILE,
                 dash.constants.AdTargetDevice.TABLET]),
            set(ad_group_settings.target_devices)
        )
        self.assertEqual(['US'], ad_group_settings.target_regions)

        self.assertEqual(ad_group.campaign.account.allowed_sources.count(), ad_group.adgroupsource_set.all().count())
        for ad_group_source in ad_group.adgroupsource_set.all():
            ad_group_source_settings = ad_group_source.get_current_settings()
            self.assertEqual(dash.constants.AdGroupSourceSettingsState.ACTIVE, ad_group_source_settings.state)
            self.assertEqual(config.DEFAULT_CPC, ad_group_source_settings.cpc_cc)
            self.assertEqual(config.DEFAULT_DAILY_BUDGET, ad_group_source_settings.daily_budget_cc)

    @patch('integrations.bizwire.config.INTEREST_TARGETING_GROUPS', [
        (dash.constants.InterestCategory.ENTERTAINMENT, dash.constants.InterestCategory.FUN),
        (dash.constants.InterestCategory.POLITICS, dash.constants.InterestCategory.FASHION,
         dash.constants.InterestCategory.FINANCE),
        (dash.constants.InterestCategory.HEALTH,),
    ])
    def test_interest_targeting_groups(self):
        start_date = helpers.get_pacific_now().date() + datetime.timedelta(days=1)
        ad_groups_before = list(dash.models.AdGroup.objects.all())

        actions._rotate_ad_groups(start_date)
        ad_groups_after = list(dash.models.AdGroup.objects.all())

        ad_groups_added = [ag for ag in ad_groups_after if not any(agb.id == ag.id for agb in ad_groups_before)]
        self.assertEqual(4, len(ad_groups_added))

        actual_targetings = []
        for ad_group in ad_groups_added:
            ad_group_settings = ad_group.get_current_settings()
            targeting = models.AdGroupTargeting.objects.get(start_date=start_date, ad_group_id=ad_group.id)
            if targeting.interest_targeting != []:
                self.assertEqual(set(targeting.interest_targeting), set(ad_group_settings.interest_targeting))
            actual_targetings.append(set(ad_group_settings.interest_targeting))

        expected_targetings = [
            set(config.INTEREST_TARGETING_OPTIONS),
            set([dash.constants.InterestCategory.ENTERTAINMENT, dash.constants.InterestCategory.FUN]),
            set([dash.constants.InterestCategory.POLITICS, dash.constants.InterestCategory.FASHION,
                 dash.constants.InterestCategory.FINANCE]),
            set([dash.constants.InterestCategory.HEALTH]),
        ]
        self.assertEqual(expected_targetings, actual_targetings)
