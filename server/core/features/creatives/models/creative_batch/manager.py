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
        type=dash.constants.CreativeBatchType.INSERT,
        ad_type=dash.constants.AdType.CONTENT,
    ):
        batch = model.CreativeBatch(name=name, agency=agency, account=account, type=type, ad_type=ad_type)
        batch.save(request)
        return batch
