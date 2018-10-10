from django.db import models

from dash import constants


class PublisherClassification(models.Model):
    publisher = models.CharField(max_length=128, blank=False)
    category = models.CharField(
        max_length=128, blank=False, default="?", choices=constants.InterestCategory.get_choices()
    )
    ignored = models.BooleanField(default=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    class Meta:
        unique_together = ("publisher", "category")
