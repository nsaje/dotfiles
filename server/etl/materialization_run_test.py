import datetime

from django.test import TestCase

import etl.materialization_run
import etl.models
from utils.magic_mixer import magic_mixer


class TestEtlDataCompleteForDate(TestCase):
    def test_etl_data_complete_for_date(self):
        self.assertEqual(False, etl.materialization_run.etl_data_complete_for_date(datetime.date(2020, 4, 5)))

        entry = magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=True, date=datetime.date(2020, 4, 5))
        self.assertEqual(True, etl.materialization_run.etl_data_complete_for_date(datetime.date(2020, 4, 5)))

        entry.etl_books_closed = False
        entry.save()
        self.assertEqual(False, etl.materialization_run.etl_data_complete_for_date(datetime.date(2020, 4, 5)))

        magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=True, date=datetime.date(2020, 4, 5))
        self.assertEqual(True, etl.materialization_run.etl_data_complete_for_date(datetime.date(2020, 4, 5)))
