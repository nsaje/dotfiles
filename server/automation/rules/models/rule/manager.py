from django.db import transaction

import core.common

from ..rule_condition import RuleCondition
from . import model


class RuleManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, agency, **kwargs):
        core.common.entity_limits.enforce(model.Rule.objects.filter(agency_id=agency.id))
        conditions = kwargs.pop("conditions", [])
        ad_groups_included = kwargs.pop("ad_groups_included", [])

        rule = model.Rule(agency=agency, **kwargs)
        rule.save(request)

        for ad_group in ad_groups_included:
            rule.ad_groups_included.add(ad_group)
        for condition in conditions:
            RuleCondition.objects.create(rule_id=rule.id, **condition)

        # TODO: write history ??
        return rule
