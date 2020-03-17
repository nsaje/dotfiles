
from django.test import TestCase

from stats import constants


class ConstantsTest(TestCase):
    def test_is_placement_breakdown(self):
        self.assertFalse(constants.is_placement_breakdown([constants.PUBLISHER]))
        self.assertTrue(constants.is_placement_breakdown([constants.PLACEMENT]))
        self.assertTrue(constants.is_placement_breakdown([constants.PLACEMENT_TYPE]))
        self.assertTrue(
            constants.is_placement_breakdown([constants.PUBLISHER, constants.PLACEMENT, constants.PLACEMENT_TYPE])
        )
