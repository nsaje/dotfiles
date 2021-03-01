import mock

from utils.base_test_case import BaseTestCase

from . import api


class MockResult:
    def __init__(self, result):
        self.result = result


class GroupByTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch("realtimeapi.api._get_client")
    def test_groupby(self, mock_client):
        row = {
            "version": "v1",
            "timestamp": "2020-11-25T05:00:00.000Z",
            "event": {
                "ctr": 0.009913692558898997,
                "cpm": 0.00046380893655236763,
                "price": 11.930093466,
                "cpc": 0.046784680258823534,
                "clicks": 255,
                "impressions": 25722,
                "price_nano": 11930093466.0,
                "data_price_nano": 0.0,
            },
        }
        mock_client.return_value.groupby.return_value = MockResult(result=[row])

        result = api.groupby(
            breakdown=["ad_group_id"], account_id=10, campaign_id=100, ad_group_id=1000, content_ad_id=10000
        )
        self.assertEqual(1, len(result))
        self.assertEqual(row["event"], result[0])

    def test_invalid_breakdown(self):
        with self.assertRaises(AssertionError):
            api.groupby(breakdown=["agency_id"], account_id=10, campaign_id=100, ad_group_id=1000, content_ad_id=10000)

        with self.assertRaises(AssertionError):
            api.groupby(
                breakdown=["ad_group_id", "campaign_id"],
                account_id=10,
                campaign_id=100,
                ad_group_id=1000,
                content_ad_id=10000,
            )


class CountRowsTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch("realtimeapi.api._get_client")
    def test_count_rows(self, mock_client):
        row = {
            "version": "v1",
            "timestamp": "2020-11-25T05:00:00.000Z",
            "event": {
                "count": 20,
            },
        }
        mock_client.return_value._post.return_value = MockResult(result=[row])

        result = api.count_rows(
            breakdown=["ad_group_id"], account_id=10, campaign_id=100, ad_group_id=1000, content_ad_id=10000
        )
        self.assertEqual(1, len(result))
        self.assertEqual(row["event"], result[0])


class TopNTest(BaseTestCase):
    def setUp(self):
        super().setUp()

    @mock.patch("realtimeapi.api._get_client")
    def test_topn(self, mock_client):
        row = {
            "timestamp": "2020-12-04T05:00:00.000Z",
            "result": [
                {
                    "ctr": 0.0,
                    "cpm": 0.21234573940610046,
                    "spend": 22662.510277597,
                    "cpc": 0.0,
                    "clicks": 0,
                    "publisher": "www.msn.com",
                    "impressions": 106724582,
                    "price_nano": 22658634677597.0,
                    "data_price_nano": 3875600000.0,
                }
            ],
        }
        mock_client.return_value.topn.return_value = MockResult(result=[row])

        result = api.topn(
            breakdown=["ad_group_id"], order="spend", campaign_id=100, ad_group_id=1000, content_ad_id=10000
        )
        self.assertEqual(1, len(result))
        self.assertEqual(row["result"], result)

    def test_invalid_breakdown(self):
        with self.assertRaises(AssertionError):
            api.groupby(breakdown=["agency_id"], campaign_id=100, ad_group_id=1000, content_ad_id=10000)

        with self.assertRaises(AssertionError):
            api.groupby(
                breakdown=["ad_group_id", "campaign_id"], campaign_id=100, ad_group_id=1000, content_ad_id=10000
            )
