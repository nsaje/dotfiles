import datetime

from django.test import TestCase

from utils.test_helper import add_permissions
from zemauth.models import User

from stats import augmenter


class AugmenterTestCase(TestCase):

    fixtures = ['test_augmenter']

    def test_augment_accounts(self):
        rows = [
            {'account_id': 1, 'source_id': 1, 'clicks': 10},
            {'account_id': 2, 'source_id': 1, 'clicks': 20},
        ]

        augmenter.augment_accounts(rows)

        self.assertItemsEqual(rows, [
            {'account_id': 1, 'account_name': 'test account 1', 'source_id': 1, 'clicks': 10},
            {'account_id': 2, 'account_name': 'test account 2', 'source_id': 1, 'clicks': 20},
        ])

    def test_augment_campaigns(self):
        rows = [
            {'campaign_id': 1, 'source_id': 1, 'clicks': 10},
            {'campaign_id': 2, 'source_id': 1, 'clicks': 20},
        ]

        augmenter.augment_campaigns(rows)

        self.assertItemsEqual(rows, [
            {'campaign_id': 1, 'campaign_name': 'test campaign 1', 'source_id': 1, 'clicks': 10},
            {'campaign_id': 2, 'campaign_name': 'test campaign 2', 'source_id': 1, 'clicks': 20},
        ])

    def test_augment_ad_groups(self):
        rows = [
            {'ad_group_id': 1, 'source_id': 1, 'clicks': 10},
            {'ad_group_id': 2, 'source_id': 1, 'clicks': 20},
        ]

        augmenter.augment_ad_groups(rows)

        self.assertItemsEqual(rows, [
            {'ad_group_id': 1, 'ad_group_name': 'test adgroup 1', 'source_id': 1, 'clicks': 10},
            {'ad_group_id': 2, 'ad_group_name': 'test adgroup 2', 'source_id': 1, 'clicks': 20},
        ])

    def test_augment_content_ads(self):
        rows = [
            {'content_ad_id': 1, 'source_id': 1, 'clicks': 10},
            {'content_ad_id': 2, 'source_id': 1, 'clicks': 20},
        ]

        augmenter.augment_content_ads(rows)

        self.assertItemsEqual(rows, [
            {'content_ad_id': 1, 'content_ad_title': 'Test Article 1', 'source_id': 1, 'clicks': 10},
            {'content_ad_id': 2, 'content_ad_title': 'Test Article 2', 'source_id': 1, 'clicks': 20},
        ])

    def test_augment_source(self):
        rows = [
            {'content_ad_id': 1, 'source_id': 1, 'clicks': 10},
            {'content_ad_id': 2, 'source_id': 2, 'clicks': 20},
        ]

        augmenter.augment_source(rows)

        self.assertItemsEqual(rows, [
            {'content_ad_id': 1, 'source_id': 1, 'source_name': 'AdBlade', 'clicks': 10},
            {'content_ad_id': 2, 'source_id': 2, 'source_name': 'Adiant', 'clicks': 20},
        ])

    def test_augment_row_delivery(self):
        rows = [
            {'device_type': 1, 'age': 1, 'age_gender': 1, 'gender': 1, 'clicks': 10},
            {'device_type': 2, 'age': 2, 'age_gender': 2, 'gender': 2, 'clicks': 20},
            {'device_type': 0, 'age': 3, 'age_gender': 5, 'gender': 0, 'clicks': 30},
        ]

        for row in rows:
            augmenter.augment_row_delivery(row)

        self.assertItemsEqual(rows, [
            {'device_type': 'Desktop', 'age': '18-20', 'age_gender': '18-20 Men', 'gender': 'Men', 'clicks': 10},
            {'device_type': 'Tablet', 'age': '21-29', 'age_gender': '18-20 Women', 'gender': 'Women', 'clicks': 20},
            {'device_type': 'Undefined', 'age': '30-39', 'age_gender': '21-29 Women', 'gender': 'Undefined',
             'clicks': 30},
        ])

    def test_augment_row_time(self):
        rows = [
            {'day': datetime.date(2016, 5, 1), 'week': datetime.date(2016, 5, 1),
             'month': datetime.date(2016, 5, 1), 'clicks': 10},
            {'day': datetime.date(2016, 5, 5), 'week': datetime.date(2016, 5, 5),
             'month': datetime.date(2016, 5, 5), 'clicks': 20},
        ]

        for row in rows:
            augmenter.augment_row_time(row)

        self.assertItemsEqual(rows, [
            {'day': '2016-05-01', 'week': 'Week 2016-05-01 - 2016-05-07',
             'month': 'Month 5/2016', 'clicks': 10},
            {'day': '2016-05-05', 'week': 'Week 2016-05-05 - 2016-05-11',
             'month': 'Month 5/2016', 'clicks': 20},
        ])

    def test_augment(self):
        breakdown = ['ad_group', 'source']
        target = 'source'

        rows = [
            {'ad_group_id': 1, 'source_id': 1, 'age': 1, 'clicks': 10},
            {'ad_group_id': 2, 'source_id': 2, 'age': 2, 'clicks': 20},
        ]

        augmenter.augment(breakdown, rows, target)

        self.assertItemsEqual(rows, [
            {'ad_group_id': 1, 'source_id': 1, 'source_name': 'AdBlade', 'clicks': 10, 'age': '18-20',
             'breakdown_id': '1||1', 'breakdown_name': 'AdBlade', 'parent_breakdown_id': '1'},
            {'ad_group_id': 2, 'source_id': 2, 'source_name': 'Adiant', 'clicks': 20, 'age': '21-29',
             'breakdown_id': '2||2', 'breakdown_name': 'Adiant', 'parent_breakdown_id': '2'},
        ])

        # same but different target
        target = 'ad_group'

        rows = [
            {'ad_group_id': 1, 'source_id': 1, 'age': 1, 'clicks': 10},
            {'ad_group_id': 2, 'source_id': 2, 'age': 2, 'clicks': 20},
        ]

        augmenter.augment(breakdown, rows, target)

        self.assertItemsEqual(rows, [
            {'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
             'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1'},
            {'ad_group_id': 2, 'source_id': 2, 'ad_group_name': 'test adgroup 2', 'clicks': 20, 'age': '21-29',
             'breakdown_id': '2||2', 'breakdown_name': 'test adgroup 2', 'parent_breakdown_id': '2'},
        ])


