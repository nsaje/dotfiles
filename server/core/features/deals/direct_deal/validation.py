from django.core.exceptions import ValidationError


class DirectDealValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()
        self._validate_account()
        self._validate_agency()

    def _validate_agency_account(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError(
                {
                    "account_id": ["Only one of either account or agency must be set."],
                    "agency_id": ["Only one of either account or agency must be set."],
                }
            )
        if self.account is None and self.agency is None:
            raise ValidationError(
                {
                    "account_id": ["One of either account or agency must be set."],
                    "agency_id": ["One of either account or agency must be set."],
                }
            )

    def _validate_account(self):
        if self.account is None or self.id is None:
            return

        connections = self.directdealconnection_set.all().select_related("campaign", "adgroup__campaign")
        if len(connections) == 0:
            return

        accounts = set()
        for connection in connections:
            account_id = None
            if connection.account is not None:
                account_id = connection.account_id
            elif connection.campaign is not None:
                account_id = connection.campaign.account_id
            elif connection.adgroup is not None:
                account_id = connection.adgroup.campaign.account_id
            if account_id is not None:
                accounts.add(account_id)

        if self.account.id not in accounts:
            raise ValidationError(
                {
                    "account_id": "Deal is used on the current account. Account cannot be changed to {account_name}.".format(
                        account_name=self.account.name
                    )
                }
            )

    def _validate_agency(self):
        if self.agency is None or self.id is None:
            return

        connections = self.directdealconnection_set.all().select_related(
            "account", "campaign__account", "adgroup__campaign__account"
        )
        if len(connections) == 0:
            return

        agencies = set()
        for connection in connections:
            agency_id = None
            if connection.account is not None:
                agency_id = connection.account.agency_id
            elif connection.campaign is not None:
                agency_id = connection.campaign.account.agency_id
            elif connection.adgroup is not None:
                agency_id = connection.adgroup.campaign.account.agency_id
            if agency_id is not None:
                agencies.add(agency_id)

        if self.agency.id not in agencies:
            raise ValidationError(
                {
                    "agency_id": "Deal is used on the current agency. Agency cannot be changed to {agency_name}.".format(
                        agency_name=self.agency.name
                    )
                }
            )
