import datetime
import mock

from django.test import TestCase

from etl import refresh_k1


class RefreshTest(TestCase):

    def setUp(self):
        self.tmp_NEW_MATERIALIZED_VIEWS = refresh_k1.NEW_MATERIALIZED_VIEWS
        self.tmp_MATERIALIZED_VIEWS = refresh_k1.MATERIALIZED_VIEWS

    def tearDown(self):
        refresh_k1.NEW_MATERIALIZED_VIEWS = self.tmp_NEW_MATERIALIZED_VIEWS
        refresh_k1.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS

    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    @mock.patch('etl.refresh_k1.generate_job_id', return_value='asd')
    def test_refresh_k1_reports(self, mock_generate_job_id, mock_reprocess):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.MATERIALIZED_VIEWS = [mock_mat_view]
        refresh_k1.NEW_MATERIALIZED_VIEWS = []

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10))

        mock_mat_view.assert_called_with(
            'asd',
            datetime.date(2016, 5, 10),
            datetime.date(2016, 5, 13)
        )

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
