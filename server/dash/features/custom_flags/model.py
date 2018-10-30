from django.db import models

from dash import constants


class CustomFlag(models.Model):
    DEFAULTS = {"string": "", "int": 0, "float": 0.0, "boolean": False}

    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    advanced = models.BooleanField(default=False)
    type = models.CharField(null=True, choices=constants.Customflags.get_choices(), max_length=120)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    def get_default_value(self):
        return CustomFlag.DEFAULTS[self.type]
