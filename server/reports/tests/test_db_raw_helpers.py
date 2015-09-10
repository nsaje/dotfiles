from mock import Mock

from django.test import TestCase

from reports import db_raw_helpers


class DbRawHelpersTest(TestCase):
    def test_dictfetchall(self):
        mock_cursor = Mock()
        mock_cursor.description = ['foo', 'bar']
        mock_cursor.fetchall.return_value = [['a', 1]]

        result = db_raw_helpers.dictfetchall(mock_cursor)

        self.assertEqual(result, [{'b': 1, 'f': 'a'}])
