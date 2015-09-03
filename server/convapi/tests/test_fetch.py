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
        cp = dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug'
        )
        cp2 = dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug2'
        )

        ca = dash.models.ContentAd.objects.get(id=1)
        ca.ad_group.campaign.conversion_pixels.add(cp, cp2)

    def test_fetch(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15),
                'source': 'outbrain',
                'creative_id': 1,
            }
        )]

        self.assertEqual(expected, conversion_pairs)

    def test_fetch_nonexisting_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'nonexisting',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_nonexisting_contentad(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 99899,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_campaign_not_set_up(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }]
            }
        }

        cp = dash.models.ConversionPixel.objects.get(slug='test_slug')
        cp.campaign_set.clear()

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_max_conversion_window(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15) - datetime.timedelta(
                        days=fetch.MAX_CONVERSION_WINDOW_DAYS, seconds=1),
                    'source': 'outbrain',
                    'creative_id': 1,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        self.assertEqual([], conversion_pairs)

    def test_fetch_multiple_touchpoints(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }, {
                    'click_id': 54322,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'creative_id': 2,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        )]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }, {
                    'conversion_id': 12346,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }, {
                    'click_id': 54322,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'creative_id': 2,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        )]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_same_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }, {
                    'conversion_id': 12346,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 17),
                    'source': 'outbrain',
                    'creative_id': 1,
                }, {
                    'click_id': 54322,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'creative_id': 2,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12346,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 18),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 17),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        )]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_impressions_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }, {
                    'conversion_id': 12346,
                    'slug': 'test_slug2',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15),
                    'source': 'outbrain',
                    'creative_id': 1,
                }, {
                    'click_id': 54322,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'creative_id': 2,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        ), (
            {
                'conversion_id': 12346,
                'slug': 'test_slug2',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 18),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12346,
                'slug': 'test_slug2',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 18),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        )]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_fetch_multiple_subsequent_pairs_different_slug(self, redirector_fetch_mock):
        redirector_fetch_mock.return_value = {
            'abc': {
                'impressions': [{
                    'conversion_id': 12345,
                    'slug': 'test_slug',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                    'account_id': 1,
                }, {
                    'conversion_id': 12346,
                    'slug': 'test_slug2',
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 18),
                    'account_id': 1,
                }],
                'redirects': [{
                    'click_id': 54321,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 2, 17),
                    'source': 'outbrain',
                    'creative_id': 1,
                }, {
                    'click_id': 54322,
                    'zuid': '1234-12345-123456',
                    'timestamp': datetime.datetime(2015, 9, 1, 18),
                    'source': 'yahoo',
                    'creative_id': 2,
                }]
            }
        }

        conversion_pairs = fetch.fetch_touchpoints_impressions(datetime.datetime(2015, 9, 2))
        redirector_fetch_mock.assert_called_with(datetime.datetime(2015, 9, 2))

        expected = [(
            {
                'conversion_id': 12345,
                'slug': 'test_slug',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        ), (
            {
                'conversion_id': 12346,
                'slug': 'test_slug2',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 18),
                'account_id': 1,
            },
            {
                'click_id': 54321,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 17),
                'source': 'outbrain',
                'creative_id': 1,
            }
        ), (
            {
                'conversion_id': 12346,
                'slug': 'test_slug2',
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 2, 18),
                'account_id': 1,
            },
            {
                'click_id': 54322,
                'zuid': '1234-12345-123456',
                'timestamp': datetime.datetime(2015, 9, 1, 18),
                'source': 'yahoo',
                'creative_id': 2,
            }
        )]

        self.assertItemsEqual(expected, conversion_pairs)
