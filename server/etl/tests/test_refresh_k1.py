import datetime
import mock

from django.test import TestCase
import dash.models

from etl import refresh_k1


class RefreshTest(TestCase):

    def setUp(self):
        self.tmp_NEW_MATERIALIZED_VIEWS = refresh_k1.NEW_MATERIALIZED_VIEWS
        self.tmp_MATERIALIZED_VIEWS = refresh_k1.MATERIALIZED_VIEWS
        self.tmp_ALL_MATERIALIZED_VIEWS = refresh_k1.ALL_MATERIALIZED_VIEWS

    def tearDown(self):
        refresh_k1.NEW_MATERIALIZED_VIEWS = self.tmp_NEW_MATERIALIZED_VIEWS
        refresh_k1.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS
        refresh_k1.ALL_MATERIALIZED_VIEWS = self.tmp_ALL_MATERIALIZED_VIEWS

    @mock.patch('etl.maintenance.crossvalidate_traffic')
    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    @mock.patch('etl.refresh_k1.generate_job_id', return_value='asd')
    def test_refresh_k1_reports(self, mock_generate_job_id, mock_reprocess, mock_crossvalidate):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.ALL_MATERIALIZED_VIEWS = [mock_mat_view]

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10))

        mock_mat_view.assert_called_with(
            'asd',
            datetime.date(2016, 5, 10),
            datetime.date(2016, 5, 13),
            account_id=None
        )

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_crossvalidate.assert_called_with(datetime.date(2016, 5, 10), datetime.date(2016, 5, 13))


class RefreshByAccountTest(TestCase):
    fixtures = ['test_materialize_views.yaml']

    def setUp(self):
        self.tmp_NEW_MATERIALIZED_VIEWS = refresh_k1.NEW_MATERIALIZED_VIEWS
        self.tmp_MATERIALIZED_VIEWS = refresh_k1.MATERIALIZED_VIEWS
        self.tmp_ALL_MATERIALIZED_VIEWS = refresh_k1.ALL_MATERIALIZED_VIEWS

    def tearDown(self):
        refresh_k1.NEW_MATERIALIZED_VIEWS = self.tmp_NEW_MATERIALIZED_VIEWS
        refresh_k1.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS
        refresh_k1.ALL_MATERIALIZED_VIEWS = self.tmp_ALL_MATERIALIZED_VIEWS

    @mock.patch('etl.maintenance.crossvalidate_traffic')
    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    @mock.patch('etl.refresh_k1.generate_job_id', return_value='asd')
    def test_refresh_k1_reports(self, mock_generate_job_id, mock_reprocess, mock_crossvalidate):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.ALL_MATERIALIZED_VIEWS = [mock_mat_view]

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10), account_id=1)

        mock_mat_view.assert_called_with(
            'asd',
            datetime.date(2016, 5, 10),
            datetime.date(2016, 5, 13),
            account_id=1
        )

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_crossvalidate.assert_called_with(datetime.date(2016, 5, 10), datetime.date(2016, 5, 13))

    def test_refresh_k1_account_validate(self):
        with self.assertRaises(dash.models.Account.DoesNotExist):
            refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10), 1000)
