from django.db import models


class AgencyQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(users__id=user.id)
            | models.Q(sales_representative__id=user.id)
            | models.Q(cs_representative__id=user.id)
        ).distinct()
