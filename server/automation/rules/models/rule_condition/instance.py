from django.db import transaction


class RuleConditionInstanceMixin:
    @transaction.atomic
    def update(self, **updates):
        self.clean(updates)
        filtered_updates = self._filter_updates(updates)
        self._apply_updates(filtered_updates)
        self.save()

    def _filter_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in updates.items():
            setattr(self, field, value)
