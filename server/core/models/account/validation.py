from . import exceptions

OUTBRAIN_SALESFORCE_SERVICE_USER = "outbrain-salesforce@service.zemanta.com"


class AccountValidatorMixin:
    def validate(self, changes, request=None):
        self._validate_externally_managed_fields(request, changes)
        self._validate_is_disabled(changes)

    def _validate_is_disabled(self, changes):
        if changes.get("is_disabled", False):
            if changes["is_disabled"] and not self.is_externally_managed:
                raise exceptions.DisablingAccountNotAllowed(
                    "Disabling Account is allowed only on externally managed Agencies."
                )

    def _validate_externally_managed_fields(self, request, changes):
        if (
            request
            and request.user.email != OUTBRAIN_SALESFORCE_SERVICE_USER
            and changes.get("is_externally_managed", self.is_externally_managed)
        ):
            externally_managed_fields = [field for field in changes.keys() if field in self._externally_managed_fields]
            if externally_managed_fields:
                raise exceptions.EditingAccountNotAllowed(
                    "Field(s) '{}' can only be edited through Outbrain Salesforce API".format(
                        ", ".join(externally_managed_fields)
                    )
                )
