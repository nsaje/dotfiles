import os

from django.conf import settings
from django.test import TestCase
from mock import patch

from dash import constants

from . import rds_materialization


class RDSAgencyTest(TestCase):
    fixtures = ["test_models"]

    def test_get_queryset(self):
        rds_agency = rds_materialization.RDSAgency()
        rds_qs = rds_agency._get_rds_queryset()
        self.assertEqual(1, rds_qs.count())
        self.assertEqual(
            rds_qs.first(),
            {
                "cs_representative": "mad.max@zemanta.com",
                "default_account_type": "Unknown",
                "id": 1,
                "name": "test agency 1",
                "ob_representative": "supertestuser@test.com",
                "sales_representative": "luka.silovinac@zemanta.com",
                "whitelabel": "Green Park Content",
            },
        )

    def test_make_case_with_constant(self):
        rds_agency = rds_materialization.RDSAgency()
        case = rds_agency.get_constant_value("default_account_type", constants.AccountType)
        self.assertEqual(
            str(case),
            "CASE WHEN <Q: (AND: ('default_account_type', 1))> THEN Value(Unknown), WHEN <Q: (AND: ('default_account_type', 2))> THEN Value(Test), WHEN <Q: (AND: ('default_account_type', 3))> THEN Value(Sandbox), WHEN <Q: (AND: ('default_account_type', 4))> THEN Value(Pilot), WHEN <Q: (AND: ('default_account_type', 5))> THEN Value(Activated), WHEN <Q: (AND: ('default_account_type', 6))> THEN Value(Managed), WHEN <Q: (AND: ('default_account_type', 7))> THEN Value(PAAS), ELSE Value(None)",  # noqa
        )

    def test_put_csv_to_S3(self):
        rds_agency = rds_materialization.RDSAgency()
        s3_path = rds_agency.put_csv_to_s3()
        self.assertEqual(s3_path, "rds-materialization/agency.csv")
        local_path = "{}/agency.csv".format(settings.FILE_STORAGE_DIR)
        self.assertTrue(os.path.isfile(local_path))
        csv_open = os.open(local_path, os.O_RDONLY)
        self.assertEqual(
            os.read(csv_open, 500),
            "1\ttest agency 1\tGreen Park Content\tUnknown\tluka.silovinac@zemanta.com\tmad.max@zemanta.com\tsupertestuser@test.com\r\n".encode(),  # noqa
        )

    @patch("etl.redshift.prepare_copy_query")
    @patch("redshiftapi.db.get_write_stats_cursor")
    @patch("redshiftapi.db.get_write_stats_transaction")
    @patch("etl.redshift.delete_from_table")
    def test_insert_csv_to_stats_db(self, mock_delete, mock_transaction, mock_stats, mock_prepare_copy_query):
        mock_prepare_copy_query.return_value = None, None
        rds_agency = rds_materialization.RDSAgency()
        rds_agency.load_csv_from_s3()
        mock_prepare_copy_query.assert_called_with(
            "rds-materialization/agency.csv",
            "mv_rds_agency",
            null_as="$NA$",
            bucket_name="prodops-test",
            truncate_columns=True,
        )
