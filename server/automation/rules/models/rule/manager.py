from django.db import transaction

import core.common

from . import model


class RuleManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, agency=None, account=None, **kwargs):
        if agency:
            self._validate_entity_limits(agency)
        elif account:
            self._validate_entity_limits(account.agency)

        rule = model.Rule(agency=agency, account=account)
        rule.update(request, **kwargs)

        return rule

    @staticmethod
    def _validate_entity_limits(agency):
        core.common.entity_limits.enforce(model.Rule.objects.filter(agency=agency))
