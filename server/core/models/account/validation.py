from . import exceptions as ex


class AccountValidatorMixin:
    def clean(self):
        self._validate_is_disabled()

    def _validate_is_disabled(self):
        if self.is_disabled and not self.is_externally_managed:
            raise ex.DisablingAccountNotAllowed("Disabling Account is allowed only on externally managed Agencies.")
