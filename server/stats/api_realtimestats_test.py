import copy
import decimal
import random

import mock
from django.test import TestCase
from parameterized import parameterized

import core.models
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import api_realtimestats

ACCOUNT_ID = "1234"
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
    ("account_id", {"account_id": ACCOUNT_ID, "breakdown": []}, {**STATS_ROW}, api_realtimestats.InvalidBreakdown),
    (
        "account_id",
        {"account_id": ACCOUNT_ID, "breakdown": ["campaign_id"]},
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

GROUPBY_SOURCE_GROUPS_TEST_CASES = [
    ("campaign_id", {"campaign_id": CAMPAIGN_ID, "breakdown": ["media_source"]}),
    ("ad_group_id", {"ad_group_id": AD_GROUP_ID, "breakdown": ["media_source"]}),
    ("content_ad_id", {"content_ad_id": CONTENT_AD_ID, "breakdown": ["media_source"]}),
]

TOPN_SOURCE_GROUPS_TEST_CASES = [
    ("campaign_id", {"campaign_id": CAMPAIGN_ID, "breakdown": ["media_source"], "order": "spend"}),
    ("ad_group_id", {"ad_group_id": AD_GROUP_ID, "breakdown": ["media_source"], "order": "spend"}),
    ("content_ad_id", {"content_ad_id": CONTENT_AD_ID, "breakdown": ["media_source"], "order": "spend"}),
]


class RealtimeStatsTest(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account, id=ACCOUNT_ID, agency__uses_source_groups=True)
        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID, account=self.account)
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

        self.account = magic_mixer.blend(core.models.Account, id=ACCOUNT_ID, agency__uses_source_groups=True)
        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID, account=self.account)
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

        self.account = magic_mixer.blend(core.models.Account, id=ACCOUNT_ID, agency__uses_source_groups=True)
        self.campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID, account=self.account)
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


class RealTimeStatsSourceGroupsTest(TestCase):
    def setUp(self):
        account = magic_mixer.blend(core.models.Account, id=ACCOUNT_ID, agency__uses_source_groups=True)
        campaign = magic_mixer.blend(core.models.Campaign, id=CAMPAIGN_ID, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, id=AD_GROUP_ID, campaign=campaign)
        magic_mixer.blend(core.models.ContentAd, id=CONTENT_AD_ID, ad_group=ad_group)

        sources = magic_mixer.cycle(8).blend(
            core.models.Source, bidder_slug=("slug" + str(i) for i in range(1, 9)), id=(i for i in range(80, 88))
        )

        self.query_return_value = [copy.copy(STATS_ROW) | {"media_source": s.bidder_slug} for s in sources]
        self.expected_result = [
            {
                "media_source": "slug1",
                "clicks": 10428,
                "impressions": 8846020,
                "price_nano": 4852520000000.0,
                "data_price_nano": 0.0,
                "spend": test_helper.AlmostMatcher(decimal.Decimal("4852.5200")),
                "ctr": 0.0011788352275938785,
                "cpc": test_helper.AlmostMatcher(decimal.Decimal("0.4653")),
                "cpm": test_helper.AlmostMatcher(decimal.Decimal("0.548554")),
            },
            {
                "media_source": "slug2",
                "clicks": 7821,
                "impressions": 6634515,
                "price_nano": 3639390000000.0,
                "data_price_nano": 0.0,
                "spend": test_helper.AlmostMatcher(decimal.Decimal("3639.39")),
                "ctr": 0.0011788352275938785,
                "cpc": test_helper.AlmostMatcher(decimal.Decimal("0.465336")),
                "cpm": test_helper.AlmostMatcher(decimal.Decimal("0.548554")),
            },
            {
                "media_source": "slug8",
                "clicks": 2607,
                "impressions": 2211505,
                "price_nano": 1213130000000.0,
                "data_price_nano": 0.0,
                "spend": test_helper.AlmostMatcher(decimal.Decimal("1213.13")),
                "ctr": 0.0011788352275938785,
                "cpc": test_helper.AlmostMatcher(decimal.Decimal("0.465336")),
                "cpm": test_helper.AlmostMatcher(decimal.Decimal("0.548554")),
            },
        ]

    @parameterized.expand(GROUPBY_SOURCE_GROUPS_TEST_CASES)
    @mock.patch("django.conf.settings.SOURCE_GROUPS", {80: [82, 83, 84], 81: [85, 86]})
    @mock.patch("realtimeapi.api.groupby")
    def test_groupby(self, _, query_kwargs, mock_groupby):
        mock_groupby.return_value = self.query_return_value

        rows = api_realtimestats.groupby(**query_kwargs)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.expected_result, rows)

    @parameterized.expand(TOPN_SOURCE_GROUPS_TEST_CASES)
    @mock.patch("django.conf.settings.SOURCE_GROUPS", {80: [82, 83, 84], 81: [85, 86]})
    @mock.patch("realtimeapi.api.topn")
    def test_topn_source_groups(self, _, query_kwargs, mock_topn):
        mock_topn.return_value = self.query_return_value

        rows = api_realtimestats.topn(**query_kwargs)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.expected_result, rows)
