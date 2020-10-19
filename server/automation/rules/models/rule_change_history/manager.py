from django.db import transaction
from django.forms.models import model_to_dict

import core.common


class RuleChangeHistoryManager(core.common.BaseManager):
    @transaction.atomic
    def create_from_rule(self, request, rule):
        snapshot = model_to_dict(rule, exclude=["ad_groups_included", "campaigns_included", "accounts_included"])

        # model_to_dict doesn't return datetime fields
        snapshot["created_dt"] = rule.created_dt
        snapshot["modified_dt"] = rule.modified_dt

        # model_to_dict returns a list of entities for many to many field, manually map ids
        snapshot["ad_groups_included"] = [ad_group.id for ad_group in rule.ad_groups_included.all()]
        snapshot["campaigns_included"] = [campaign.id for campaign in rule.campaigns_included.all()]
        snapshot["accounts_included"] = [account.id for account in rule.accounts_included.all()]

        # model_to_dict doesn't consider fields via foreign key, manually construct conditions
        snapshot["conditions"] = [model_to_dict(condition) for condition in rule.conditions.all()]

        rule_change_history = self.create(snapshot=snapshot, rule=rule, created_by=request.user if request else None)
        return rule_change_history
