import decimal

from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer


class GetEtfmLimitsTestCase(TestCase):
    def setUp(self):
        self.source_type = magic_mixer.blend(
            core.models.SourceType,
            min_cpc=decimal.Decimal("0.03"),
            max_cpc=decimal.Decimal("10.0"),
            min_cpm=decimal.Decimal("0.03"),
            max_cpm=decimal.Decimal("10.0"),
            min_daily_budget=decimal.Decimal("10"),
            max_daily_budget=decimal.Decimal("1000"),
        )
        self.bcm_modifiers = {"fee": decimal.Decimal("0.15"), "margin": decimal.Decimal("0.33")}

    def test_get_etfm_min_cpc(self):
        self.assertEqual(decimal.Decimal("0.03"), self.source_type.get_etfm_min_cpc())

    def test_get_etfm_min_cpc_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("0.053"), self.source_type.get_etfm_min_cpc(self.bcm_modifiers))

    def test_get_etfm_max_cpc(self):
        self.assertEqual(decimal.Decimal("10.0"), self.source_type.get_etfm_max_cpc())

    def test_get_etfm_max_cpc_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("17.559"), self.source_type.get_etfm_max_cpc(self.bcm_modifiers))

    def test_get_etfm_min_cpm(self):
        self.assertEqual(decimal.Decimal("0.03"), self.source_type.get_etfm_min_cpm())

    def test_get_etfm_min_cpm_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("0.053"), self.source_type.get_etfm_min_cpm(self.bcm_modifiers))

    def test_get_etfm_max_cpm(self):
        self.assertEqual(decimal.Decimal("10.0"), self.source_type.get_etfm_max_cpm())

    def test_get_etfm_max_cpm_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("17.559"), self.source_type.get_etfm_max_cpm(self.bcm_modifiers))

    def test_get_etfm_min_daily_budget(self):
        self.assertEqual(decimal.Decimal("10.0"), self.source_type.get_etfm_min_daily_budget())

    def test_get_etfm_min_daily_budget_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("18"), self.source_type.get_etfm_min_daily_budget(self.bcm_modifiers))

    def test_get_etfm_max_daily_budget(self):
        self.assertEqual(decimal.Decimal("1000.0"), self.source_type.get_etfm_max_daily_budget())

    def test_get_etfm_max_daily_budget_with_bcm_modifiers(self):
        self.assertEqual(decimal.Decimal("1755"), self.source_type.get_etfm_max_daily_budget(self.bcm_modifiers))
