# -*- coding: utf-8 -*-

from django.db import models


class HistoryQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise AssertionError("Using update not allowed.")

    def delete(self, *args, **kwargs):
        raise AssertionError("Using delete not allowed.")

    def filter_selfmanaged(self):
        return (
            self.filter(created_by__isnull=False)
            .filter(created_by__email__isnull=False)
            .exclude(created_by__email__icontains="@zemanta")
            .exclude(created_by__is_test_user=True)
            .exclude(action_type__isnull=True)
        )
