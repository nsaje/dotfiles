import copy
from reports.db_raw_helpers import extract_obj_ids
from dash import breakdown_helpers


def copy_and_translate_dict(mapping, dict_):
    if not dict_:
        return dict_

    return {mapping.get(k, k): extract_obj_ids(v) for k, v in dict_.items()}


def copy_and_translate_dicts(mapping, list_of_dicts):
    if not list_of_dicts:
        return list_of_dicts

    return [translate_dict(mapping, x) for x in list_of_dicts]


def copy_and_translate_list(mapping, list_):
    return [mapping.get(x, x) for x in list_]
