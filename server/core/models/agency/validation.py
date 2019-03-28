from . import exceptions as ex


class AgencyValidatorMixin:
    def clean(self, changes):
        self._validate_is_disabled(changes)

    def _validate_is_disabled(self, changes):
        self.is_externally_managed = changes.get("is_externally_managed", self.is_externally_managed)
        if "is_disabled" not in changes:
            return
        if changes.get("is_disabled") is True and not self.is_externally_managed:
            raise ex.DisablingAgencyNotAllowed("Agency can be disabled only if it is externally managed.")
