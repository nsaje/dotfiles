# -*- coding: utf-8 -*-
import traceback

from django.db import models


class HistoryQuerySetManager(models.Manager):
    def create(self, *args, **kwargs):
        stack_trace = "".join(traceback.format_stack())
        return super().create(stack_trace=stack_trace, *args, **kwargs)

    def get_queryset(self):
        return self.model.QuerySet(self.model)

    def delete(self):
        raise AssertionError("Deleting history objects not allowed")
