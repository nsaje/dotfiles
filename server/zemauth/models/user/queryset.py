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
