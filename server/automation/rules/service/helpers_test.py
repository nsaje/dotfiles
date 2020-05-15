import contextlib
import datetime

import mock
from django.test import TestCase

import core.models
import core.models.settings
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import models
from . import helpers


class RulesMapTest(TestCase):
    def setUp(self):
        ad_groups_archived = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=True)
        self.ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in self.ad_groups + ad_groups_archived:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.ad_groups_inactive = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in self.ad_groups_inactive:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        self.rule_1 = magic_mixer.blend(
            models.Rule, ad_groups_included=self.ad_groups[:3] + self.ad_groups_inactive[:3] + ad_groups_archived[:3]
        )
        self.rule_2 = magic_mixer.blend(
            models.Rule, ad_groups_included=self.ad_groups[3:5] + self.ad_groups_inactive[3:5] + ad_groups_archived[3:5]
        )
        self.rule_3 = magic_mixer.blend(
            models.Rule, ad_groups_included=self.ad_groups[1:4] + self.ad_groups_inactive[1:4] + ad_groups_archived[1:4]
        )

    def test_filter_active_disabled(self):
        rules_map = helpers.get_rules_by_ad_group_map(
            [self.rule_1, self.rule_2, self.rule_3], filter_active=False, exclude_inactive_yesterday=False
        )
        self.assertEqual(
            {
                self.ad_groups[0]: [self.rule_1],
                self.ad_groups[1]: [self.rule_1, self.rule_3],
                self.ad_groups[2]: [self.rule_1, self.rule_3],
                self.ad_groups[3]: [self.rule_2, self.rule_3],
                self.ad_groups[4]: [self.rule_2],
                self.ad_groups_inactive[0]: [self.rule_1],
                self.ad_groups_inactive[1]: [self.rule_1, self.rule_3],
                self.ad_groups_inactive[2]: [self.rule_1, self.rule_3],
                self.ad_groups_inactive[3]: [self.rule_2, self.rule_3],
                self.ad_groups_inactive[4]: [self.rule_2],
            },
            rules_map,
        )

    def test_filter_active(self):
        rules_map = helpers.get_rules_by_ad_group_map(
            [self.rule_1, self.rule_2, self.rule_3], filter_active=True, exclude_inactive_yesterday=False
        )
        self.assertEqual(
            {
                self.ad_groups[0]: [self.rule_1],
                self.ad_groups[1]: [self.rule_1, self.rule_3],
                self.ad_groups[2]: [self.rule_1, self.rule_3],
                self.ad_groups[3]: [self.rule_2, self.rule_3],
                self.ad_groups[4]: [self.rule_2],
            },
            rules_map,
        )

    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_exclude_inactive_yesterday_spend(self, mock_breakdowns_query):
        mock_breakdowns_query.return_value = [
            {"ad_group_id": self.ad_groups[0].id, "local_yesterday_etfm_cost": 500},
            {"ad_group_id": self.ad_groups[1].id, "local_yesterday_etfm_cost": 5},
            {"ad_group_id": self.ad_groups[2].id, "local_yesterday_etfm_cost": 1},
        ]
        rules_map = helpers.get_rules_by_ad_group_map(
            [self.rule_1, self.rule_2, self.rule_3], filter_active=True, exclude_inactive_yesterday=True
        )
        self.assertEqual(
            {
                self.ad_groups[0]: [self.rule_1],
                self.ad_groups[1]: [self.rule_1, self.rule_3],
                self.ad_groups[2]: [self.rule_1, self.rule_3],
            },
            rules_map,
        )

    @mock.patch("redshiftapi.api_breakdowns.query")
    @mock.patch("automation.rules.service.helpers._get_time_active_yesterday_per_ad_group_id")
    def test_exclude_inactive_settings(self, mock_time_active, mock_breakdowns_query):
        mock_breakdowns_query.return_value = []
        mock_time_active.return_value = {
            self.ad_groups[0].id: 0,
            self.ad_groups[1].id: 7199,
            self.ad_groups[2].id: 7200,
            self.ad_groups[3].id: 43200,
            self.ad_groups[4].id: 86400,
        }
        rules_map = helpers.get_rules_by_ad_group_map(
            [self.rule_1, self.rule_2, self.rule_3], filter_active=True, exclude_inactive_yesterday=True
        )
        self.assertEqual(
            {
                self.ad_groups[2]: [self.rule_1, self.rule_3],
                self.ad_groups[3]: [self.rule_2, self.rule_3],
                self.ad_groups[4]: [self.rule_2],
            },
            rules_map,
        )


class GetTimeActiveTest(TestCase):
    def setUp(self):
        self.utc_dt_ad_group = datetime.datetime(2020, 5, 2, 22, 0, 0)
        self.utc_dt_first_settings = datetime.datetime(2020, 5, 2, 22, 0, 1)
        with patch_settings_datetime(self.utc_dt_ad_group):
            self.ad_group = magic_mixer.blend(core.models.AdGroup)

    def test_whole_day(self):
        with patch_settings_datetime(self.utc_dt_first_settings):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)

        time_active = helpers._get_time_active_yesterday_per_ad_group_id([self.ad_group])
        self.assertEqual({self.ad_group.id: 24 * 60 * 60}, time_active)

    def test_inactive_start_of_day(self):
        with patch_settings_datetime(self.utc_dt_first_settings):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        time_active = helpers._get_time_active_yesterday_per_ad_group_id([self.ad_group])
        self.assertEqual({}, time_active)

    def test_inactive_end_of_day(self):
        with patch_settings_datetime(self.utc_dt_first_settings):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(12)):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        time_active = helpers._get_time_active_yesterday_per_ad_group_id([self.ad_group])
        self.assertEqual({self.ad_group.id: 12 * 60 * 60}, time_active)

    def test_paused_and_started_midday(self):
        with patch_settings_datetime(self.utc_dt_first_settings):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(12)):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(12, 30)):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(17)):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(18, 40)):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        time_active = helpers._get_time_active_yesterday_per_ad_group_id([self.ad_group])
        self.assertEqual({self.ad_group.id: 130 * 60}, time_active)

    def test_multiple_ad_groups(self):
        with patch_settings_datetime(self.utc_dt_first_settings):
            self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)

        with patch_settings_datetime(self._get_yesterday_local_to_utc(11, 59)):
            new_ad_group = magic_mixer.blend(core.models.AdGroup)
        with patch_settings_datetime(self._get_yesterday_local_to_utc(12)):
            new_ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)

        time_active = helpers._get_time_active_yesterday_per_ad_group_id([new_ad_group, self.ad_group])
        self.assertEqual({self.ad_group.id: 24 * 60 * 60, new_ad_group.id: 12 * 60 * 60}, time_active)

    def _get_yesterday_local_to_utc(self, hour=0, minute=0):
        local_yesterday = dates_helper.local_yesterday()
        mock_local_dt = datetime.datetime(
            local_yesterday.year, local_yesterday.month, local_yesterday.day, hour, minute, 0
        )
        mock_utc_dt = dates_helper.local_to_utc_time(mock_local_dt).replace(tzinfo=None)
        return mock_utc_dt


@contextlib.contextmanager
def patch_settings_datetime(mocked_datetime):
    with mock.patch(
        "core.models.settings.settings_base.datetime",
        type("_mockdatetime", (datetime.datetime,), {"utcnow": lambda: mocked_datetime}),
    ) as datetime_mock:
        yield (datetime_mock,)
