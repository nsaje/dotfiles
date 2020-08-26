from django.db import models

from .. import common


class RuleTriggerHistoryQuerySet(common.PreventUpdatesQuerySetMixin, models.QuerySet):
    pass
