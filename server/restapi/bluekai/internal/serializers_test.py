import decimal

from django.test import TestCase

import restapi.bluekai.v1.serializers_test

from . import serializers


class BlueKaiCategoryInternalSerializerTestCase(
    restapi.bluekai.v1.serializers_test.BlueKaiCategorySerializerTestCaseMixin, TestCase
):
    serializer = serializers.BlueKaiCategoryInternalSerializer

    def check_node(self, node, category, child_categories):
        for key in set(node.keys()) - set(["child_nodes"]):
            db_value = getattr(category, key)
            if isinstance(db_value, decimal.Decimal):
                db_value = format(db_value, "0.2f")

            out_value = node[key]
            if key == "reach":
                out_value = out_value["value"]

            self.assertEqual(db_value, out_value)

        self.assertEqual(
            set([child["category_id"] for child in node["child_nodes"]]),
            set([child_category.category_id for child_category in child_categories]),
        )
