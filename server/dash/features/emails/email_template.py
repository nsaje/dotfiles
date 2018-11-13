# -*- coding: utf-8 -*-

from django.db import models

from dash import constants


class EmailTemplate(models.Model):
    template_type = models.PositiveSmallIntegerField(
        choices=constants.EmailTemplateType.get_choices(), null=True, blank=True
    )
    recipients = models.TextField(blank=True, null=False)
    subject = models.CharField(blank=True, null=False, max_length=255)
    body = models.TextField(blank=True, null=False)

    def __str__(self):
        return (
            (constants.EmailTemplateType.get_text(self.template_type) or "<noname>")
            if self.template_type
            else "Unassigned"
        )

    class Meta:
        unique_together = ("template_type",)
