from django.db import models

from ... import constants
from .. import common


class RuleHistoryQuerySet(common.PreventUpdatesQuerySetMixin, models.QuerySet):
    def exclude_without_changes(self):
        return self.exclude(
            (models.Q(changes__exact={}) | models.Q(changes__isnull=True))
            & models.Q(status=constants.ApplyStatus.SUCCESS)
        )
