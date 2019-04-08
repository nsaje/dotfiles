from . import exceptions as ex

OUTBRAIN_SALESFORCE_SERVICE_USER = "outbrain-salesforce@service.zemanta.com"


class AgencyValidatorMixin:
    def validate(self, changes, request=None):

        self._validate_is_disabled(changes)
        self._validate_externally_managed_fields(changes, request)

    def _validate_is_disabled(self, changes):
        if changes.get("is_disabled", self.is_disabled) and not changes.get(
            "is_externally_managed", self.is_externally_managed
        ):
            raise ex.DisablingAgencyNotAllowed("Agency can be disabled only if it is externally managed.")

    def _validate_externally_managed_fields(self, changes, request):
        if (
            request
            and request.user.email != OUTBRAIN_SALESFORCE_SERVICE_USER
            and changes.get("is_externally_managed", self.is_externally_managed)
        ):
            externally_managed_fields = [field for field in changes if field in self._externally_managed_fields]
            if externally_managed_fields:
                raise ex.EditingAgencyNotAllowed(
                    "Field(s) '{}' can only be edited through Outbrain Salesforce API".format(
                        ", ".join(externally_managed_fields)
                    )
                )
