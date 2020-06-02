from django.db import models


class RuleQuerySet(models.QuerySet):
    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)
