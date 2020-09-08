from django.test import TestCase

from dash.constants import Level
from stats import constants
from stats.api_reports import validate_breakdown_by_permissions
from stats.api_reports import validate_breakdown_by_structure
from utils import exc
from utils import test_helper
from zemauth.models import User


class ValidateBreakdownTest(TestCase):
    fixtures = ["test_non_superuser"]

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
        self.add_permission_and_test(Level.AD_GROUPS, ["publisher_id"], ["can_see_publishers"])

        self.add_permission_and_test(
            Level.AD_GROUPS,
            ["publisher_id", "content_ad_id"],
            ["can_see_publishers", "can_breakdown_reports_by_ads_and_publishers"],
        )

    def test_breakdown_validate_publisher(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ["can_see_publishers"])

        validate_breakdown_by_structure(Level.ALL_ACCOUNTS, ["publisher_id"])

        validate_breakdown_by_structure(Level.ACCOUNTS, ["publisher_id"])

        validate_breakdown_by_structure(Level.CAMPAIGNS, ["publisher_id"])

        validate_breakdown_by_structure(Level.AD_GROUPS, ["publisher_id"])

        validate_breakdown_by_structure(Level.AD_GROUPS, ["publisher_id", "content_ad_id"])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, ["publisher_id", "source_id"])

    def test_breakdown_validate_placement_permissions(self):
        self.add_permission_and_test(Level.AD_GROUPS, ["placement_id"], ["can_use_placement_targeting"])
        self.add_permission_and_test(Level.CAMPAIGNS, ["placement_id"], ["can_use_placement_targeting"])

        user = User.objects.get(pk=1)
        # TODO should be structure validation, but leaving like this until refactor
        with self.assertRaises(exc.MissingDataError):
            validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ["placement_id"])

        with self.assertRaises(exc.MissingDataError):
            validate_breakdown_by_permissions(Level.ACCOUNTS, user, ["placement_id"])

    def test_breakdown_validate_placement_structure(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ["can_use_placement_targeting"])

        validate_breakdown_by_structure(Level.CAMPAIGNS, ["placement_id"])

        validate_breakdown_by_structure(Level.AD_GROUPS, ["placement_id"])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, ["placement_id", "content_ad_id"])

    def test_breakdown_validate_delivery(self):
        User.objects.get(pk=1)
        for dimension in constants.DeliveryDimension._ALL:
            validate_breakdown_by_structure(Level.AD_GROUPS, [dimension])

    def test_breakdown_validate_delivery_multiple(self):
        User.objects.get(pk=1)
        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, constants.DeliveryDimension._ALL)

    def test_breakdown_validate_time(self):
        User.objects.get(pk=1)
        for dimension in constants.TimeDimension._ALL:
            validate_breakdown_by_structure(Level.AD_GROUPS, [dimension])

        with self.assertRaises(exc.InvalidBreakdownError):
            validate_breakdown_by_structure(Level.AD_GROUPS, [constants.DAY, constants.WEEK])

    def test_breakdown_structure(self):
        validate_breakdown_by_structure(
            Level.AD_GROUPS,
            [constants.ACCOUNT, constants.CAMPAIGN, constants.AD_GROUP, constants.CONTENT_AD, constants.SOURCE],
        )
