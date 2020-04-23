# -*- coding: utf-8 -*-

from utils.exc import ValidationError


class EntityPermissionValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()

    def _validate_agency_account(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError(
                errors={
                    "account_id": ["Only one of either account or agency can be set."],
                    "agency_id": ["Only one of either account or agency can be set."],
                }
            )
