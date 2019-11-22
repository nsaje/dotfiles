import jsonfield
from django.conf import settings
from django.db import models

import core.models
import dash.features.reports.helpers as reports_helpers
from dash import constants
from dash import history_helpers
from dash.features import reports
from utils import dates_helper
from utils.json_helper import JSONFIELD_DUMP_KWARGS


class ScheduledReportManager(models.Manager):
    def for_view(self, user, account):
        scheduled_reports = self.get_queryset().exclude_removed()

        if account:
            scheduled_reports = scheduled_reports.filter(account=account)
        else:
            scheduled_reports = scheduled_reports.filter(user=user)

        return scheduled_reports

    def create(self, *args, **kwargs):
        account = self._get_account(kwargs["user"], kwargs["query"])
        kwargs["account"] = account

        if account:
            account.write_history(
                "Scheduled report", user=kwargs["user"], action_type=constants.HistoryActionType.REPORTING_MANAGE
            )
        else:
            history_helpers.write_global_history(
                "Scheduled report", user=kwargs["user"], action_type=constants.HistoryActionType.REPORTING_MANAGE
            )

        return super(ScheduledReportManager, self).create(*args, **kwargs)

    def _get_account(self, user, query):
        constraints = reports_helpers.get_filter_constraints(query["filters"])
        if "ad_group_id" in constraints:
            ad_group = core.models.AdGroup.objects.select_related("campaign__account").get(
                pk=constraints["ad_group_id"]
            )
            return ad_group.campaign.account
        elif "campaign_id" in constraints:
            campaign = core.models.Campaign.objects.select_related("account").get(pk=constraints["campaign_id"])
            return campaign.account
        elif "account_id" in constraints:
            return core.models.Account.objects.get(pk=constraints["account_id"])
        else:
            return None


class ScheduledReportQuerySet(models.QuerySet):
    def filter_due(self):
        today = dates_helper.utc_today()

        due_reports = self.filter(state=constants.ScheduledReportState.ACTIVE)

        done_today_reports = (
            reports.ReportJob.objects.filter(scheduled_report__isnull=False)
            .filter(created_dt__gte=today)
            .exclude(status=reports.constants.ReportJobStatus.FAILED)
            .values_list("scheduled_report_id", flat=True)
        )

        due_reports = due_reports.exclude(id__in=done_today_reports)

        due_reports = due_reports.exclude(
            ~models.Q(day_of_week=today.isoweekday()),
            sending_frequency=constants.ScheduledReportSendingFrequency.WEEKLY,
        )

        if today.day != 1:  # montly reports are only sent on the 1st
            due_reports = due_reports.exclude(sending_frequency=constants.ScheduledReportSendingFrequency.MONTHLY)

        return due_reports

    def exclude_removed(self):
        return self.exclude(state=constants.ScheduledReportState.REMOVED)


class ScheduledReport(models.Model):
    id = models.AutoField(primary_key=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    name = models.CharField(max_length=100, null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=False)
    state = models.IntegerField(
        default=constants.ScheduledReportState.ACTIVE, choices=constants.ScheduledReportState.get_choices()
    )
    account = models.ForeignKey("Account", blank=True, null=True, on_delete=models.PROTECT)

    sending_frequency = models.IntegerField(
        default=constants.ScheduledReportSendingFrequency.DAILY,
        choices=constants.ScheduledReportSendingFrequency.get_choices(),
    )
    day_of_week = models.IntegerField(
        default=constants.ScheduledReportDayOfWeek.MONDAY, choices=constants.ScheduledReportDayOfWeek.get_choices()
    )
    time_period = models.IntegerField(
        default=constants.ScheduledReportTimePeriod.YESTERDAY, choices=constants.ScheduledReportTimePeriod.get_choices()
    )

    query = jsonfield.JSONField(dump_kwargs=JSONFIELD_DUMP_KWARGS)

    objects = ScheduledReportManager.from_queryset(ScheduledReportQuerySet)()

    def get_recipients(self):
        return self.query["options"]["recipients"]

    def set_date_filter(self, start_date, end_date):
        for filter in self.query["filters"]:
            if filter["field"] == "Date":
                filter["from"] = start_date
                filter["to"] = end_date

    def remove(self):
        self.state = constants.ScheduledReportState.REMOVED
        self.save()

        if self.account:
            self.account.write_history(
                "Deleted scheduled report", user=self.user, action_type=constants.HistoryActionType.REPORTING_MANAGE
            )
        else:
            history_helpers.write_global_history(
                "Deleted scheduled report", user=self.user, action_type=constants.HistoryActionType.REPORTING_MANAGE
            )
