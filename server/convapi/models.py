from django.db import models


class RawPostclickStats(models.Model):

    datetime = models.DateTimeField()

    ad_group_id = models.IntegerField(default=0, blank=False, null=False)
    source_id = models.IntegerField(default=0, blank=False, null=True)

    url_raw = models.CharField(max_length=2048, blank=False, null=False)
    url_clean = models.CharField(max_length=2048, blank=False, null=False)

    device_type = models.CharField(max_length=64, blank=False, null=False)

    # _z1_parameters
    z1_adgid = models.CharField(max_length=32, blank=False, null=False)
    z1_msid = models.CharField(max_length=64, blank=False, null=False)
    z1_did = models.CharField(max_length=64, blank=False, null=True)
    z1_kid = models.CharField(max_length=64, blank=False, null=True)
    z1_tid = models.CharField(max_length=64, blank=False, null=True)

    # postclick metrics
    visits = models.IntegerField(default=0, blank=False, null=False)
    new_visits = models.IntegerField(default=0, blank=False, null=False)
    bounced_visits = models.IntegerField(default=0, blank=False, null=False)
    pageviews = models.IntegerField(default=0, blank=False, null=False)
    duration = models.IntegerField(default=0, blank=False, null=False)


class RawGoalConversionStats(models.Model):

    datetime = models.DateTimeField()

    ad_group_id = models.IntegerField(default=0, blank=False, null=False)
    source_id = models.IntegerField(default=0, blank=False, null=True)

    url_raw = models.CharField(max_length=2048, blank=False, null=False)
    url_clean = models.CharField(max_length=2048, blank=False, null=False)

    device_type = models.CharField(max_length=64, blank=False, null=False)

    goal_name = models.CharField(max_length=127, blank=False, null=False)

    # _z1_parameters
    z1_adgid = models.CharField(max_length=32, blank=False, null=False)
    z1_msid = models.CharField(max_length=64, blank=False, null=False)
    z1_did = models.CharField(max_length=64, blank=False, null=True)
    z1_kid = models.CharField(max_length=64, blank=False, null=True)
    z1_tid = models.CharField(max_length=64, blank=False, null=True)

    # conversion metrics
    conversions = models.IntegerField(default=0, blank=False, null=False)
    conversions_value_cc = models.IntegerField(default=0, blank=False, null=False)
