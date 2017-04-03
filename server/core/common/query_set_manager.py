# -*- coding: utf-8 -*-

from django.db import models


class QuerySetManager(models.Manager):

    def get_queryset(self):
        return self.model.QuerySet(self.model)
