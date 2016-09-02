import datetime

from django.test import TestCase

from stats import augmenter


class AugmenterTestCase(TestCase):

    fixtures = ['test_augmenter']

    def test_augment_device_type(self):
        rows = [
            {'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ]

        augmenter.augment(['device_type'], rows)

        self.assertEqual(rows, [
            {'parent_breakdown_id': '', 'breakdown_id': '1', 'breakdown_name': 'Desktop', 'name': 'Desktop',
             'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'parent_breakdown_id': '', 'breakdown_id': '2', 'breakdown_name': 'Tablet', 'name': 'Tablet',
             'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'parent_breakdown_id': '', 'breakdown_id': '0', 'breakdown_name': 'Unknown', 'name': 'Unknown',
             'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ])

    def test_augment_age(self):
        rows = [
            {'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ]

        augmenter.augment(['age'], rows)

        self.assertEqual(rows, [
            {'parent_breakdown_id': '', 'breakdown_id': '1', 'breakdown_name': '18-20', 'name': '18-20',
             'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'parent_breakdown_id': '', 'breakdown_id': '2', 'breakdown_name': '21-29', 'name': '21-29',
             'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'parent_breakdown_id': '', 'breakdown_id': '3', 'breakdown_name': '30-39', 'name': '30-39',
             'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ])

    def test_augment_age_gender(self):
        rows = [
            {'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ]

        augmenter.augment(['age_gender'], rows)

        self.assertEqual(rows, [
            {'parent_breakdown_id': '', 'breakdown_id': '1', 'breakdown_name': '18-20 Men', 'name': '18-20 Men',
             'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'parent_breakdown_id': '', 'breakdown_id': '2', 'breakdown_name': '18-20 Women', 'name': '18-20 Women',
             'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'parent_breakdown_id': '', 'breakdown_id': '5', 'breakdown_name': '21-29 Women', 'name': '21-29 Women',
             'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ])

    def test_augment_gender(self):
        rows = [
            {'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ]

        augmenter.augment(['gender'], rows)

        self.assertEqual(rows, [
            {'parent_breakdown_id': '', 'breakdown_id': '1', 'breakdown_name': 'Men', 'name': 'Men',
             'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'parent_breakdown_id': '', 'breakdown_id': '2', 'breakdown_name': 'Women', 'name': 'Women',
             'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'parent_breakdown_id': '', 'breakdown_id': '0', 'breakdown_name': 'Unknown', 'name': 'Unknown',
             'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ])

    def test_augment_dma(self):
        rows = [
            {'dma': 669, 'clicks': 10},
            {'dma': 547, 'clicks': 20},
            {'dma': None, 'clicks': 30},
        ]

        augmenter.augment(['dma'], rows)

        self.assertEqual(rows, [
            {'parent_breakdown_id': '', 'breakdown_id': '669',
             'breakdown_name': '669 Madison, WI', 'name': '669 Madison, WI', 'dma': 669, 'clicks': 10},
            {'parent_breakdown_id': '', 'breakdown_id': '547',
             'breakdown_name': '547 Toledo, OH', 'name': '547 Toledo, OH', 'dma': 547, 'clicks': 20},
            {'parent_breakdown_id': '', 'breakdown_id': '-None-',
             'breakdown_name': 'Unknown', 'name': 'Unknown', 'dma': None, 'clicks': 30},
        ])

    def test_augment_day(self):
        rows = [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20},
        ]

        augmenter.augment(['day'], rows)

        self.assertEqual(rows, [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10, 'breakdown_name': '2016-05-01', 'name': '2016-05-01',
             'breakdown_id': '2016-05-01', 'parent_breakdown_id': ''},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20, 'breakdown_name': '2016-05-05', 'name': '2016-05-05',
             'breakdown_id': '2016-05-05', 'parent_breakdown_id': ''},
        ])

    def test_augment_week(self):
        rows = [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20},
        ]

        augmenter.augment(['week'], rows)

        self.assertItemsEqual(rows, [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10, 'breakdown_name': 'Week 2016-05-01 - 2016-05-07', 'name': 'Week 2016-05-01 - 2016-05-07',
             'breakdown_id': '2016-05-01', 'parent_breakdown_id': ''},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20, 'breakdown_name': 'Week 2016-05-05 - 2016-05-11', 'name': 'Week 2016-05-05 - 2016-05-11',
             'breakdown_id': '2016-05-05', 'parent_breakdown_id': ''},
        ])

    def test_augment_month(self):
        rows = [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20},
        ]

        augmenter.augment(['month'], rows)

        self.assertItemsEqual(rows, [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1), 'month': datetime.date(2016, 5, 1),
             'clicks': 10, 'breakdown_name': 'Month 5/2016', 'name': 'Month 5/2016',
             'breakdown_id': '2016-05-01', 'parent_breakdown_id': ''},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5), 'month': datetime.date(2016, 5, 5),
             'clicks': 20, 'breakdown_name': 'Month 5/2016', 'name': 'Month 5/2016',
             'breakdown_id': '2016-05-05', 'parent_breakdown_id': ''},
        ])

    def test_augment_other(self):
        breakdown = ['ad_group_id', 'source_id']

        rows = [
            {'ad_group_id': 1, 'source_id': 1, 'name': 'Source1', 'age': 1, 'dma': 501, 'clicks': 10},
            {'ad_group_id': 2, 'source_id': 2, 'name': 'Source2', 'age': 2, 'dma': 502, 'clicks': 20},
        ]

        augmenter.augment(breakdown, rows)

        self.assertItemsEqual(rows, [
            {'ad_group_id': 1, 'source_id': 1, 'breakdown_id': '1||1', 'parent_breakdown_id': '1',
             'name': 'Source1', 'breakdown_name': 'Source1', 'age': 1, 'dma': 501, 'clicks': 10},
            {'ad_group_id': 2, 'source_id': 2, 'breakdown_id': '2||2', 'parent_breakdown_id': '2',
             'name': 'Source2', 'breakdown_name': 'Source2', 'age': 2, 'dma': 502, 'clicks': 20},
        ])

    def test_remove_state_for_content_ad_source(self):
        breakdown = ['content_ad_id', 'source_id']

        rows = [
            {'content_ad_id': 1, 'source_id': 1, 'name': 'Source1', 'status': 1, 'state': 1, 'clicks': 10},
            {'content_ad_id': 2, 'source_id': 2, 'name': 'Source2', 'status': 1, 'state': 1, 'clicks': 20},
        ]

        augmenter.augment(breakdown, rows)

        self.assertItemsEqual(rows, [
            {'content_ad_id': 1, 'source_id': 1, 'name': 'Source1', 'clicks': 10,
             'breakdown_id': '1||1', 'breakdown_name': 'Source1', 'parent_breakdown_id': '1'},
            {'content_ad_id': 2, 'source_id': 2, 'name': 'Source2', 'clicks': 20,
             'breakdown_id': '2||2', 'breakdown_name': 'Source2', 'parent_breakdown_id': '2'},
        ])
