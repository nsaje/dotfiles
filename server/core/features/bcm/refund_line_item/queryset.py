from django.db import models


class RefundLineItemQuerySet(models.QuerySet):
    def filter_by_credit(self, credit):
        return self.filter(models.Q(credit=credit))

    def filter_by_account(self, account):
        return self.filter(models.Q(account=account))

    def filter_by_agency(self, agency):
        return self.filter(models.Q(account__agency=agency))
