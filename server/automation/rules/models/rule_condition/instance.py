from django.db import transaction
from django.forms.models import model_to_dict


class RuleConditionInstanceMixin:
    @transaction.atomic
    def update(self, **updates):
        self.clean(updates)
        filtered_updates = self._filter_updates(updates)
        self._apply_updates(filtered_updates)
        self.save()

    def to_dict(self):
        return model_to_dict(self)

    def _filter_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in updates.items():
            setattr(self, field, value)
