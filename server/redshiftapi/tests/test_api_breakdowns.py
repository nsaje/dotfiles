import backtosql
import mock

from utils import exc

from django.test import TestCase

from redshiftapi import api_breakdowns
from redshiftapi import models


class APIBreakdownsTest(TestCase, backtosql.TestSQLMixin):

    def test_prepare_query_select_time(self):

        with mock.patch('redshiftapi.queries.prepare_time_top_rows') as mock_prepare:
            m = models.MVMaster()
            api_breakdowns._prepare_query(
                m, ['account_id', 'week'], {}, None, 'clicks', None, None
            )

            mock_prepare.assert_called_with(m, 'week', mock.ANY, {})

        with mock.patch('redshiftapi.queries.prepare_time_top_rows') as mock_prepare:
            m = models.MVMaster()
            api_breakdowns._prepare_query(
                m, ['account_id', 'day'], {}, None, 'impressions', None, None
            )

            mock_prepare.assert_called_with(m, 'day', mock.ANY, {})

    def test_prepare_query_structure_and_delivery(self):

        with mock.patch('redshiftapi.queries.prepare_breakdown_struct_delivery_top_rows') as mock_prepare:
            m = models.MVMaster()
            api_breakdowns._prepare_query(
                m, ['account_id', 'campaign_id'], {}, None, 'clicks', None, None
            )

            self.assertTrue(mock_prepare.called)

        with mock.patch('redshiftapi.queries.prepare_breakdown_struct_delivery_top_rows') as mock_prepare:
            m = models.MVMaster()
            api_breakdowns._prepare_query(
                m, ['account_id', 'campaign_id', 'dma'], {}, None, 'clicks', None, None
            )

            self.assertTrue(mock_prepare.called)

    def test_prepare_query_invalid_breakdown(self):

        with self.assertRaises(exc.InvalidBreakdownError):
            m = models.MVMaster()
            api_breakdowns._prepare_query(
                m, [
                    'account_id', 'campaign_id', 'content_ad_id', 'source_id'
                ], {}, None, 'clicks', None, None
            )

        with self.assertRaises(exc.InvalidBreakdownError):
            m = models.MVMaster()

            # len 1 breakdown not yet supported
            api_breakdowns._prepare_query(
                m, ['account_id'], {}, None, 'clicks', None, None
            )
