from django.db import transaction

import core.common
import dash.constants

from . import model


class CreativeBatchManager(core.common.BaseManager):
    @transaction.atomic
    def create(
        self,
        request,
        name,
        *,
        agency=None,
        account=None,
        mode=dash.constants.CreativeBatchMode.INSERT,
        type=dash.constants.CreativeBatchType.NATIVE,
    ):
        batch = model.CreativeBatch(name=name, agency=agency, account=account, mode=mode, type=type)
        batch.save(request)
        return batch
