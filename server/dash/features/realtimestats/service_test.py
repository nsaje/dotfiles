import datetime
import decimal
import urllib.error
import urllib.parse
import urllib.request

import mock
import pytz
from django.test import TestCase

import core.models
import dash.constants
from dash.features.realtimestats import service
from utils import dates_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer


class RealtimestatsServiceTest(TestCase):
    def setUp(self):
        ad_group_sources = [
            {"type": "outbrain", "source_campaign_key": {"campaign_id": "test_outbrain_1"}},
            {"type": "yahoo", "source_campaign_key": "test_yahoo_1"},
        ]
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group_sources = magic_mixer.cycle(len(ad_group_sources)).blend(
            core.models.AdGroupSource,
            ad_group=self.ad_group,
            ad_review_only=False,
            source__source_type__type=(ags["type"] for ags in ad_group_sources),
            source_campaign_key=(ags["source_campaign_key"] for ags in ad_group_sources),
        )

        self._set_up_budgets()

    def _set_up_budgets(self):
        today = dates_helper.local_today()

        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=today,
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            service_fee=decimal.Decimal("0.1111"),
            license_fee=decimal.Decimal("0.3333"),
        )

        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=today,
            end_date=today,
            credit=credit,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0.2200"),
        )

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_stats(self, mock_k1_get):
        mock_k1_get.return_value = {
            "spend": [
                {"spend": 3.0, "source_slug": self.ad_group_sources[0].source.bidder_slug},
                {"spend": 1.1, "source_slug": self.ad_group_sources[1].source.bidder_slug},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }

        result = service.get_ad_group_stats(self.ad_group)
        self.assertEqual(
            result, {"clicks": 15, "impressions": 100, "spend": test_helper.AlmostMatcher(decimal.Decimal("8.8696"))}
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, {})

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(
            result,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("6.4900")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.3797")),
                    },
                ],
                "clicks": 15,
                "impressions": 100,
            },
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, {})

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_only_allowed(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
                {"source_slug": "amplify", "spend": 3.0},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(
            result,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("6.4900")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.3797")),
                    },
                ],
                "clicks": 15,
                "impressions": 100,
            },
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, {})

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_multicurrency(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": decimal.Decimal("1.1")},
                {"source_slug": sources[1].bidder_slug, "spend": decimal.Decimal("3.0")},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }
        self.ad_group.campaign.account.currency = dash.constants.Currency.EUR
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            date=dates_helper.local_today(), currency=dash.constants.Currency.EUR, exchange_rate=decimal.Decimal("1.2")
        )
        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(
            result,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("6.4900")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.3797")),
                    },
                ],
                "clicks": 15,
                "impressions": 100,
            },
        )
        mock_k1_get.assert_called_once_with(self.ad_group.id, {})
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": decimal.Decimal("1.1")},
                {"source_slug": sources[1].bidder_slug, "spend": decimal.Decimal("3.0")},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }

        result_local = service.get_ad_group_sources_stats(self.ad_group, use_local_currency=True)
        self.assertEqual(
            result_local,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("7.7880")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.8556")),
                    },
                ],
                "clicks": 15,
                "impressions": 100,
            },
        )

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    @mock.patch("django.conf.settings.SOURCE_GROUPS", {80: [82, 83, 84], 81: [85, 86]})
    def test_get_ad_group_sources_stats_source_groups(self, mock_k1_get):
        self.agency.uses_source_groups = True
        self.agency.save(None)

        sources = magic_mixer.cycle(8).blend(
            core.models.Source, bidder_slug=magic_mixer.RANDOM, id=(i for i in range(80, 88))
        )
        magic_mixer.cycle(8).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": 2.0},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
                {"source_slug": sources[2].bidder_slug, "spend": 4.0},
                {"source_slug": sources[3].bidder_slug, "spend": 5.0},
                {"source_slug": sources[4].bidder_slug, "spend": 6.0},
                {"source_slug": sources[5].bidder_slug, "spend": 7.0},
                {"source_slug": sources[6].bidder_slug, "spend": 8.0},
                {"source_slug": sources[7].bidder_slug, "spend": 9.0},
            ],
            "clicks": 15,
            "impressions": 100,
            "errors": {},
        }

        result = service.get_ad_group_sources_stats(self.ad_group)

        self.assertEqual(
            result,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("38.9399")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("36.7765")),
                    },
                    {
                        "source_slug": sources[7].bidder_slug,
                        "source": sources[7],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("19.4699")),
                    },
                ],
                "clicks": 15,
                "impressions": 100,
            },
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, {})

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_with_source_tz_today(self, mock_k1_get):
        mock_k1_get.return_value = {"spend": [], "clicks": 15, "impressions": 100, "errors": {}}
        budgets_tz = pytz.timezone("America/Los_Angeles")
        utc_today = dates_helper.utc_today()
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            tz_now = budgets_tz.localize(datetime.datetime(utc_today.year, utc_today.month, utc_today.day, 0))
            mock_utc_now.return_value = tz_now.astimezone(pytz.utc)
            service.get_ad_group_sources_stats(self.ad_group)

            expected_params = dict({})
            mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_with_source_tz_yesterday(self, mock_k1_get):
        mock_k1_get.return_value = {"spend": [], "clicks": 15, "impressions": 100, "errors": {}}
        budgets_tz = pytz.timezone("America/Los_Angeles")
        utc_today = dates_helper.utc_today()
        utc_yesterday = dates_helper.day_before(utc_today)
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            tz_now = budgets_tz.localize(
                datetime.datetime(utc_yesterday.year, utc_yesterday.month, utc_yesterday.day, 23)
            )
            mock_utc_now.return_value = tz_now.astimezone(pytz.utc)
            service.get_ad_group_sources_stats(self.ad_group)

            expected_params = dict({})
            mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats_spend")
    def test_get_ad_group_sources_stats_without_cache(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "spend": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
            ],
            "errors": {},
        }

        result = service.get_ad_group_sources_stats_without_caching(self.ad_group)
        self.assertEqual(
            result,
            {
                "spend": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("6.4900")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.3797")),
                    },
                ],
                "errors": {},
            },
        )

        expected_params = dict({}, **{"no_cache": True})
        mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("dash.features.realtimestats.service.metrics_compat")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_exception(self, mock_k1_get, mock_logger, mock_metrics_compat):
        e = Exception("test")
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual({"spend": [], "clicks": 0, "impressions": 0}, result)

        mock_logger.exception.assert_called_once_with(e)
        mock_metrics_compat.incr.assert_called_once_with("dash.realtimestats.error", 1, type="exception")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats_spend")
    def test_k1_exception_without_caching(self, mock_k1_get):
        e = Exception("test")
        mock_k1_get.side_effect = e

        with self.assertRaises(Exception) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertIs(e, cm.exception)

    @mock.patch("dash.features.realtimestats.service.metrics_compat")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_http_exception(self, mock_k1_get, mock_logger, mock_metrics_compat):
        e = urllib.error.HTTPError("url", 400, "msg", None, None)
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual({"spend": [], "clicks": 0, "impressions": 0}, result)

        mock_logger.exception.assert_not_called()
        mock_metrics_compat.incr.assert_called_once_with("dash.realtimestats.error", 1, type="http", status="400")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats_spend")
    def test_k1_http_exception_without_caching(self, mock_k1_get):
        e = urllib.error.HTTPError("url", 400, "msg", None, None)
        mock_k1_get.side_effect = e

        with self.assertRaises(urllib.error.HTTPError) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertEqual(e, cm.exception)

    @mock.patch("dash.features.realtimestats.service.metrics_compat")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_ioerror_exception(self, mock_k1_get, mock_logger, mock_metrics_compat):
        e = IOError()
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual({"spend": [], "clicks": 0, "impressions": 0}, result)

        mock_logger.exception.assert_not_called()
        mock_metrics_compat.incr.assert_called_once_with("dash.realtimestats.error", 1, type="ioerror")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats_spend")
    def test_k1_ioerror_exception_without_caching(self, mock_k1_get):
        e = IOError()
        mock_k1_get.side_effect = e

        with self.assertRaises(IOError) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertEqual(e, cm.exception)
