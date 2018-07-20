from mock import patch

from django.test import TestCase
from mixer.backend.django import mixer

from . import taxonomy
from dash.features.bluekai import constants, models


class GetTreeTestCase(TestCase):
    @patch("dash.features.bluekai.service.taxonomy.ROOT_NODE_ID", 1)
    def test_get_tree(self):
        root_node = mixer.blend(
            models.BlueKaiCategory,
            category_id=1,
            parent_category_id=99999,  # non-existing parent
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        middle_node = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=root_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        leaf_node_1 = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        leaf_node_2 = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )

        tree = taxonomy.get_tree()
        self.assertEqual(tree["category_id"], root_node.category_id)
        self.assertEqual(len(tree["child_nodes"]), 1)
        self.assertEqual(tree["child_nodes"][0]["category_id"], middle_node.category_id)
        self.assertEqual(len(tree["child_nodes"][0]["child_nodes"]), 2)
        self.assertEqual(
            set([leaf_node_1.category_id, leaf_node_2.category_id]),
            set([category["category_id"] for category in tree["child_nodes"][0]["child_nodes"]]),
        )

    @patch("dash.features.bluekai.service.taxonomy.ROOT_NODE_ID", 1)
    def test_get_tree_inactive_node(self):
        root_node = mixer.blend(
            models.BlueKaiCategory,
            category_id=1,
            parent_category_id=99999,  # non-existing parent
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        middle_node = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=root_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        leaf_node_1 = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.INACTIVE,
        )

        tree = taxonomy.get_tree()
        self.assertEqual(tree["category_id"], root_node.category_id)
        self.assertEqual(len(tree["child_nodes"]), 1)
        self.assertEqual(tree["child_nodes"][0]["category_id"], middle_node.category_id)
        self.assertEqual(len(tree["child_nodes"][0]["child_nodes"]), 1)
        self.assertEqual(tree["child_nodes"][0]["child_nodes"][0]["category_id"], leaf_node_1.category_id)
