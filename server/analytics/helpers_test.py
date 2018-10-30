import datetime

from django import test
from mock import patch

import analytics.helpers
import dash.models
import zemauth.models


class ManagementReportTestCase(test.TestCase):
    fixtures = ["test_api"]

    @patch("backtosql.generate_sql")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_get_spend_ad_group(self, mock_db, mock_gen):
        date = datetime.date(2017, 3, 1)
        analytics.helpers.get_spend(date, ad_group=dash.models.AdGroup.objects.get(pk=1))
        mock_gen.assert_called_with(
            "sql/helpers_get_spend.sql", {"date": "2017-03-01", "operator": "=", "value": 1, "key": "ad_group"}
        )

    @patch("backtosql.generate_sql")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_get_spend_campaign(self, mock_db, mock_gen):
        date = datetime.date(2017, 3, 1)
        analytics.helpers.get_spend(date, campaign=dash.models.Campaign.objects.get(pk=1))
        mock_gen.assert_called_with(
            "sql/helpers_get_spend.sql", {"date": "2017-03-01", "operator": "=", "value": 1, "key": "campaign"}
        )

    @patch("backtosql.generate_sql")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_get_spend_account(self, mock_db, mock_gen):
        date = datetime.date(2017, 3, 1)
        analytics.helpers.get_spend(date, account=dash.models.Account.objects.get(pk=1))
        mock_gen.assert_called_with(
            "sql/helpers_get_spend.sql", {"date": "2017-03-01", "operator": "=", "value": 1, "key": "account"}
        )

    @patch("backtosql.generate_sql")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_get_spend_agency(self, mock_db, mock_gen):
        class Req:
            pass

        req = Req()
        req.user = zemauth.models.User.objects.get(pk=1)

        agency = dash.models.Agency(pk=1, id=1, name="Test")
        agency.save(req)
        date = datetime.date(2017, 3, 1)

        analytics.helpers.get_spend(date, agency=agency)
        self.assertFalse(mock_gen.called)

        account = dash.models.Account.objects.get(pk=1)
        account.agency_id = agency.pk
        account.save(req)
        analytics.helpers.get_spend(date, agency=agency)
        mock_gen.assert_called_with(
            "sql/helpers_get_spend.sql", {"date": "2017-03-01", "operator": "IN", "value": "(1)", "key": "account"}
        )
