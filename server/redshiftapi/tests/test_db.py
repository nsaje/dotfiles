from mock import Mock

from django.test import TestCase

from redshiftapi import db


class DBTest(TestCase):

    def test_dictfetchall(self):
        mock_cursor = Mock()
        mock_cursor.description = [['foo'], ['bar']]
        mock_cursor.fetchall.return_value = [['a', 1]]

        result = db.dictfetchall(mock_cursor)

        self.assertEqual(result, [{'bar': 1, 'foo': 'a'}])

    def test_namedtuplefetchall(self):
        mock_cursor = Mock()
        mock_cursor.description = [['foo'], ['bar']]
        mock_cursor.fetchall.return_value = [['a', 1]]

        result = db.namedtuplefetchall(mock_cursor)

        self.assertEqual(result[0].bar, 1)
        self.assertEqual(result[0].foo, 'a')
