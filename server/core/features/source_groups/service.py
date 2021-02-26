from django.conf import settings

import core.models


def get_source_id_slugs_mapping():
    return {
        data["id"]: data
        for data in core.models.Source.objects.filter(
            id__in=set(source_id for source_group in settings.SOURCE_GROUPS.values() for source_id in source_group)
        ).values("id", "bidder_slug", "tracking_slug")
    }


def get_source_id_group_id_mapping():
    return {subsource: parent for parent, subsources in settings.SOURCE_GROUPS.items() for subsource in subsources}


def get_source_slug_group_slug_mapping(include_group_slug=False):
    source_ids = set(settings.SOURCE_GROUPS.keys())
    for ids in settings.SOURCE_GROUPS.values():
        source_ids.update(ids)

    source_id_slug_map = {
        source["id"]: source["bidder_slug"]
        for source in core.models.Source.objects.filter(id__in=source_ids).values("id", "bidder_slug")
    }

    source_slug_group_slug_map = {}
    for group_id, source_ids in settings.SOURCE_GROUPS.items():
        group_slug = source_id_slug_map[group_id]
        source_slug_group_slug_map.update({source_id_slug_map[sid]: group_slug for sid in source_ids})

        if include_group_slug:
            source_slug_group_slug_map.update({group_slug: group_slug})

    return source_slug_group_slug_map
