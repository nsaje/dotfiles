from django.db import models


class SourceQuerySet(models.QuerySet):
    def filter_can_manage_content_ads(self):
        return self.filter(id__in=[x.id for x in self.select_related("source_type") if x.can_manage_content_ads()])
