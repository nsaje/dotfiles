# -*- coding: utf-8 -*-

from django.conf import settings

from utils.exc import ValidationError


class EntityPermissionValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()
        self._validate_internal_user()

    def _validate_agency_account(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError(
                errors={
                    "account_id": ["Only one of either account or agency can be set."],
                    "agency_id": ["Only one of either account or agency can be set."],
                }
            )

    def _validate_internal_user(self):
        if (
            self.account is None
            and self.agency is None
            and not any(self.user.email.endswith(postfix) for postfix in settings.INTERNAL_EMAIL_POSTFIXES)
        ):
            raise ValidationError(
                errors={"user_id": ["Only Outbrain accounts can have internal permissions assigned."]}
            )
