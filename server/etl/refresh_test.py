import datetime

import mock
from django.test import TestCase

import dash.models
from etl import materialize
from etl import redshift
from etl import refresh
from utils import dates_helper


class RefreshTest(TestCase):
    def setUp(self):
        self.tmp_MATERIALIZED_VIEWS = materialize.MATERIALIZED_VIEWS

    def tearDown(self):
        materialize.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS

    @mock.patch("etl.maintenance.vacuum", mock.Mock())
    @mock.patch("etl.maintenance.analyze", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2000, 1, 1)))
    @mock.patch("utils.slack.publish")
    @mock.patch("etl.daily_statements.get_effective_spend")
    @mock.patch("etl.daily_statements.reprocess_daily_statements")
    @mock.patch("etl.refresh.generate_job_id", return_value="asd")
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh(self, mock_generate_job_id, mock_reprocess, mock_geteffspend, mock_slack):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_geteffspend.return_value = effective_spend_factors

        materialize.MATERIALIZED_VIEWS = [mock_mat_view]

        refresh.refresh(datetime.datetime(2016, 5, 10))

        mock_mat_view.assert_called_with("asd", datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), account_id=None)

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_slack.assert_has_calls(
            (
                mock.call(
                    "Materialization since 2016-05-10 *started*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
                mock.call(
                    "Materialization since 2016-05-10 *finished*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
            )
        )
        mock_reprocess.assert_called()

    @mock.patch("etl.maintenance.vacuum", mock.Mock())
    @mock.patch("etl.maintenance.analyze", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2000, 1, 1)))
    @mock.patch("utils.slack.publish")
    @mock.patch("etl.daily_statements.get_effective_spend")
    @mock.patch("etl.daily_statements.reprocess_daily_statements")
    @mock.patch("etl.refresh.generate_job_id", return_value="asd")
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh_skip_daily_statements(self, mock_generate_job_id, mock_reprocess, mock_geteffspend, mock_slack):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_geteffspend.return_value = effective_spend_factors

        materialize.MATERIALIZED_VIEWS = [mock_mat_view]

        refresh.refresh(datetime.datetime(2016, 5, 10), skip_daily_statements=True)

        mock_mat_view.assert_called_with("asd", datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), account_id=None)

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_slack.assert_has_calls(
            (
                mock.call(
                    "Materialization since 2016-05-10 *started*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
                mock.call(
                    "Materialization since 2016-05-10 *finished*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
            )
        )
        mock_reprocess.assert_not_called()

    @mock.patch("etl.redshift.unload_table")
    @mock.patch("etl.maintenance.vacuum", mock.Mock())
    @mock.patch("etl.maintenance.analyze", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2000, 1, 1)))
    @mock.patch("utils.slack.publish", mock.Mock())
    @mock.patch("etl.daily_statements.get_effective_spend")
    @mock.patch("etl.daily_statements.reprocess_daily_statements")
    @mock.patch("etl.refresh.generate_job_id", return_value="asd")
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh_dump_and_abort(self, mock_generate_job_id, mock_reprocess, mock_geteffspend, mock_unload):
        mock_mat_view1 = mock.MagicMock()
        mock_mat_view1.TABLE_NAME = "abort_this"
        mock_mat_view2 = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_geteffspend.return_value = effective_spend_factors

        materialize.MATERIALIZED_VIEWS = [mock_mat_view1, mock_mat_view2]

        with self.assertRaises(SystemExit):
            refresh.refresh(datetime.datetime(2016, 5, 10), dump_and_abort="abort_this")

        mock_mat_view1.assert_called_with(
            "asd", datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), account_id=None
        )
        mock_mat_view2.assert_not_called()

        mock_unload.assert_called_once_with(
            "asd", "abort_this", datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), prefix=redshift.DUMP_S3_PREFIX
        )

    @mock.patch("utils.slack.publish", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2016, 5, 15)))
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh_update_since(self):
        with self.assertRaises(Exception):
            refresh.refresh(datetime.datetime(2016, 5, 10), 1000)


class RefreshByAccountTest(TestCase):
    fixtures = ["test_materialize_views.yaml"]

    def setUp(self):
        self.tmp_MATERIALIZED_VIEWS = materialize.MATERIALIZED_VIEWS

    def tearDown(self):
        materialize.MATERIALIZED_VIEWS = self.tmp_MATERIALIZED_VIEWS

    @mock.patch("etl.maintenance.vacuum", mock.Mock())
    @mock.patch("etl.maintenance.analyze", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2000, 1, 1)))
    @mock.patch("utils.slack.publish")
    @mock.patch("etl.daily_statements.get_effective_spend")
    @mock.patch("etl.daily_statements.reprocess_daily_statements")
    @mock.patch("etl.refresh.generate_job_id", return_value="asd")
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh(self, mock_generate_job_id, mock_reprocess, mock_geteffspend, mock_slack):
        mock_mat_view = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_geteffspend.return_value = effective_spend_factors

        materialize.MATERIALIZED_VIEWS = [mock_mat_view]

        refresh.refresh(datetime.datetime(2016, 5, 10), account_id=1)

        mock_mat_view.assert_called_with("asd", datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), account_id=1)

        mock_mat_view().generate.assert_called_with(campaign_factors=effective_spend_factors)
        mock_slack.assert_has_calls(
            (
                mock.call(
                    "Materialization since 2016-05-10 for *account 1* *started*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
                mock.call(
                    "Materialization since 2016-05-10 for *account 1* *finished*.",
                    msg_type=":information_source:",
                    username="Refresh k1",
                ),
            )
        )

    @mock.patch("utils.slack.publish", mock.Mock())
    @mock.patch("etl.maintenance.stats_min_date", mock.Mock(return_value=datetime.date(2000, 1, 1)))
    @mock.patch("etl.maintenance.check_existing_data_by_hours", mock.Mock(return_value=24))
    def test_refresh_account_validate(self):
        with self.assertRaises(dash.models.Account.DoesNotExist):
            refresh.refresh(datetime.datetime(2016, 5, 10), 1000)


class EtlBooksTests(TestCase):
    @mock.patch("etl.refresh._refresh", mock.Mock())
    @mock.patch("utils.slack.publish", mock.Mock())
    @mock.patch("etl.maintenance.check_existing_data_by_hours")
    @mock.patch("etl.materialization_run.write_etl_books_status")
    def test_write_etl_books_status(self, mock_write_etl_books_status, mock_check_existing_data_by_hours):
        mock_check_existing_data_by_hours.return_value = 24
        refresh.refresh(datetime.datetime(2016, 5, 10))
        mock_write_etl_books_status.assert_called_with(True, dates_helper.local_yesterday())

        mock_check_existing_data_by_hours.return_value = 22
        refresh.refresh(datetime.datetime(2016, 5, 10))
        mock_write_etl_books_status.assert_called_with(False, dates_helper.local_yesterday())

    @mock.patch("etl.maintenance.check_existing_data_by_hours")
    def test_check_if_yesterdays_data_exists(self, mock_check_existing_data_by_hours):
        mock_check_existing_data_by_hours.return_value = 24

        data_complete, date = refresh._check_if_yesterdays_data_exists()
        self.assertEqual(data_complete, True)
        self.assertEqual(date, dates_helper.local_yesterday())

        mock_check_existing_data_by_hours.return_value = 23
        data_complete, date = refresh._check_if_yesterdays_data_exists()
        self.assertEqual(data_complete, False)
