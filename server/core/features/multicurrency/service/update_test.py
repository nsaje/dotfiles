import decimal

from mock import patch

import core.features.goals
import core.models
import dash.constants
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from .. import CurrencyExchangeRate
from . import update


class UpdateExchangeRatesTestCase(BaseTestCase):
    def setUp(self):
        CurrencyExchangeRate.objects.create(
            date="2018-01-01", currency=dash.constants.Currency.EUR, exchange_rate="0.8"
        )
        request = magic_mixer.blend_request_user(is_superuser=True)
        self.account = magic_mixer.blend(core.models.Account, currency=dash.constants.Currency.EUR)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.goal1 = magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPC,
        )
        self.goal2 = magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.campaign,
            primary=False,
            type=dash.constants.CampaignGoalKPI.PAGES_PER_SESSION,
        )
        self.goal1.add_local_value(request, decimal.Decimal("0.15"))
        self.goal2.add_local_value(request, 20)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group.settings.update(
            request,
            skip_automation=True,
            skip_validation=True,
            local_cpc="0.8",
            local_autopilot_daily_budget=100,
            local_b1_sources_group_cpc_cc="0.35",
            local_cpm="1.3",
        )
        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group)
        self.ad_group_source.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=True,
            local_cpc_cc="0.62",
            local_daily_budget_cc=28,
        )
        self.ad_group.settings.update(
            request, skip_automation=True, skip_validation=True, local_b1_sources_group_daily_budget=72
        )
        self.prepare_threadpoolexecutor_mock("concurrent.futures.ThreadPoolExecutor")

    def test_initial_settings(self):
        self.ad_group.settings.refresh_from_db()
        self.ad_group_source.settings.refresh_from_db()

        self._test_initial_local_settings()
        self.assertEqual(decimal.Decimal("1"), self.ad_group.settings.cpc)
        self.assertEqual(decimal.Decimal("125"), self.ad_group.settings.autopilot_daily_budget)
        self.assertEqual(decimal.Decimal("90"), self.ad_group.settings.b1_sources_group_daily_budget)
        self.assertEqual(decimal.Decimal("90"), self.ad_group.settings.daily_budget)
        self.assertEqual(decimal.Decimal("0.4375"), self.ad_group.settings.b1_sources_group_cpc_cc)
        self.assertEqual(decimal.Decimal("1.625"), self.ad_group.settings.cpm)
        self.assertEqual(decimal.Decimal("35"), self.ad_group_source.settings.daily_budget_cc)
        self.assertEqual(decimal.Decimal("0.775"), self.ad_group_source.settings.cpc_cc)
        self.assertEqual(decimal.Decimal("0.1875"), self.goal1.get_current_value().value)
        self.assertEqual(20, self.goal2.get_current_value().value)

    @patch("core.features.multicurrency.service.ecb._fetch_ecb_exchange_rates")
    def test_update_exchange_rates(self, mock_get_exchange_rates):
        mock_get_exchange_rates.return_value = {dash.constants.Currency.USD: decimal.Decimal("1.3333")}
        update.update_exchange_rates(currencies=[dash.constants.Currency.EUR])
        self.ad_group.settings.refresh_from_db()
        self.ad_group_source.settings.refresh_from_db()

        self._test_initial_local_settings()
        self.assertEqual(decimal.Decimal("1.0667"), self.ad_group.settings.cpc)
        self.assertEqual(decimal.Decimal("133.3333"), self.ad_group.settings.autopilot_daily_budget)
        self.assertEqual(decimal.Decimal("96"), self.ad_group.settings.b1_sources_group_daily_budget)
        self.assertEqual(decimal.Decimal("96"), self.ad_group.settings.daily_budget)
        self.assertEqual(decimal.Decimal("0.4667"), self.ad_group.settings.b1_sources_group_cpc_cc)
        self.assertEqual(decimal.Decimal("1.7333"), self.ad_group.settings.cpm)
        self.assertEqual(decimal.Decimal("37.3333"), self.ad_group_source.settings.daily_budget_cc)
        self.assertEqual(decimal.Decimal("0.8267"), self.ad_group_source.settings.cpc_cc)
        self.assertEqual(decimal.Decimal("0.2"), self.goal1.get_current_value().value)
        self.assertEqual(20, self.goal2.get_current_value().value)

    def _test_initial_local_settings(self):
        self.assertEqual(decimal.Decimal("0.8"), self.ad_group.settings.local_cpc)
        self.assertEqual(decimal.Decimal("100"), self.ad_group.settings.local_autopilot_daily_budget)
        self.assertEqual(decimal.Decimal("72"), self.ad_group.settings.local_b1_sources_group_daily_budget)
        self.assertEqual(decimal.Decimal("72"), self.ad_group.settings.local_daily_budget)
        self.assertEqual(decimal.Decimal("0.35"), self.ad_group.settings.local_b1_sources_group_cpc_cc)
        self.assertEqual(decimal.Decimal("1.3"), self.ad_group.settings.local_cpm)
        self.assertEqual(decimal.Decimal("28"), self.ad_group_source.settings.local_daily_budget_cc)
        self.assertEqual(decimal.Decimal("0.62"), self.ad_group_source.settings.local_cpc_cc)
        self.assertEqual(decimal.Decimal("0.15"), self.goal1.get_current_value().local_value)
        self.assertEqual(20, self.goal2.get_current_value().local_value)

    def test_sanity_check(self):
        update._sanity_check({"cpc": 0.12}, ["cpc"])
        with self.assertRaises(update.ProgrammingError):
            update._sanity_check({"cpc": 0.12, "local_cpc": 1.23}, ["cpc"])
