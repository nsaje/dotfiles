import datetime

from django.test import TestCase
import mock

from convapi import fetch
import dash.models


@mock.patch('convapi.fetch.redirector_helper.fetch_redirects_impressions')
class FetchTouchpointsImpressionsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        # TODO: move to fixtures ??
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug'
        )
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug2'
        )
        dash.models.ContentAd.objects.get(id=1)

    def test_fetch(self, redirector_fetch_mock):
        self.maxDiff = None
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            }
        ]

        self.assertEqual(expected, conversion_pairs)

    def test_fetch_nonexisting_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'nonexisting',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_nonexisting_contentad(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 99899,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_multiple_touchpoints(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }, {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            }, {
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 1,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 1,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'accountId': 1,
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'accountId': 1,
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'accountId': 1,
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'accountId': 1,
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 17),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 1,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'accountId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54322',
                    'redirectTimestamp': '2015-09-01T18:00:00Z',
                    'accountId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = fetch.process_touchpoint_conversions(datetime.date(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.date(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'source_id': 5,
                'content_ad_id': 2,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 17),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)
