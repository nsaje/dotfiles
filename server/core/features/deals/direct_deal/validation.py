from django.core.exceptions import ValidationError


class DirectDealValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_object_scope()

    def _validate_object_scope(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError({"non_field_validation": "Object scope must be either agency or account, not both."})
