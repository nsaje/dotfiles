from django.db import transaction

import core.common

from . import model


class CreativeBatchManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, name, agency=None, account=None):
        batch = model.CreativeBatch(name=name, agency=agency, account=account)
        batch.save(request)
        return batch
