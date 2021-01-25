from django.conf import settings

import core.models


def get_source_id_slugs_mapping():
    return {
        data["id"]: data
        for data in core.models.Source.objects.filter(
            id__in=set(source_id for source_group in settings.SOURCE_GROUPS.values() for source_id in source_group)
        ).values("id", "bidder_slug", "tracking_slug")
    }
