from django.db import models

import dash.constants


class WhiteLabel(models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Whitelabels"

    id = models.AutoField(primary_key=True)
    theme = models.CharField(
        max_length=255, choices=dash.constants.Whitelabel.get_choices(), editable=True, unique=False, blank=True
    )
    favicon_url = models.CharField(max_length=255, editable=True, blank=True, default="")
    dashboard_title = models.CharField(max_length=255, editable=True, blank=True, default="")
    terms_of_service_url = models.CharField(max_length=255, blank=True, null=True)
    copyright_holder = models.CharField(max_length=255, blank=True, null=True)
    copyright_holder_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.theme
