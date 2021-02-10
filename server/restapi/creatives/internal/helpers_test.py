import datetime

import mock
from django.test import TestCase

from . import helpers


class HelpersTestCase(TestCase):
    @mock.patch("utils.dates_helper.local_now")
    def test_generate_batch_name(self, mock_local_now):
        mock_local_now.return_value = datetime.datetime(2021, 2, 3, 10, 25)
        self.assertEqual(helpers.generate_batch_name(), "02/03/2021 10:25 AM")

        mock_local_now.return_value = datetime.datetime(2021, 2, 3, 22, 25)
        self.assertEqual(helpers.generate_batch_name(), "02/03/2021 10:25 PM")
