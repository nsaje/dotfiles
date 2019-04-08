from . import exceptions as ex


class AgencyValidatorMixin:
    def clean(self):
        self._validate_is_disabled()

    def _validate_is_disabled(self):
        if self.is_disabled and not self.is_externally_managed:
            raise ex.DisablingAgencyNotAllowed("Agency can be disabled only if it is externally managed.")
