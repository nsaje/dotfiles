from utils.exc import ValidationError


class CreativeTagValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()

    def _validate_agency_account(self):
        if self.account is None and self.agency is None:
            raise ValidationError(
                errors={
                    "account_id": ["Either account or agency must be set."],
                    "agency_id": ["Either account or agency must be set."],
                }
            )
        if self.account is not None and self.agency is not None:
            raise ValidationError(
                errors={
                    "account_id": ["Only one of either account or agency can be set."],
                    "agency_id": ["Only one of either account or agency can be set."],
                }
            )
