from django.db import transaction

import core.common

from . import model


class RuleManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, agency, **kwargs):
        core.common.entity_limits.enforce(model.Rule.objects.filter(agency_id=agency.id))

        rule = model.Rule(agency=agency)
        rule.update(request, **kwargs)

        # TODO: write history ??
        return rule
