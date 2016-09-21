from django.test import TestCase

from utils import dict_helper


class JoinDictsTest(TestCase):

    def test_join(self):

        self.assertEqual(dict_helper.dict_join({1: 2, 'asd': 'asd'}, {'end_date': None}), {
            1: 2,
            'asd': 'asd',
            'end_date': None,
        })
