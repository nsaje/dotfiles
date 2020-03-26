from django.contrib.postgres.fields import ArrayField
from django.db import models


class SupplyReportRecipient(models.Model):
    first_name = models.CharField("first name", max_length=30, blank=True)
    last_name = models.CharField("last name", max_length=30, blank=True)
    email = models.EmailField("email address", max_length=255)
    source = models.ForeignKey("dash.Source", on_delete=models.PROTECT)
    outbrain_publisher_ids = ArrayField(models.IntegerField(), null=True, blank=True)
    custom_subject = models.CharField(max_length=100, blank=True)

    publishers_report = models.BooleanField(default=False)
    mtd_report = models.BooleanField(default=False, verbose_name="MTD report")
    daily_breakdown_report = models.BooleanField(default=False, verbose_name="MTD daily breakdown report")

    last_sent_dt = models.DateTimeField(blank=True, null=True, verbose_name="Last sent at")
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
