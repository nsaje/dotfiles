import datetime
import decimal
import urllib.error
import urllib.parse
import urllib.request

import mock
import pytz
from django.test import TestCase

import core.features.yahoo_accounts
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
        self.yahoo_account = magic_mixer.blend(
            core.features.yahoo_accounts.YahooAccount, budgets_tz="America/Los_Angeles", advertiser_id="test"
        )
        self.account = magic_mixer.blend(core.models.Account, uses_bcm_v2=True, yahoo_account=self.yahoo_account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group_sources = magic_mixer.cycle(len(ad_group_sources)).blend(
            core.models.AdGroupSource,
            ad_group=self.ad_group,
            ad_review_only=False,
            source__source_type__type=(ags["type"] for ags in ad_group_sources),
            source_campaign_key=(ags["source_campaign_key"] for ags in ad_group_sources),
        )
        self.expected_params = {
            "outbrain_campaign_id": "test_outbrain_1",
            "yahoo_campaign_id": "test_yahoo_1",
            "yahoo_advertiser_id": "test",
        }

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
            flat_fee_cc=0,
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

    @mock.patch("utils.redirector_helper.get_adgroup_realtimestats")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_stats(self, mock_k1_get, mock_redirector_get):
        mock_k1_get.return_value = {
            "stats": [
                {"spend": 3.0, "source_slug": self.ad_group_sources[0].source.bidder_slug},
                {"spend": 1.1, "source_slug": self.ad_group_sources[1].source.bidder_slug},
            ],
            "errors": {},
        }
        mock_redirector_get.return_value = {"clicks": 13}

        result = service.get_ad_group_stats(self.ad_group)
        self.assertEqual(result, {"clicks": 13, "spend": test_helper.AlmostMatcher(decimal.Decimal("7.8842"))})

        mock_k1_get.assert_called_once_with(self.ad_group.id, self.expected_params)
        mock_redirector_get.assert_called_once_with(self.ad_group.id)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "stats": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
            ],
            "errors": {},
        }

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(
            result,
            [
                {
                    "source_slug": sources[1].bidder_slug,
                    "source": sources[1],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("5.7689")),
                },
                {
                    "source_slug": sources[0].bidder_slug,
                    "source": sources[0],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("2.1153")),
                },
            ],
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, self.expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_only_allowed(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "stats": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
                {"source_slug": "amplify", "spend": 3.0},
            ],
            "errors": {},
        }

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(
            result,
            [
                {
                    "source_slug": sources[1].bidder_slug,
                    "source": sources[1],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("5.7689")),
                },
                {
                    "source_slug": sources[0].bidder_slug,
                    "source": sources[0],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("2.1153")),
                },
            ],
        )

        mock_k1_get.assert_called_once_with(self.ad_group.id, self.expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_multicurrency(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "stats": [
                {"source_slug": sources[0].bidder_slug, "spend": decimal.Decimal("1.1")},
                {"source_slug": sources[1].bidder_slug, "spend": decimal.Decimal("3.0")},
            ],
            "errors": {},
        }

        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__currency=dash.constants.Currency.EUR)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=ad_group, source=(s for s in sources), ad_review_only=False
        )
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            date=dates_helper.local_today(), currency=dash.constants.Currency.EUR, exchange_rate=decimal.Decimal("1.2")
        )
        result = service.get_ad_group_sources_stats(ad_group)
        self.assertEqual(
            result,
            [
                {
                    "source_slug": sources[1].bidder_slug,
                    "source": sources[1],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("3.0")),
                },
                {
                    "source_slug": sources[0].bidder_slug,
                    "source": sources[0],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("1.1")),
                },
            ],
        )
        mock_k1_get.assert_called_once_with(ad_group.id, {})

        result_local = service.get_ad_group_sources_stats(ad_group, use_local_currency=True)
        self.assertEqual(
            result_local,
            [
                {
                    "source_slug": sources[1].bidder_slug,
                    "source": sources[1],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("3.6")),
                },
                {
                    "source_slug": sources[0].bidder_slug,
                    "source": sources[0],
                    "spend": test_helper.AlmostMatcher(decimal.Decimal("1.32")),
                },
            ],
        )

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_with_source_tz_today(self, mock_k1_get):
        mock_k1_get.return_value = {"stats": [], "errors": {}}
        budgets_tz = self.yahoo_account.budgets_tz
        utc_today = dates_helper.utc_today()
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            tz_now = budgets_tz.localize(datetime.datetime(utc_today.year, utc_today.month, utc_today.day, 0))
            mock_utc_now.return_value = tz_now.astimezone(pytz.utc)
            service.get_ad_group_sources_stats(self.ad_group, use_source_tz=True)

            expected_params = dict(self.expected_params)
            expected_params["yahoo_date"] = utc_today.isoformat()
            mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_with_source_tz_yesterday(self, mock_k1_get):
        mock_k1_get.return_value = {"stats": [], "errors": {}}
        budgets_tz = self.yahoo_account.budgets_tz
        utc_today = dates_helper.utc_today()
        utc_yesterday = dates_helper.day_before(utc_today)
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            tz_now = budgets_tz.localize(
                datetime.datetime(utc_yesterday.year, utc_yesterday.month, utc_yesterday.day, 23)
            )
            mock_utc_now.return_value = tz_now.astimezone(pytz.utc)
            service.get_ad_group_sources_stats(self.ad_group, use_source_tz=True)

            expected_params = dict(self.expected_params)
            expected_params["yahoo_date"] = utc_yesterday.isoformat()
            mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_get_ad_group_sources_stats_without_cache(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=(s for s in sources), ad_review_only=False
        )
        mock_k1_get.return_value = {
            "stats": [
                {"source_slug": sources[0].bidder_slug, "spend": 1.1},
                {"source_slug": sources[1].bidder_slug, "spend": 3.0},
            ],
            "errors": {},
        }

        result = service.get_ad_group_sources_stats_without_caching(self.ad_group)
        self.assertEqual(
            result,
            {
                "stats": [
                    {
                        "source_slug": sources[1].bidder_slug,
                        "source": sources[1],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("5.7689")),
                    },
                    {
                        "source_slug": sources[0].bidder_slug,
                        "source": sources[0],
                        "spend": test_helper.AlmostMatcher(decimal.Decimal("2.1153")),
                    },
                ],
                "errors": {},
            },
        )

        expected_params = dict(self.expected_params, **{"no_cache": True})
        mock_k1_get.assert_called_once_with(self.ad_group.id, expected_params)

    @mock.patch("dash.features.realtimestats.service.influx")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = Exception("test")
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_called_once_with(e)
        mock_influx.incr.assert_called_once_with("dash.realtimestats.error", 1, type="exception")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_exception_without_caching(self, mock_k1_get):
        e = Exception("test")
        mock_k1_get.side_effect = e

        with self.assertRaises(Exception) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertIs(e, cm.exception)

    @mock.patch("dash.features.realtimestats.service.influx")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_http_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = urllib.error.HTTPError("url", 400, "msg", None, None)
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_not_called()
        mock_influx.incr.assert_called_once_with("dash.realtimestats.error", 1, type="http", status="400")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_http_exception_without_caching(self, mock_k1_get):
        e = urllib.error.HTTPError("url", 400, "msg", None, None)
        mock_k1_get.side_effect = e

        with self.assertRaises(urllib.error.HTTPError) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertEqual(e, cm.exception)

    @mock.patch("dash.features.realtimestats.service.influx")
    @mock.patch("dash.features.realtimestats.service.logger")
    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_ioerror_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = IOError()
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_not_called()
        mock_influx.incr.assert_called_once_with("dash.realtimestats.error", 1, type="ioerror")

    @mock.patch("utils.k1_helper.get_adgroup_realtimestats")
    def test_k1_ioerror_exception_without_caching(self, mock_k1_get):
        e = IOError()
        mock_k1_get.side_effect = e

        with self.assertRaises(IOError) as cm:
            service.get_ad_group_sources_stats_without_caching(self.ad_group)
            self.assertEqual(e, cm.exception)
