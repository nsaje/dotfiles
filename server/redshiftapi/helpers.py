from reports.db_raw_helpers import extract_obj_ids


def translate_dict(mapping, dict_):
    if not dict_:
        return dict_

    return {mapping.get(k, k): extract_obj_ids(v) for k, v in dict_.items()}


def translate_dicts(mapping, list_of_dicts):
    if not list_of_dicts:
        return list_of_dicts

    return [translate_dict(mapping, x) for x in list_of_dicts]


def translate_list(mapping, list_):
    return [mapping.get(x, x) for x in list_]
