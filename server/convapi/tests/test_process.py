import datetime
import mock

from django.test import TestCase

from convapi import process
import dash.models


class UpdateTouchpointConversionsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug',
            last_sync_dt=datetime.datetime(2015, 9, 8) + datetime.timedelta(hours=process.ADDITIONAL_SYNC_HOURS),
        )
        dash.models.ConversionPixel.objects.create(
            account_id=1,
            slug='test_slug2',
            last_sync_dt=None
        )

    # @mock.patch('convapi.process.redirector_helper')
    # @mock.patch('convapi.process.process_touchpoint_conversions')
    # @mock.patch('convapi.process.reports.update')
    # def test_update(self, mock_reports_update, mock_process_touchpoints_conversions, mock_redirector_helper):
    #     mock_reports_update.update_touchpoints_conversions = mock.Mock()
    #     mock_process_touchpoints_conversions.return_value = [{}, {}]
    #     mock_redirector_helper.fetch_redirects_impressions = mock.Mock()
    #     mock_redirector_helper.fetch_redirects_impressions.return_value = {'abc': [{}, {}]}

    #     dates = [datetime.datetime(2015, 9, 7), datetime.datetime(2015, 9, 8), datetime.datetime(2015, 9, 9)]
    #     process.update_touchpoint_conversions(dates, [1])

    #     mock_redirector_helper.fetch_redirects_impressions.assert_has_calls(
    #         [mock.call(datetime.datetime(2015, 9, 7), 1),
    #          mock.call(datetime.datetime(2015, 9, 8), 1),
    #          mock.call(datetime.datetime(2015, 9, 9), 1)])
    #     mock_process_touchpoints_conversions.assert_has_calls([mock.call({'abc': [{}, {}]}),
    #                                                            mock.call({'abc': [{}, {}]}),
    #                                                            mock.call({'abc': [{}, {}]})])
    #     mock_reports_update.update_touchpoint_conversions.assert_has_calls(
    #         [mock.call(datetime.datetime(2015, 9, 7), 1, [{}, {}]),
    #          mock.call(datetime.datetime(2015, 9, 8), 1, [{}, {}]),
    #          mock.call(datetime.datetime(2015, 9, 9), 1, [{}, {}])]
    #     )

    @mock.patch('convapi.process.update_touchpoint_conversions')
    @mock.patch('convapi.process.datetime')
    def test_update_full(self, datetime_mock, update_touchpoint_conversions_mock):
        datetime_mock.datetime = mock.Mock()
        datetime_mock.datetime.utcnow = mock.Mock()
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2015, 9, 10)
        datetime_mock.timedelta = datetime.timedelta

        process.update_touchpoint_conversions_full()

        conversion_pixels = dash.models.ConversionPixel.objects.all()
        account_ids = set(cp.account_id for cp in conversion_pixels)
        update_touchpoint_conversions_mock.assert_called_once_with([datetime.date(2015, 9, 8),
                                                                    datetime.date(2015, 9, 9),
                                                                    datetime.date(2015, 9, 10)],
                                                                   account_ids)

    @mock.patch('convapi.process.update_touchpoint_conversions')
    @mock.patch('convapi.process.datetime')
    def test_update_full_additional_sync(self, datetime_mock, update_touchpoint_conversions_mock):
        datetime_mock.datetime = mock.Mock()
        datetime_mock.datetime.utcnow = mock.Mock()
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2015, 9, 10)
        datetime_mock.timedelta = datetime.timedelta

        dash.models.ConversionPixel.objects.filter(slug='test_slug2').update(last_sync_dt=datetime.datetime(2015, 9, 8))

        process.update_touchpoint_conversions_full()

        conversion_pixels = dash.models.ConversionPixel.objects.all()
        account_ids = set(cp.account_id for cp in conversion_pixels)
        update_touchpoint_conversions_mock.assert_called_once_with([datetime.date(2015, 9, 7),
                                                                    datetime.date(2015, 9, 8),
                                                                    datetime.date(2015, 9, 9),
                                                                    datetime.date(2015, 9, 10)],
                                                                   account_ids)


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
