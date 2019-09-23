from django.db import models


class DirectDealConnectionQuerySet(models.QuerySet):
    def filter_by_deal(self, deal):
        return self.filter(models.Q(deal=deal))

    def delete(self, request=None):
        for item in self:
            item.write_delete_history(request)
        super().delete()
