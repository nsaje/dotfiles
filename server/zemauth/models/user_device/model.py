# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from zemauth.models import Device


class UserDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
