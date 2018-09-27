# -*- coding: utf-8 -*-
import jsonfield
from django.db import models

import core.common


class DefaultSourceSettings(models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Default Source Settings"

    source = models.OneToOneField("Source", unique=True, on_delete=models.PROTECT)
    credentials = models.ForeignKey("SourceCredentials", on_delete=models.PROTECT, null=True, blank=True)
    params = jsonfield.JSONField(
        blank=True,
        null=False,
        default={},
        verbose_name="Additional action parameters",
        help_text='Information about format can be found here: <a href="https://sites.google.com/a/zemanta.com/root/content-ads-dsp/additional-source-parameters-format" target="_blank">Zemanta Pages</a>',
    )

    default_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Default CPC",
        help_text="This setting has moved. See Source model.",
    )

    mobile_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Default CPC (if ad group is targeting mobile only)",
        help_text="This setting has moved. See Source model.",
    )

    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Default daily spend cap",
        help_text="This setting has moved. See Source model.",
    )

    objects = core.common.QuerySetManager()

    class QuerySet(models.QuerySet):
        def with_credentials(self):
            return self.exclude(credentials__isnull=True)

    def __str__(self):
        return self.source.name
