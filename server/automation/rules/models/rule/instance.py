from django.db import transaction
from django.utils.functional import cached_property

from ... import constants
from ...common import macros
from ..rule_condition import RuleCondition


class RuleInstanceMixin:
    def save(self, request, *args, **kwargs):
        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
            else:
                self.modified_by = request.user
        super().save(*args, **kwargs)

    @cached_property
    def requires_cpa_stats(self):
        return self._has_cpa_operands() or self._has_cpa_macros()

    def _has_cpa_operands(self):
        for condition in self.conditions.all():
            if condition.left_operand_type in constants.CONVERSION_METRICS:
                return True
        return False

    def _has_cpa_macros(self):
        if self.action_type == constants.ActionType.SEND_EMAIL:
            if self.send_email_subject:
                if macros.has_cpa_macros(self.send_email_subject):
                    return True
            if self.send_email_body:
                if macros.has_cpa_macros(self.send_email_body):
                    return True
        return False

    @transaction.atomic
    def update(self, request, **updates):
        self.clean(updates)

        cleaned_updates = self._clean_updates(updates)
        self._apply_updates(cleaned_updates)
        self.save(request)

        self._apply_related_updates(updates)

    def _clean_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in updates.items():
            setattr(self, field, value)

    def _apply_related_updates(self, updates):
        if "conditions" in updates:
            self._update_conditions(updates["conditions"])
        if "ad_groups_included" in updates:
            self._update_ad_groups_included(updates["ad_groups_included"])

    def _update_conditions(self, conditions):
        self.conditions.all().delete()
        for condition in conditions:
            RuleCondition.objects.create(rule_id=self.id, **condition)

    def _update_ad_groups_included(self, ad_groups_included):
        for ad_group in ad_groups_included:
            self.ad_groups_included.add(ad_group)
