# -*- coding: utf-8 -*-
import logging
import traceback

from django.db import models

from .. import history_stacktrace

logger = logging.getLogger(__name__)


class HistoryQuerySetManager(models.Manager):
    def create(self, *args, **kwargs):
        history = super().create(*args, **kwargs)
        try:
            stack_trace = "".join(traceback.format_stack())
            history_stacktrace.model.HistoryStacktrace.objects.create(history=history, value=stack_trace)
        except Exception:
            logger.exception("Could not save history stack trace!")
        return history

    def get_queryset(self):
        return self.model.QuerySet(self.model)

    def delete(self):
        raise AssertionError("Deleting history objects not allowed")
