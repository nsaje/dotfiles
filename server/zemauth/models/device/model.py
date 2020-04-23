# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class Device(models.Model):
    device_key = models.CharField(max_length=40, primary_key=True)
    expire_date = models.DateTimeField(db_index=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="UserDevice")
