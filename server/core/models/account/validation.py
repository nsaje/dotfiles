import core.features.bcm

from . import exceptions

OUTBRAIN_SALESFORCE_SERVICE_USER = "outbrain-salesforce@service.zemanta.com"


class AccountValidatorMixin:
    def validate(self, changes, request=None):
        self._validate_externally_managed_fields(request, changes)
        self._validate_agency(request, changes)

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

    def _validate_agency(self, request, changes):
        if changes.get("agency"):
            if self.is_agency() and self.agency != changes["agency"]:
                if core.features.bcm.BudgetLineItem.objects.filter(campaign__account=self):
                    raise exceptions.EditingAccountNotAllowed(
                        "Cannot switch Agency if Account has campaigns with budgets."
                    )
