import copy
import decimal
import random

import mock
from django.test import TestCase
from parameterized import parameterized

import core.models
from utils.magic_mixer import magic_mixer

from . import api_realtimestats

CAMPAIGN_ID = str(random.randint(10 ** 5, 10 ** 6))
AD_GROUP_ID = str(random.randint(10 ** 5, 10 ** 6))
CONTENT_AD_ID = str(random.randint(10 ** 5, 10 ** 6))

STATS_ROW = {
    "clicks": 2607,
    "impressions": 2211505,
    "price_nano": 1213130000000.0,
    "data_price_nano": 0.0,
    "spend": 1213.13,
}


GROUPBY_TEST_CASES = [
    ("account_id", {"account_id": "1234", "breakdown": []}, {**STATS_ROW}, api_realtimestats.InvalidBreakdown),
    (
        "account_id",
        {"account_id": "1234", "breakdown": ["campaign_id"]},
        {**STATS_ROW, "campaign_id": CAMPAIGN_ID},
        False,
    ),
    ("campaign_id", {"campaign_id": CAMPAIGN_ID, "breakdown": []}, {**STATS_ROW}, False),
    ("ad_group_id", {"ad_group_id": AD_GROUP_ID, "breakdown": []}, {**STATS_ROW}, False),
    ("content_ad_id", {"content_ad_id": CONTENT_AD_ID}, {**STATS_ROW}, False),
    ("campaign_id_breakdown", {"breakdown": "campaign_id"}, {**STATS_ROW, "campaign_id": CAMPAIGN_ID}, False),
    ("ad_group_id_breakdown", {"breakdown": "ad_group_id"}, {**STATS_ROW, "ad_group_id": AD_GROUP_ID}, False),
    ("content_ad_id_breakdown", {"breakdown": "content_ad_id"}, {**STATS_ROW, "content_ad_id": CONTENT_AD_ID}, False),
]

TOPN_TEST_CASES = [
    ("campaign_id", {"campaign_id": CAMPAIGN_ID, "breakdown": [], "order": "spend"}, {**STATS_ROW}, False),
    ("ad_group_id", {"ad_group_id": AD_GROUP_ID, "breakdown": [], "order": "spend"}, {**STATS_ROW}, False),
    ("content_ad_id", {"content_ad_id": CONTENT_AD_ID, "breakdown": [], "order": "spend"}, {**STATS_ROW}, False),
    (
        "campaign_id_breakdown",
        {"breakdown": "campaign_id", "order": "spend"},
        {**STATS_ROW, "campaign_id": CAMPAIGN_ID},
        AssertionError,
    ),
    (
        "ad_group_id_breakdown",
        {"breakdown": "ad_group_id", "order": "spend"},
        {**STATS_ROW, "ad_group_id": AD_GROUP_ID},
        AssertionError,
    ),
    (
        "content_ad_id_breakdown",
        {"breakdown": "content_ad_id", "order": "spend"},
        {**STATS_ROW, "content_ad_id": CONTENT_AD_ID},
        AssertionError,
    ),
]


class RealtimeStatsTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, id=AD_GROUP_ID, campaign=self.campaign)
        self.content_ad = magic_mixer.blend(core.models.ContentAd, id=CONTENT_AD_ID, ad_group=self.ad_group)

    @parameterized.expand(GROUPBY_TEST_CASES)
    @mock.patch("realtimeapi.api.groupby")
    def test_groupby(self, name, query_kwargs, stats_row, expected_exception, mock_groupby):
        mock_groupby.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.groupby(**query_kwargs)
        else:
            rows = api_realtimestats.groupby(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("1213.13"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.4653"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.5486"), row["cpm"], places=4)

    @parameterized.expand(TOPN_TEST_CASES)
    @mock.patch("realtimeapi.api.topn")
    def test_topn(self, _, query_kwargs, stats_row, expected_exception, mock_topn):
        mock_topn.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.topn(**query_kwargs)
        else:
            rows = api_realtimestats.topn(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("1213.13"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.4653"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.5486"), row["cpm"], places=4)


class RealTimeStatsFeesMarginsTest(TestCase):
    def setUp(self):
        self.get_todays_fees_and_margin_patcher = mock.patch.object(core.models.Campaign, "get_todays_fees_and_margin")
        mock_get_todays_fees_and_margin = self.get_todays_fees_and_margin_patcher.start()
        mock_get_todays_fees_and_margin.return_value = (
            decimal.Decimal("0.08"),
            decimal.Decimal("0.15"),
            decimal.Decimal("0.3"),
        )

        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, id=AD_GROUP_ID, campaign=self.campaign)
        self.content_ad = magic_mixer.blend(core.models.ContentAd, id=CONTENT_AD_ID, ad_group=self.ad_group)

    def tearDown(self):
        self.get_todays_fees_and_margin_patcher.stop()

    @parameterized.expand(GROUPBY_TEST_CASES)
    @mock.patch("realtimeapi.api.groupby")
    def test_groupby(self, name, query_kwargs, stats_row, expected_exception, mock_groupby):
        mock_groupby.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.groupby(**query_kwargs)
        else:
            rows = api_realtimestats.groupby(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("2216.1673"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.8501"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("1.0021"), row["cpm"], places=4)

    @parameterized.expand(TOPN_TEST_CASES)
    @mock.patch("realtimeapi.api.topn")
    def test_topn(self, _, query_kwargs, stats_row, expected_exception, mock_topn):
        mock_topn.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.topn(**query_kwargs)
        else:
            rows = api_realtimestats.topn(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("2216.1673"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.8501"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("1.0021"), row["cpm"], places=4)


class RealTimeStatsFeesMulticurrencyTest(TestCase):
    def setUp(self):
        self.get_current_exchange_rate_patcher = mock.patch("core.features.multicurrency.get_current_exchange_rate")
        mock_get_current_exchange_rate = self.get_current_exchange_rate_patcher.start()
        mock_get_current_exchange_rate.return_value = decimal.Decimal("1.2")

        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, id=AD_GROUP_ID, campaign=self.campaign)
        self.content_ad = magic_mixer.blend(core.models.ContentAd, id=CONTENT_AD_ID, ad_group=self.ad_group)

    def tearDown(self):
        self.get_current_exchange_rate_patcher.stop()

    @parameterized.expand(GROUPBY_TEST_CASES)
    @mock.patch("realtimeapi.api.groupby")
    def test_groupby(self, name, query_kwargs, stats_row, expected_exception, mock_groupby):
        mock_groupby.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.groupby(**query_kwargs)
        else:
            rows = api_realtimestats.groupby(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("1455.756"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.5584"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.6583"), row["cpm"], places=4)

    @parameterized.expand(TOPN_TEST_CASES)
    @mock.patch("realtimeapi.api.topn")
    def test_topn(self, _, query_kwargs, stats_row, expected_exception, mock_topn):
        mock_topn.return_value = [copy.copy(stats_row)]
        if expected_exception:
            with self.assertRaises(expected_exception):
                api_realtimestats.topn(**query_kwargs)
        else:
            rows = api_realtimestats.topn(**query_kwargs)
            self.assertEqual(1, len(rows))

            row = rows[0]
            self.assertAlmostEqual(decimal.Decimal("1455.756"), row["spend"], places=4)
            self.assertAlmostEqual(0.0012, row["ctr"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.5584"), row["cpc"], places=4)
            self.assertAlmostEqual(decimal.Decimal("0.6583"), row["cpm"], places=4)
