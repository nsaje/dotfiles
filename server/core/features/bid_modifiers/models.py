from django.db import models

import core.models


class BidModifier(models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("ad_group", "source", "publisher")

    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(core.models.AdGroup, on_delete=models.PROTECT)
    source = models.ForeignKey(core.models.Source, on_delete=models.PROTECT)
    publisher = models.CharField(max_length=127, blank=False, null=False, verbose_name="Publisher name or domain")
    modifier = models.FloatField(verbose_name="Publisher bid modifier")
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
