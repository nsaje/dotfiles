from django.db import models


class DirectDealConnectionQuerySet(models.QuerySet):
    def filter_by_deal(self, deal):
        return self.filter(models.Q(deal=deal))
