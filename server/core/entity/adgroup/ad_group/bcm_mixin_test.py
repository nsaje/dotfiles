import decimal
from mock import patch, MagicMock

from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity
import core.bcm


class MigrateToBcmV2Test(TestCase):

    def setUp(self):
        self._set_up_patchers()
        today = datetime.date.today()

        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        self.request = magic_mixer.blend_request_user(permissions=['can_set_ad_group_max_cpm'])
        self.ad_group.settings.update(
            self.request,
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
            b1_sources_group_daily_budget=decimal.Decimal('50'),
            b1_sources_group_cpc_cc=decimal.Decimal('0.3'),
            autopilot_daily_budget=decimal.Decimal('100'),
            max_cpm=decimal.Decimal('1.22'),
        )
        campaign_goal = magic_mixer.blend(core.goals.CampaignGoal, campaign=campaign, primary=True, value='0.1')
        campaign_goal.add_value(self.request, decimal.Decimal('0.1'))

    def _set_up_patchers(self):
        redirector_insert_patcher = patch('utils.redirector_helper.insert_adgroup', MagicMock())
        redirector_insert_patcher.start()
        self.addCleanup(redirector_insert_patcher.stop)

        redshiftapi_patcher = patch('redshiftapi.api_breakdowns.query_all', MagicMock())
        redshiftapi_patcher.start()
        self.addCleanup(redshiftapi_patcher.stop)
=======
        self.fee = decimal.Decimal('0.2')
        self.margin = decimal.Decimal('0.1')
>>>>>>> Fix existing tests

    @patch('utils.k1_helper.update_ad_group', MagicMock())
    @patch.object(core.entity.AdGroupSource, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2(self, mock_ad_group_source_migrate):
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group)

        self._test_migrate_to_bcm_v2()
        self.assertTrue(ad_group_source.migrate_to_bcm_v2.called)

    @patch('utils.k1_helper.update_ad_group', MagicMock())
    @patch.object(core.entity.AdGroupSource, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2_b1_sources_group_enabled(self, mock_ad_group_source_migrate):
        source_type = magic_mixer.blend(core.source.SourceType, type=constants.SourceType.B1)
        source = magic_mixer.blend(core.source.Source, source_type=source_type)
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=source)

        self._test_migrate_to_bcm_v2()
        self.assertFalse(ad_group_source.migrate_to_bcm_v2.called)

    @patch('utils.k1_helper.update_ad_group', MagicMock())
    @patch.object(core.entity.AdGroupSource, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2_full_autopilot_enabled(self, mock_ad_group_source_migrate):
        source_type = magic_mixer.blend(core.source.SourceType, type=constants.SourceType.B1)
        source = magic_mixer.blend(core.source.Source, source_type=source_type)
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=source)

        self.ad_group.settings.update(
            self.request,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )

        self._test_migrate_to_bcm_v2()
        self.assertTrue(ad_group_source.migrate_to_bcm_v2.called)

    def _test_migrate_to_bcm_v2(self):
        self.ad_group.migrate_to_bcm_v2(self.request)

        self.assertEqual(70, self.ad_group.settings.b1_sources_group_daily_budget)
        self.assertEqual(139, self.ad_group.settings.autopilot_daily_budget)
        self.assertEqual(decimal.Decimal('0.417'), self.ad_group.settings.b1_sources_group_cpc_cc)
        self.assertEqual(decimal.Decimal('1.694'), self.ad_group.settings.max_cpm)
