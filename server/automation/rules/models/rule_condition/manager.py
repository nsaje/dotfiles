from django.db import transaction

import core.common

from . import model


class RuleConditionManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, rule, **kwargs):
        rule_condition = model.RuleCondition(rule=rule)
        rule_condition.update(**kwargs)
        return rule_condition
