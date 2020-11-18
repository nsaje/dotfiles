import datetime

from django.test import TestCase

import etl.materialization_run
import etl.models
import utils.dates_helper
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

    def test_get_last_books_closed_date(self):
        today = utils.dates_helper.local_today()
        yesterday = utils.dates_helper.local_yesterday()
        last_week = today - datetime.timedelta(days=7)
        magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=True, date=last_week)
        latest_closed_entry = magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=True, date=yesterday)
        magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=False, date=today)
        magic_mixer.blend(etl.models.EtlBooksClosed, etl_books_closed=False, date=today)
        self.assertEqual(latest_closed_entry.date, etl.materialization_run.get_last_books_closed_date())
