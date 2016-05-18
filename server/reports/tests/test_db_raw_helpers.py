from mock import Mock

from django.test import TestCase

from reports import db_raw_helpers

import dash.models


class DbRawHelpersTest(TestCase):

    fixtures = ['test_api_contentads']

    def test_dictfetchall(self):
        mock_cursor = Mock()
        mock_cursor.description = ['foo', 'bar']
        mock_cursor.fetchall.return_value = [['a', 1]]

        result = db_raw_helpers.dictfetchall(mock_cursor)

        self.assertEqual(result, [{'b': 1, 'f': 'a'}])

    def test_is_collection(self):
        self.assertTrue(db_raw_helpers.is_collection([]))
        self.assertTrue(db_raw_helpers.is_collection(set()))
        self.assertTrue(db_raw_helpers.is_collection({1, 2}))
        self.assertTrue(db_raw_helpers.is_collection(tuple()))
        self.assertTrue(db_raw_helpers.is_collection(dash.models.AdGroup.objects.all()))

        self.assertFalse(db_raw_helpers.is_collection(1))
        self.assertFalse(db_raw_helpers.is_collection('a'))
        self.assertFalse(db_raw_helpers.is_collection(u'a'))
        self.assertFalse(db_raw_helpers.is_collection(r'a'))
        self.assertFalse(db_raw_helpers.is_collection(None))
        self.assertFalse(db_raw_helpers.is_collection(dash.models.AdGroup.objects.get(pk=1)))

    def test_extract_obj_ids(self):

        self.assertItemsEqual(db_raw_helpers.extract_obj_ids([1, 2, 3]), [1, 2, 3])
        self.assertItemsEqual(db_raw_helpers.extract_obj_ids(dash.models.AdGroup.objects.filter(pk__in=[1, 2, 3])), [1, 2, 3])
        self.assertEqual(db_raw_helpers.extract_obj_ids({
            'account': [1, 2, 3],
            'ad_group': dash.models.AdGroup.objects.filter(pk__in=[1, 2, 3]),
            'bla': 5,
            'aaa': dash.models.AdGroup.objects.get(pk=1),
            'bbb': "qwe"
        }), {
            'account': [1, 2, 3],
            'ad_group': [1, 2, 3],
            'bla': 5,
            'aaa': 1,
            'bbb': "qwe"
        })
