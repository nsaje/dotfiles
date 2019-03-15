from collections import defaultdict
from decimal import Decimal


def format_metrics(stats, metrics, group_names, group_key=None, default_group="totals"):
    data = defaultdict(lambda: defaultdict(list))
    for stat in stats:
        for metric in metrics:
            if not group_key:
                group_id = default_group
            elif group_names and group_key in stat and stat[group_key] in group_names:
                group_id = stat[group_key]
            else:
                continue
            data[group_id][metric].append(
                (stat["day"], float(stat[metric]) if isinstance(stat.get(metric), Decimal) else stat.get(metric))
            )
            # when all values are None we treat this as no data (an empty array)
            if all(x[1] is None for x in data[group_id][metric]):
                data[group_id][metric] = []

    return [{"id": key, "name": value, "series_data": data[key]} for key, value in group_names.items()]


def get_object_mapping(objects):
    return {obj.id: getattr(obj, "name", None) or obj.title for obj in objects}


def get_delivery_mapping(constant_cls, delivery_ids):
    mapping = {}
    for delivery_id in delivery_ids:
        try:
            mapping[delivery_id] = constant_cls.get_name(delivery_id) if constant_cls else delivery_id
        except KeyError:
            mapping[delivery_id] = delivery_id
    return mapping


def merge(*args):
    """
    Merge an arbitrary number of dictionaries
    """
    ret = {}
    for d in args:
        if d:
            ret.update(d)
    return ret
