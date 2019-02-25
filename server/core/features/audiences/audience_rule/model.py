from django.db import models

from dash import constants


class AudienceRule(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    audience = models.ForeignKey("Audience", on_delete=models.PROTECT)
    type = models.PositiveSmallIntegerField(choices=constants.AudienceRuleType.get_choices())
    value = models.CharField(max_length=255, blank=True)
