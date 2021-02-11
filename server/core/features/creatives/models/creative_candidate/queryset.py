from django.db import models


class CreativeCandidateQuerySet(models.QuerySet):
    def filter_by_batch(self, batch):
        return self.filter(batch=batch)
