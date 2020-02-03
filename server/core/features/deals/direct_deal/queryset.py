from django.db import models


class DirectDealQuerySet(models.QuerySet):
    def filter_by_agency(self, agency):
        return self.filter(models.Q(agency=agency))

    def filter_by_account(self, account):
        return self.filter(models.Q(account=account))
