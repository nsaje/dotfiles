from django.db import models


class DirectDealQuerySet(models.QuerySet):
    def filter_by_agency(self, agency):
        return self.filter(models.Q(agency=agency))

    def filter_by_account(self, account):
        deal_qs = self.filter(models.Q(account=account))
        if account.agency is not None:
            deal_qs |= self.filter_by_agency(account.agency)
        return deal_qs
