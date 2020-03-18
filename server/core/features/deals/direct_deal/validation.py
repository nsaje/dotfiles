from django.core.exceptions import ValidationError


class DirectDealValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()
        self._validate_account()

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
        if self.account is None:
            return

        connections = self.directdealconnection_set.all()
        if len(connections) == 0:
            return

        accounts = set()
        for connection in connections:
            account_id = None
            if connection.account is not None:
                account_id = connection.account.id
            elif connection.campaign is not None:
                account_id = connection.campaign.account.id
            elif connection.adgroup is not None:
                account_id = connection.adgroup.campaign.account.id
            if account_id is not None:
                accounts.add(account_id)

        if len(accounts) > 1:
            raise ValidationError(
                {
                    "account_id": "Deal is used on different accounts. Account cannot be changed to {account_name}.".format(
                        account_name=self.account
                    )
                }
            )
        if len(accounts) == 1 and self.account.id not in accounts:
            raise ValidationError(
                {
                    "account_id": "Deal is used on a different account. Account cannot be changed to {account_name}.".format(
                        account_name=self.account
                    )
                }
            )
