
import jsonfield
from django.conf import settings
from django.db import models

from utils.json_helper import JSONFIELD_DUMP_KWARGS

from . import constants


class ReportJob(models.Model):
    id = models.AutoField(primary_key=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(null=True, auto_now=True, verbose_name="Modified at")
    start_dt = models.DateTimeField(null=True, verbose_name="Started processing at")
    end_dt = models.DateTimeField(null=True, verbose_name="Finished processing at")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True)
    status = models.IntegerField(
        default=constants.ReportJobStatus.IN_PROGRESS, choices=constants.ReportJobStatus.get_choices()
    )
    query = jsonfield.JSONField(dump_kwargs=JSONFIELD_DUMP_KWARGS)
    result = jsonfield.JSONField(null=True, blank=True, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    exception = models.TextField(null=True, blank=True)

    scheduled_report = models.ForeignKey(
        "ScheduledReport", related_name="jobs", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "restapi_reportjob"
