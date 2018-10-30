from django.test import TestCase

import backtosql
from etl import models


class ColumnsTest(TestCase, backtosql.TestSQLMixin):
    def test_json_dict_sum(self):
        column = models.K1PostclickStats().conversions

        self.assertSQLEquals(
            column.column_as_alias("T"), "json_dict_sum(listagg(T.conversions, ';'), ';') as conversions"
        )


class MVMasterTest(TestCase):
    def test_get_ordered_aggregates(self):
        # items should be equal, just order can differ
        self.assertCountEqual(models.MVMaster().get_aggregates(), models.MVMaster().get_ordered_aggregates())
