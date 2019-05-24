def entity_tag_query_set_to_string(entity_tag_query_set):
    return entity_tag_names_to_string(entity_tag_query_set.values_list("name", flat=True))


def entity_tag_names_to_string(tag_name_list):
    if tag_name_list:
        return ", ".join(sorted(e for e in tag_name_list if e))

    return ""
