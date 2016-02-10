import datetime
import mock

from django.test import TestCase

from convapi import process
import dash.models
from utils import dates_helper


class UpdateTouchpointConversionsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.cp1 = dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug',
            last_sync_dt=dates_helper.local_to_utc_time(datetime.datetime(2015, 9, 8, process.ADDITIONAL_SYNC_HOURS)),
        )
        self.cp2 = dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug2',
            last_sync_dt=None
        )

    @mock.patch('convapi.process.update_touchpoint_conversions')
    @mock.patch('utils.dates_helper.datetime')
    def test_update_full(self, datetime_mock, update_touchpoint_conversions_mock):
        datetime_mock.datetime = mock.Mock()
        datetime_mock.datetime.utcnow = mock.Mock()
        datetime_mock.datetime.utcnow.return_value = dates_helper.local_to_utc_time(
            datetime.datetime(2015, 9, 10, process.ADDITIONAL_SYNC_HOURS + 1))
        datetime_mock.timedelta = datetime.timedelta

        process.update_touchpoint_conversions_full()

        expected_args = dict([(datetime.date(2015, 9, 8), [self.cp1]),
                              (datetime.date(2015, 9, 9), [self.cp1]),
                              (datetime.date(2015, 9, 10), [self.cp1, self.cp2])])

        self.assertEqual(update_touchpoint_conversions_mock.call_count, 1)
        self.assertEqual(dict(update_touchpoint_conversions_mock.call_args[0][0]), expected_args)

    @mock.patch('convapi.process.update_touchpoint_conversions')
    @mock.patch('utils.dates_helper.datetime')
    def test_update_full_additional_sync(self, datetime_mock, update_touchpoint_conversions_mock):
        datetime_mock.datetime = mock.Mock()
        datetime_mock.datetime.utcnow = mock.Mock()
        datetime_mock.datetime.utcnow.return_value = dates_helper.local_to_utc_time(
            datetime.datetime(2015, 9, 10, process.ADDITIONAL_SYNC_HOURS + 1))
        datetime_mock.timedelta = datetime.timedelta

        dash.models.ConversionPixel.objects.filter(slug='test_slug2').update(last_sync_dt=datetime.datetime(2015, 9, 8))

        process.update_touchpoint_conversions_full()

        expected_args = dict([(datetime.date(2015, 9, 8), [self.cp1, self.cp2]),
                             (datetime.date(2015, 9, 9), [self.cp1, self.cp2]),
                             (datetime.date(2015, 9, 10), [self.cp1, self.cp2]),
                             (datetime.date(2015, 9, 7), [self.cp2])])

        self.assertEqual(update_touchpoint_conversions_mock.call_count, 1)
        self.assertEqual(dict(update_touchpoint_conversions_mock.call_args[0][0]), expected_args)


class ProcessTouchpointsImpressionsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug'
        )
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug2'
        )

    def test_process(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                    'adLookup': False,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)
        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_id': '54321',
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

    def test_process_ad_lookup(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                    'adLookup': True,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)
        expected = []

        self.assertEqual(expected, conversion_pairs)

    def test_process_source_slug_z1(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'z1',
                    'contentAdId': 1,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)
        expected = []

        self.assertEqual(expected, conversion_pairs)

    def test_process_simple_redirect(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 0,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)
        expected = []

        self.assertEqual(expected, conversion_pairs)

    def test_process_archived_pixel(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }
            ]
        }

        px = dash.models.ConversionPixel.objects.get(account_id=1, slug='test_slug')
        px.archived = True
        px.save()

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        self.assertEqual([], conversion_pairs)

    def test_process_nonexisting_slug(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'nonexisting',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        self.assertEqual([], conversion_pairs)

    def test_process_nonexisting_contentad(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 99899,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        self.assertEqual([], conversion_pairs)

    def test_process_multiple_touchpoints(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_id': '54321',
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
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 22,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_process_multiple_impressions_same_slug(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
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
                    'adGroupId': 1,
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
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_id': '54321',
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
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 22,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_process_multiple_subsequent_pairs_same_slug(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'accountId': 1,
                    'redirectId': '54323',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'accountId': 1,
                    'redirectId': '54323',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_id': '54323',
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
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 22,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_process_multiple_impressions_different_slug(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54321',
                    'redirectTimestamp': '2015-09-02T15:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
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
                    'adGroupId': 1,
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
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        self.maxDiff = None
        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_id': '54321',
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
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 22,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_id': '54321',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 2, 15),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'source_id': 3,
                'conversion_lag': 3,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 24,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_process_multiple_subsequent_pairs_different_slug(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54323',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                },
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug2',
                    'impressionId': '12346',
                    'impressionTimestamp': '2015-09-02T18:00:00Z',
                    'redirectId': '54323',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
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
                    'adGroupId': 1,
                    'source': 'yahoo',
                    'contentAdId': 2,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        expected = [
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12345',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 15, 15, 15),
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'source_id': 5,
                'content_ad_id': 2,
                'conversion_lag': 22,
            },
            {
                'zuid': '1234-12345-123456',
                'slug': 'test_slug2',
                'date': datetime.date(2015, 9, 2),
                'conversion_id': '12346',
                'conversion_timestamp': datetime.datetime(2015, 9, 2, 18),
                'touchpoint_id': '54323',
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
                'touchpoint_id': '54322',
                'touchpoint_timestamp': datetime.datetime(2015, 9, 1, 18),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 2,
                'source_id': 5,
                'conversion_lag': 24,
            }
        ]

        self.assertItemsEqual(expected, conversion_pairs)

    def test_process_bad_pixie(self):
        redirects_impressions = {
            '1234-12345-123456': [
                {
                    'zuid': '1234-12345-123456',
                    'slug': 'test_slug',
                    'impressionId': '12345',
                    'impressionTimestamp': '2015-09-02T15:15:15Z',
                    'redirectId': '54323',
                    'redirectTimestamp': '2015-09-02T17:00:00Z',
                    'accountId': 1,
                    'adGroupId': 1,
                    'source': 'outbrain',
                    'contentAdId': 1,
                }
            ]
        }

        conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)

        self.assertItemsEqual([], conversion_pairs, "Conversion pair should have been filtered out by BAD_PIXIE check")
