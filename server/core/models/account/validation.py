from . import exceptions as ex


class AccountValidatorMixin:
    def clean(self, changes):
        self._validate_is_disabled(changes)

    def _validate_is_disabled(self, changes):
        if "is_disabled" not in changes:
            return
        if changes.get("is_disabled") is True and not self.is_externally_managed:
            raise ex.DisablingAccountNotAllowed("Disabling Account is allowed only on externally managed Agencies.")
