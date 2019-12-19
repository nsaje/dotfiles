from . import exceptions as ex

OUTBRAIN_SALESFORCE_SERVICE_USER = "outbrain-salesforce@service.zemanta.com"


class AgencyValidatorMixin:
    def validate(self, changes, request=None):
        self._validate_externally_managed_fields(changes, request)
        self._validate_sources(changes)

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

    def _validate_sources(self, changes):
        available_sources = set(
            changes["available_sources"] if "available_sources" in changes else self.available_sources.all()
        )
        allowed_sources = set(
            changes["allowed_sources"] if "allowed_sources" in changes else self.allowed_sources.all()
        )

        if not allowed_sources.issubset(available_sources):
            raise ex.EditingSourcesNotAllowed(
                "Allowed source(s) must be a subset of available sources. "
                "(if removing from available it also needs to be removed from allowed)."
            )
