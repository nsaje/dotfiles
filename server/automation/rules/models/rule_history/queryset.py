from django.db import models

from ... import constants
from .. import common


class RuleHistoryQuerySet(common.PreventUpdatesQuerySetMixin, models.QuerySet):
    def exclude_without_changes(self):
        return self.exclude(status=constants.ApplyStatus.SUCCESS_NO_CHANGES)
