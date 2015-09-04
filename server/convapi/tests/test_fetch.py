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
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            }
        ]

        self.assertEqual(expected, conversion_pairs)

    def test_fetch_nonexisting_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'nonexisting',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_nonexisting_contentad(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 99899,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_multiple_touchpoints(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                }, {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            }, {
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'content_ad_id': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'content_ad_id': 2,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12346',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'impression_id': '12346',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'impression_id': '12346',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impression_id': '12345',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54321',
                    'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                    'account_id': 1,
                    'source': 'outbrain',
                    'content_ad_id': 1,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impression_id': '12346',
                    'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                    'click_id': '54322',
                    'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                    'account_id': 1,
                    'source': 'yahoo',
                    'content_ad_id': 2,
                }
            ]
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'impression_id': '12345',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'impression_id': '12346',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                'click_id': '54321',
                'click_timestamp': datetime.datetime(2015, 9, 2, 17),
                'account_id': 1,
                'source': 'outbrain',
                'content_ad_id': 1,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'impression_id': '12346',
                'impression_timestamp': datetime.datetime(2015, 9, 2, 18),
                'click_id': '54322',
                'click_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'source': 'yahoo',
                'content_ad_id': 2,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)
