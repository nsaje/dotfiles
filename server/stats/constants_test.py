from django.test import TestCase

from stats import constants


class ConstantsTest(TestCase):
    def test_is_placement_breakdown(self):
        self.assertFalse(constants.is_placement_breakdown([constants.PUBLISHER]))
        self.assertTrue(constants.is_placement_breakdown([constants.PLACEMENT]))
        self.assertTrue(constants.is_placement_breakdown([constants.PUBLISHER, constants.PLACEMENT]))

    def test_contains_dimension(self):
        self.assertTrue(constants.contains_dimension(["publisher_id"], [constants.PUBLISHER]))
        self.assertTrue(constants.contains_dimension(["placement_id"], [constants.PUBLISHER, constants.PLACEMENT]))
        self.assertFalse(constants.contains_dimension(["ad_group_id"], [constants.PUBLISHER, constants.PLACEMENT]))
        self.assertTrue(
            constants.contains_dimension(
                ["ad_group_id", "publisher_id", "placement_id"], [constants.PUBLISHER, constants.PLACEMENT]
            )
        )
        self.assertFalse(constants.contains_dimension([], [constants.PUBLISHER]))
        self.assertFalse(constants.contains_dimension(["ad_group_id"], None))
        self.assertFalse(constants.contains_dimension([], [constants.PUBLISHER]))
        self.assertFalse(constants.contains_dimension(["ad_group_id"], None))
