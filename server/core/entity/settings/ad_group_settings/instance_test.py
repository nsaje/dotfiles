from decimal import Decimal
from mock import patch

from django.test import TestCase
from utils.magic_mixer import magic_mixer

import core.entity
from dash import constants

import instance


class InstanceTest(TestCase):

    def test_b1_sources_group_adjustments_sets_default_cpc_and_daily_budget(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal('0.111')
        new_settings.b1_sources_group_daily_budget = Decimal('100.0')
        new_settings.cpc_cc = Decimal('0.5')
        new_settings.save(None)

        # turn on rtb as one
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(changes, {'b1_sources_group_enabled': True})

        changes_new, cs2, ns2 = instance.AdGroupSettingsMixin._b1_sources_group_adjustments(changes, current_settings, new_settings)

        self.assertDictEqual(changes_new, {
            'b1_sources_group_enabled': True,
            'b1_sources_group_cpc_cc': min(ns2.cpc_cc, constants.SourceAllRTB.DEFAULT_CPC_CC),
            'b1_sources_group_daily_budget': constants.SourceAllRTB.DEFAULT_DAILY_BUDGET,
        })

    def test_b1_sources_group_adjustments_sets_new_cpc_daily_budget(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal('0.111')
        new_settings.b1_sources_group_daily_budget = Decimal('100.0')
        new_settings.cpc_cc = Decimal('0.5')
        new_settings.save(None)

        # turn on rtb as one
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_daily_budget = Decimal('10.0')
        new_settings.b1_sources_group_cpc_cc = Decimal('0.211')
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(changes, {
            'b1_sources_group_enabled': True,
            'b1_sources_group_cpc_cc': Decimal('0.211'),
            'b1_sources_group_daily_budget': Decimal('10.0'),
        })

        changes_new, cs2, ns2 = instance.AdGroupSettingsMixin._b1_sources_group_adjustments(changes, current_settings, new_settings)

        self.assertDictEqual(changes_new, {
            'b1_sources_group_enabled': True,
            'b1_sources_group_cpc_cc': Decimal('0.211'),
            'b1_sources_group_daily_budget': Decimal('10.0'),
        })

    def test_b1_sources_group_adjustments_obeys_new_adgroup_max_cpc(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal('0.111')
        new_settings.b1_sources_group_daily_budget = Decimal('100.0')
        new_settings.cpc_cc = Decimal('0.5')
        new_settings.save(None)

        # turn on rtb as one
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.cpc_cc = Decimal('0.05')
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(changes, {
            'b1_sources_group_enabled': True,
            'cpc_cc': Decimal('0.05'),
        })

        changes_new, cs2, ns2 = instance.AdGroupSettingsMixin._b1_sources_group_adjustments(changes, current_settings, new_settings)

        self.assertDictEqual(changes_new, {
            'b1_sources_group_enabled': True,
            'b1_sources_group_cpc_cc': Decimal('0.05'),
            'b1_sources_group_daily_budget': constants.SourceAllRTB.DEFAULT_DAILY_BUDGET,
            'cpc_cc': Decimal('0.05')
        })

    @patch('utils.redirector_helper.insert_adgroup')
    def test_get_external_max_cpm(self, mock_insert_adgroup):
        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        request = magic_mixer.blend_request_user(permissions=['can_set_ad_group_max_cpm'])

        ad_group.settings.update(
            request, max_cpm=None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.assertEqual(None, ad_group.settings.get_external_max_cpm(account, Decimal('0.2'), Decimal('0.1')))

        ad_group.settings.update(
            request, max_cpm=Decimal('0.5'))
        self.assertEqual(Decimal('0.5'), ad_group.settings.get_external_max_cpm(account, Decimal('0.2'), Decimal('0.1')))

        account.uses_bcm_v2 = True
        self.assertEqual(Decimal('0.36'), ad_group.settings.get_external_max_cpm(account, Decimal('0.2'), Decimal('0.1')))
