# -*- coding: utf-8 -*-

from django.db import models


class HistoryQuerySetManager(models.Manager):
    def get_queryset(self):
        return self.model.QuerySet(self.model)

    def delete(self):
        raise AssertionError("Deleting history objects not allowed")
