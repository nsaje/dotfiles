import decimal

from django.test import TestCase
from mock import patch
from mixer.backend.django import mixer

import constants
import models
import service
import serializers


class TestSerializerCommonMixin(object):

    @patch('dash.features.bluekai.service.taxonomy.ROOT_NODE_ID', 1)
    def test_serialize(self):
        root_category = mixer.blend(
            models.BlueKaiCategory,
            category_id=1,
            parent_category_id=99999,  # non-existing parent
            status=constants.BlueKaiCategoryStatus.ACTIVE)
        middle_node = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=root_category.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE)
        leaf_category_1 = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE)
        leaf_category_2 = mixer.blend(
            models.BlueKaiCategory,
            parent_category_id=middle_node.category_id,
            status=constants.BlueKaiCategoryStatus.ACTIVE)

        tree = service.get_tree()
        serialized = self.serializer(tree).data
        self.check_node(serialized, root_category, [middle_node])
        self.check_node(
            serialized['child_nodes'][0], middle_node,
            [leaf_category_1, leaf_category_2])

        leaf_nodes = serialized['child_nodes'][0]['child_nodes']
        leaf_node_1 = [node for node in leaf_nodes
                       if node['category_id'] == leaf_category_1.category_id][0]
        leaf_node_2 = [node for node in leaf_nodes
                       if node['category_id'] == leaf_category_2.category_id][0]
        self.check_node(leaf_node_1, leaf_category_1, [])
        self.check_node(leaf_node_2, leaf_category_2, [])


class TestBlueKaiCategorySerializer(TestCase, TestSerializerCommonMixin):

    serializer = serializers.BlueKaiCategorySerializer

    def check_node(self, node, category, child_categories):
        for key in set(node.keys()) - set(['child_nodes']):
            db_value = getattr(category, key)
            if isinstance(db_value, decimal.Decimal):
                db_value = format(db_value, '0.2f')

            self.assertEqual(db_value, node[key])

        self.assertEqual(
            set([child['category_id'] for child in node['child_nodes']]),
            set([child_category.category_id for child_category in child_categories])
        )


class TestBlueKaiCategoryInternalSerializer(TestCase, TestSerializerCommonMixin):

    serializer = serializers.BlueKaiCategoryInternalSerializer

    def check_node(self, node, category, child_categories):
        for key in set(node.keys()) - set(['child_nodes']):
            db_value = getattr(category, key)
            if isinstance(db_value, decimal.Decimal):
                db_value = format(db_value, '0.2f')

            out_value = node[key]
            if key == 'reach':
                out_value = out_value['value']

            self.assertEqual(db_value, out_value)

        self.assertEqual(
            set([child['category_id'] for child in node['child_nodes']]),
            set([child_category.category_id for child_category in child_categories])
        )
