import datetime
import mock

from django.test import TestCase
import dash.models

from etl import refresh_k1


class RefreshTest(TestCase):

    def setUp(self):
        self.tmp_MATERIALIZED_VIEWS = refresh_k1.MATERIALIZED_VIEWS

    def tearDown(self):
        refresh_k1.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS

    @mock.patch('etl.maintenance.vacuum', mock.Mock())
    @mock.patch('etl.maintenance.analyze', mock.Mock())
    @mock.patch('utils.slack.publish')
    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    @mock.patch('etl.refresh_k1.generate_job_id', return_value='asd')
    def test_refresh_k1_reports(self, mock_generate_job_id, mock_reprocess, mock_slack):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.MATERIALIZED_VIEWS = [mock_mat_view]

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10))

        mock_mat_view.assert_called_with(
            'asd',
            datetime.date(2016, 5, 10),
            datetime.date(2016, 5, 13),
            account_id=None
        )

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_slack.assert_has_calls((
            mock.call('Materialization since 2016-05-10 *started*.',
                      msg_type=':information_source:', username='Refresh k1'),
            mock.call('Materialization since 2016-05-10 *finished*.',
                      msg_type=':information_source:', username='Refresh k1'),
        ))


class RefreshByAccountTest(TestCase):
    fixtures = ['test_materialize_views.yaml']

    def setUp(self):
        self.tmp_MATERIALIZED_VIEWS = refresh_k1.MATERIALIZED_VIEWS

    def tearDown(self):
        refresh_k1.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS

    @mock.patch('etl.maintenance.vacuum', mock.Mock())
    @mock.patch('etl.maintenance.analyze', mock.Mock())
    @mock.patch('utils.slack.publish')
    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    @mock.patch('etl.refresh_k1.generate_job_id', return_value='asd')
    def test_refresh_k1_reports(self, mock_generate_job_id, mock_reprocess, mock_slack):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.MATERIALIZED_VIEWS = [mock_mat_view]

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10), account_id=1)

        mock_mat_view.assert_called_with(
            'asd',
            datetime.date(2016, 5, 10),
            datetime.date(2016, 5, 13),
            account_id=1
        )

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_slack.assert_has_calls((
            mock.call('Materialization since 2016-05-10 for *account 1* *started*.',
                      msg_type=':information_source:', username='Refresh k1'),
            mock.call('Materialization since 2016-05-10 for *account 1* *finished*.',
                      msg_type=':information_source:', username='Refresh k1'),
        ))

    @mock.patch('utils.slack.publish', mock.Mock())
    def test_refresh_k1_account_validate(self):
        with self.assertRaises(dash.models.Account.DoesNotExist):
            refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10), 1000)
