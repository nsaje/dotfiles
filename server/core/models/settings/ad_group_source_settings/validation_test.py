import decimal

from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper
from core.models.settings.ad_group_source_settings import exceptions


class ValidateAdGroupSourceUpdatesTestCase(TestCase):
    def setUp(self):
        today = dates_helper.local_today()
        self.account = magic_mixer.blend(core.models.Account, uses_bcm_v2=True)
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=dates_helper.day_before(today),
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.15"),
        )

        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.budget = magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.day_before(today),
            end_date=today,
            credit=self.credit,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0.30"),
        )

        source_type = magic_mixer.blend(
            core.models.SourceType,
            min_cpc=decimal.Decimal("0.03"),
            min_cpm=decimal.Decimal("0.03"),
            min_daily_budget=decimal.Decimal("10"),
            max_cpc=decimal.Decimal("5"),
            max_cpm=decimal.Decimal("5"),
            max_daily_budget=decimal.Decimal("10000"),
        )
        self.source = magic_mixer.blend(core.models.Source, source_type=source_type)

    def test_validate_ad_group_source_cpc_cc(self):
        ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group__campaign=self.campaign, source=self.source
        )
        ad_group_source.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpc_cc=decimal.Decimal("0.35"),
            daily_budget_cc=decimal.Decimal("50"),
        )

        updates = {}

        updates["cpc_cc"] = decimal.Decimal("0.0")
        with self.assertRaises(exceptions.MinimalCPCTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        updates["cpc_cc"] = decimal.Decimal("0.05")
        with self.assertRaises(exceptions.MinimalCPCTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertEqual(decimal.Decimal("0.051"), exception.data["value"])

        updates["cpc_cc"] = decimal.Decimal("8.404")
        with self.assertRaises(exceptions.MaximalCPCTooHigh) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertEqual(decimal.Decimal("8.403"), exception.data["value"])

        updates["cpc_cc"] = decimal.Decimal("5")
        ad_group_source.settings.update(None, **updates)

    def test_validate_ad_group_source_cpm(self):
        ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group__campaign=self.campaign, source=self.source
        )
        ad_group_source.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpm=decimal.Decimal("0.35"),
            daily_budget_cc=decimal.Decimal("50"),
        )

        updates = {}

        updates["cpm"] = decimal.Decimal("0.0")
        with self.assertRaises(exceptions.MinimalCPMTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        updates["cpm"] = decimal.Decimal("0.05")
        with self.assertRaises(exceptions.MinimalCPMTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertEqual(decimal.Decimal("0.051"), exception.data["value"])

        updates["cpm"] = decimal.Decimal("8.404")
        with self.assertRaises(exceptions.MaximalCPMTooHigh) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertEqual(decimal.Decimal("8.403"), exception.data["value"])

        updates["cpm"] = decimal.Decimal("5")
        ad_group_source.settings.update(None, **updates)

    def test_validate_ad_group_source_daily_budget(self):
        ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group__campaign=self.campaign, source=self.source
        )
        ad_group_source.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpc_cc=decimal.Decimal("0.35"),
            daily_budget_cc=decimal.Decimal("50"),
        )

        updates = {}

        updates["daily_budget_cc"] = decimal.Decimal("0.0")
        with self.assertRaises(exceptions.MinimalDailyBudgetTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        updates["daily_budget_cc"] = decimal.Decimal("0.5")
        with self.assertRaises(exceptions.MinimalDailyBudgetTooLow) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertTrue(decimal.Decimal("17"), exception.data)

        updates["daily_budget_cc"] = decimal.Decimal("99999")
        with self.assertRaises(exceptions.MaximalDailyBudgetTooHigh) as cm:
            ad_group_source.settings.update(None, **updates)

        exception = cm.exception
        self.assertTrue(decimal.Decimal("16806"), exception.data)

        updates["daily_budget_cc"] = decimal.Decimal("100")
        ad_group_source.settings.update(None, **updates)

    def test_validate_state(self):
        ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group__campaign=self.campaign, source=self.source
        )
        ad_group_source.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            cpc_cc=decimal.Decimal("0.35"),
            daily_budget_cc=decimal.Decimal("50"),
        )

        updates = {}
        updates["cpc_cc"] = decimal.Decimal("0.05")
        updates["state"] = dash.constants.AdGroupSourceSettingsState.INACTIVE
        with self.assertRaises(exceptions.MinimalCPCTooLow):
            ad_group_source.settings.update(None, **updates)
        self.assertEqual(ad_group_source.settings.state, dash.constants.AdGroupSettingsState.ACTIVE)

        ad_group_source.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.05"))

        updates = {}
        updates["state"] = dash.constants.AdGroupSourceSettingsState.INACTIVE
        ad_group_source.settings.update(None, skip_automation=True, **updates)
        self.assertEqual(ad_group_source.settings.state, dash.constants.AdGroupSettingsState.INACTIVE)

        with self.assertRaises(exceptions.MinimalCPCTooLow):
            ad_group_source.settings.update(
                None, skip_automation=True, state=dash.constants.AdGroupSourceSettingsState.ACTIVE
            )