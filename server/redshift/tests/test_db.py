from mock import Mock

from django.test import TestCase

from redshift import db


class DBTest(TestCase):

    def test_dictfetchall(self):
        mock_cursor = Mock()
        mock_cursor.description = ['foo', 'bar']
        mock_cursor.fetchall.return_value = [['a', 1]]

        result = db.dictfetchall(mock_cursor)

        self.assertEqual(result, [{'b': 1, 'f': 'a'}])
