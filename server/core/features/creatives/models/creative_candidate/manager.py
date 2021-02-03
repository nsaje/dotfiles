from django.db import transaction

import core.common

from . import model


class CreativeCandidateManager(core.common.BaseManager):
    @transaction.atomic()
    def create(self, batch):
        candidate = model.CreativeCandidate(batch=batch)
        candidate.save()
        return candidate
