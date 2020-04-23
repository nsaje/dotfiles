# -*- coding: utf-8 -*-

from django.contrib.auth import models as auth_models
from django.db import models


class InternalGroup(models.Model):
    group = models.OneToOneField(auth_models.Group, on_delete=models.PROTECT)

    def __str__(self):
        return self.group.name
