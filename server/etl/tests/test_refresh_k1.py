import datetime
import mock

from django.test import TestCase

from etl import refresh_k1


class RefreshTest(TestCase):

    @mock.patch('etl.daily_statements_k1.reprocess_daily_statements')
    def test_refresh_k1_reports(self, mock_reprocess):
        mock_generate = mock.MagicMock()

        effective_spend_factors = {
            datetime.date(2016, 5, 10): 234,
            datetime.date(2016, 5, 11): 235,
            datetime.date(2016, 5, 12): 236,
            datetime.date(2016, 5, 13): 237,
        }

        mock_reprocess.return_value = effective_spend_factors

        refresh_k1.MATERIALIZED_VIEWS = [mock_generate]

        refresh_k1.refresh_k1_reports(datetime.datetime(2016, 5, 10))

        mock_generate.generate.assert_called_with(
            datetime.date(2016, 5, 10), datetime.date(2016, 5, 13), effective_spend_factors)
