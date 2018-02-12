from .. import models
from . import reach

ROOT_NODE_ID = 671901


def get_tree():
    active_categories = models.BlueKaiCategory.objects.active()

    nodes = {}
    for category in active_categories:
        nodes[category.category_id] = {
            'category_id': category.category_id,
            'parent_category_id': category.parent_category_id,
            'name': category.name,
            'description': category.description,
            'navigation_only': category.navigation_only,
            'price': category.price,
            'reach': {
                'value': category.reach,
                'relative': reach.calculate_relative_reach(category.reach)
            },
            'child_nodes': [],
        }

    for node in list(nodes.values()):
        parent = nodes.get(node['parent_category_id'])
        if not parent:
            continue

        parent['child_nodes'].append(node)

    return nodes[ROOT_NODE_ID]
