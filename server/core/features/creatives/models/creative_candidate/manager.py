from django.db import transaction

import core.common

from ... import converters
from . import model


class CreativeCandidateManager(core.common.BaseManager):
    @transaction.atomic()
    def create(self, batch):
        candidate = model.CreativeCandidate(
            batch=batch,
            type=converters.ConstantsConverter.to_ad_type(batch.type),
            image_crop=batch.image_crop,
            display_url=batch.display_url,
            brand_name=batch.brand_name,
            description=batch.description,
            call_to_action=batch.call_to_action,
        )
        candidate.save()
        return candidate
