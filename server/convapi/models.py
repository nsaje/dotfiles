from django.db import models

from convapi import constants


class RawPostclickStats(models.Model):

    datetime = models.DateTimeField()

    ad_group_id = models.IntegerField(default=0, blank=False, null=False)
    source_id = models.IntegerField(default=0, blank=False, null=True)

    url_raw = models.CharField(max_length=2048, blank=False, null=False)
    url_clean = models.CharField(max_length=2048, blank=False, null=False)

    device_type = models.CharField(max_length=64, blank=False, null=True)

    # _z1_parameters
    z1_adgid = models.CharField(max_length=32, blank=False, null=False)
    z1_msid = models.CharField(max_length=64, blank=False, null=False)

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

    device_type = models.CharField(max_length=64, blank=False, null=True)

    goal_name = models.CharField(max_length=127, blank=False, null=False)

    # _z1_parameters
    z1_adgid = models.CharField(max_length=32, blank=False, null=False)
    z1_msid = models.CharField(max_length=64, blank=False, null=False)

    # conversion metrics
    conversions = models.IntegerField(default=0, blank=False, null=False)
    conversions_value_cc = models.IntegerField(default=0, blank=False, null=False)


class GAReportLog(models.Model):

    datetime = models.DateTimeField(auto_now=True)

    for_date = models.DateField(null=True)

    email_subject = models.CharField(max_length=1024, blank=False, null=True)

    from_address = models.CharField(max_length=1024, blank=False, null=True)

    csv_filename = models.CharField(max_length=1024, blank=False, null=True)

    ad_groups = models.CharField(max_length=128, blank=False, null=True)

    s3_key =  models.CharField(max_length=1024, blank=False, null=True)

    visits_reported = models.IntegerField(blank=False, null=True)
    visits_imported = models.IntegerField(blank=False, null=True)

    multimatch = models.IntegerField(default=0, blank=False, null=False)
    multimatch_clicks = models.IntegerField(default=0, blank=False, null=False)
    nomatch = models.IntegerField(default=0, blank=False, null=False)

    state = models.IntegerField(
        default=constants.ReportState.RECEIVED,
        choices=constants.ReportState.get_choices(),
    )

    errors = models.TextField(blank=False, null=True)

    def add_error(self, error_msg):
        if self.errors is None:
            self.errors = error_msg
        else:
            self.errors += '\n\n' + error_msg

    def add_ad_group_id(self, aid):
        if self.ad_groups is None:
            self.ad_groups = str(aid)
        else:
            self.ad_groups += ',' + str(aid)

    def add_visits_imported(self, n):
        if self.visits_imported is None:
            self.visits_imported = n
        else:
            self.visits_imported += n

    def add_visits_reported(self, n):
        if self.visits_reported is None:
            self.visits_reported = n
        else:
            self.visits_reported += n


class ReportLog(models.Model):

    datetime = models.DateTimeField(auto_now=True)
    for_date = models.DateField(null=True)
    email_subject = models.CharField(max_length=1024, blank=False, null=True)
    from_address = models.CharField(max_length=1024, blank=False, null=True)
    report_filename = models.CharField(max_length=1024, blank=False, null=True)

    visits_reported = models.IntegerField(blank=False, null=True)
    visits_imported = models.IntegerField(blank=False, null=True)

    s3_key =  models.CharField(max_length=1024, blank=False, null=True)

    state = models.IntegerField(
        default=constants.ReportState.RECEIVED,
        choices=constants.ReportState.get_choices(),
    )

    errors = models.TextField(blank=False, null=True)

    def add_error(self, error_msg):
        if self.errors is None:
            self.errors = error_msg
        else:
            self.errors += '\n\n' + error_msg

    def add_ad_group_id(self, aid):
        if self.ad_groups is None:
            self.ad_groups = str(aid)
        else:
            self.ad_groups += ',' + str(aid)

    def add_visits_imported(self, n):
        if self.visits_imported is None:
            self.visits_imported = n
        else:
            self.visits_imported += n

    def add_visits_reported(self, n):
        if self.visits_reported is None:
            self.visits_reported = n
        else:
            self.visits_reported += n
