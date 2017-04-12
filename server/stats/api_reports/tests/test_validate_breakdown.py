from django.test import TestCase

from dash.constants import Level
from stats import constants
from stats.api_reports import validate_breakdown_by_permissions, validate_breakdown_by_structure
from utils import exc
from utils import test_helper
from zemauth.models import User


class ValidateBreakdownTest(TestCase):
    fixtures = ['test_non_superuser']

    def add_permission_and_test(self, level, breakdown, permissions):
        user = User.objects.get(pk=1)
        with self.assertRaises(exc.MissingDataError):
            validate_breakdown_by_permissions(level, user, breakdown)

        # load it again as it seems that user backend caches permissions collection once it is asked about it
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, permissions)
        validate_breakdown_by_permissions(level, user, breakdown)

        test_helper.remove_permissions(user, permissions)

    def test_breakdown_validate_by_permissions(self):
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ['account_id'], ['all_accounts_accounts_view'])
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ['source_id'], ['all_accounts_sources_view'])

        self.add_permission_and_test(Level.ACCOUNTS, ['campaign_id'], ['account_campaigns_view'])
        self.add_permission_and_test(Level.ACCOUNTS, ['source_id'], ['account_sources_view'])

        self.add_permission_and_test(Level.AD_GROUPS, ['publisher_id'], ['can_see_publishers'])

    def test_breakdown_validate_publisher(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['can_see_publishers'])

        validate_breakdown_by_structure(Level.ALL_ACCOUNTS, ['publisher_id'])

        validate_breakdown_by_structure(Level.ACCOUNTS, ['publisher_id'])

        validate_breakdown_by_structure(Level.CAMPAIGNS, ['publisher_id'])

        validate_breakdown_by_structure(Level.AD_GROUPS, ['publisher_id'])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, ['publisher_id', 'source_id'])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, ['publisher_id', 'content_ad_id'])

    def test_breakdown_validate_delivery(self):
        user = User.objects.get(pk=1)
        for dimension in constants.DeliveryDimension._ALL:
            with self.assertRaises(exc.InvalidBreakdownError):
                validate_breakdown_by_structure(Level.AD_GROUPS, [dimension])

    def test_breakdown_validate_time(self):
        user = User.objects.get(pk=1)
        for dimension in constants.TimeDimension._ALL:
            validate_breakdown_by_structure(Level.AD_GROUPS, [dimension])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, [constants.DAY, constants.WEEK])

    def test_breakdown_structure(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, [
            'all_accounts_sources_view',
            'account_sources_view',
            'all_accounts_accounts_view',
            'account_campaigns_view',
        ])
        validate_breakdown_by_structure(Level.AD_GROUPS, [
            constants.ACCOUNT,
            constants.CAMPAIGN,
            constants.AD_GROUP,
            constants.CONTENT_AD,
            constants.SOURCE,
        ])
