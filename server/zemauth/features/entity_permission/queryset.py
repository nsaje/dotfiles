from django.db import models


class EntityPermissionQuerySet(models.QuerySet):
    def filter_by_agency(self, agency):
        return self.filter(agency=agency)

    def filter_by_account(self, account):
        deal_qs = self.filter(account=account)
        if account.agency is not None:
            deal_qs |= self.filter_by_agency(account.agency)
        return deal_qs

    def filter_by_user(self, user):
        return self.filter(user=user)