class FilterTestCase(TestCase):

    fixtures = ['test_augmenter', 'test_non_superuser']

    def test_user_not_superuser(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_superuser)

    def test_filter_columns_by_permission_no_perm(self):
        user = User.objects.get(pk=1)

        rows = [
            {
                'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
                'license_fee': 123, 'billing_cost': 124, 'media_cost': 125,
            },
            {
                'ad_group_id': 2, 'source_id': 2, 'ad_group_name': 'test adgroup 2', 'clicks': 20, 'age': '21-29',
                'breakdown_id': '2||2', 'breakdown_name': 'test adgroup 2', 'parent_breakdown_id': '2',
                'license_fee': 223, 'billing_cost': 224, 'media_cost': 225,
            },
        ]

        augmenter.filter_columns_by_permission(user, rows)

        self.assertItemsEqual(rows, [
            {
                'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
            },
            {
                'ad_group_id': 2, 'source_id': 2, 'ad_group_name': 'test adgroup 2', 'clicks': 20, 'age': '21-29',
                'breakdown_id': '2||2', 'breakdown_name': 'test adgroup 2', 'parent_breakdown_id': '2',
            },
        ])

    def test_filter_columns_by_permission(self):
        user = User.objects.get(pk=1)
        add_permissions(user, ['can_view_effective_costs'])

        rows = [
            {
                'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
                'license_fee': 123, 'billing_cost': 124, 'media_cost': 125,
            },
            {
                'ad_group_id': 2, 'source_id': 2, 'ad_group_name': 'test adgroup 2', 'clicks': 20, 'age': '21-29',
                'breakdown_id': '2||2', 'breakdown_name': 'test adgroup 2', 'parent_breakdown_id': '2',
                'license_fee': 223, 'billing_cost': 224, 'media_cost': 225,
            },
        ]

        augmenter.filter_columns_by_permission(user, rows)

        self.assertItemsEqual(rows, [
            {
                'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
                'license_fee': 123, 'billing_cost': 124,
            },
            {
                'ad_group_id': 2, 'source_id': 2, 'ad_group_name': 'test adgroup 2', 'clicks': 20, 'age': '21-29',
                'breakdown_id': '2||2', 'breakdown_name': 'test adgroup 2', 'parent_breakdown_id': '2',
                'license_fee': 223, 'billing_cost': 224,
            },
        ])
