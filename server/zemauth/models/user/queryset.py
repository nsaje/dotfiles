from django.db import models


class UserQuerySet(models.QuerySet):
    def filter_by_agencies(self, agencies):
        if not agencies:
            return self
        return self.filter(
            models.Q(agency__id__in=agencies)
            | models.Q(groups__permissions__codename="can_see_all_accounts")
            | models.Q(user_permissions__codename="can_see_all_accounts")
        )

    def filter_selfmanaged(self):
        return self.filter(email__isnull=False).exclude(email__icontains="@zemanta").exclude(is_test_user=True)

    def filter_by_account(self, account):
        user_qs = self.filter(entitypermission__account=account)
        if account.agency is not None:
            user_qs |= self.filter(entitypermission__agency=account.agency)
        return user_qs.distinct()

    def filter_by_agency(self, agency):
        return self.filter(entitypermission__agency=agency).distinct()

    def filter_by_agency_and_related_accounts(self, agency):
        return self.filter(
            models.Q(entitypermission__agency=agency) | models.Q(entitypermission__account__agency=agency)
        ).distinct()
