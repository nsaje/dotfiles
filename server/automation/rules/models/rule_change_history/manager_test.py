from itertools import chain

import core.models
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleCondition
from . import RuleChangeHistory


class RuleChangeHistoryManagerTest(BaseTestCase):
    def test_persist_snapshot(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        rule = magic_mixer.blend(
            Rule, ad_groups_included=[ad_group], campaigns_included=[campaign], accounts_included=[account]
        )
        rule_condition = magic_mixer.blend(RuleCondition, rule=rule)

        rule_change_history = RuleChangeHistory.objects.create_from_rule(request, rule)
        snapshot = rule_change_history.snapshot

        expected_rule_fields = []
        for field in chain(rule._meta.concrete_fields, rule._meta.private_fields, rule._meta.many_to_many):
            expected_rule_fields.append(field.name)

        for field in rule._meta.related_objects:
            if field.name not in {"history", "change_history", "trigger_history"}:
                expected_rule_fields.append(field.name)
        self.assertCountEqual(expected_rule_fields, snapshot.keys())

        expected_condition_fields = []
        for field in chain(
            rule_condition._meta.concrete_fields, rule_condition._meta.private_fields, rule_condition._meta.many_to_many
        ):
            expected_condition_fields.append(field.name)
        self.assertCountEqual(expected_condition_fields, snapshot["conditions"][0].keys())
