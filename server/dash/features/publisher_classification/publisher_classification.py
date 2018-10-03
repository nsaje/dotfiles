from django.db import models

from dash import constants


class PublisherClassification(models.Model):
    publisher = models.CharField(max_length=128, blank=False)
    classification = models.CharField(
        max_length=128, blank=False, null=True, choices=constants.InterestCategory.get_choices()
    )
    ignored = models.BooleanField(default=False)
