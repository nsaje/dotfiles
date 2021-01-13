import abc
import datetime
import ftplib
import io
import os.path
import random
import string
import traceback

from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings

import dash.constants
import dash.models
import dash.views.helpers
import stats.api_breakdowns
import stats.api_reports
import stats.constants
import stats.helpers
import utils.columns
import utils.dates_helper
import utils.email_helper
import utils.exc
import utils.s3helpers
import utils.sort_helper
from server import celery
from utils import csv_utils
from utils import metrics_compat
from utils import threads
from utils import zlogging
from zemauth.features.entity_permission import Permission

from . import constants
from . import format_helper
from . import helpers
from .reportjob import ReportJob

logger = zlogging.getLogger(__name__)

BATCH_ROWS = 100000


def create_job(user, query, scheduled_report=None):
    job = ReportJob(user=user, query=query, scheduled_report=scheduled_report)
    job.save()

    if settings.USE_CELERY_FOR_REPORTS:
        execute.delay(job.id)
    else:
        executor = ReportJobExecutor(job)
        thread = threads.AsyncFunction(executor.execute)
        thread.start()

    return job


# if soft time limit is changed, visibility timeout on the SQS queue should be changed as well!
@celery.app.task(acks_late=True, name="reports_execute", soft_time_limit=39 * 60, ignore_result=True)
def execute(job_id, **kwargs):
    logger.info("Start job executor for report", job=job_id)
    job = ReportJob.objects.get(pk=job_id)
    executor = ReportJobExecutor(job)
    executor.execute(**kwargs)
    logger.info("Done job executor for report", job=job_id)


def clean_up_old_in_progress_reports(created_before):
    report_jobs = ReportJob.objects.filter(status=constants.ReportJobStatus.IN_PROGRESS, created_dt__lte=created_before)

    for report_job in report_jobs:
        process_report_job_fail(
            report_job, "stale", "Job Timeout: Requested report is taking too long to complete. Report job ID is {id}."
        )

    return len(report_jobs)


def process_report_job_fail(report_job, status, result, exception=None):
    report_job.status = constants.ReportJobStatus.FAILED
    report_job.end_dt = datetime.datetime.now()
    report_job.result = result.format(id=report_job.id)
    if exception is not None:
        report_job.exception = traceback.format_exc()
    utils.metrics_compat.incr("dash.reports", 1, status=status)
    report_job.save()
    try:
        _send_fail_mail(report_job)
    except Exception:
        logger.exception("Exception when sending fail notification for report job %s" % report_job.id)


def _send_fail_mail(report_job):
    if len(helpers.get_option(report_job, "recipients")) <= 0:
        return

    if report_job.scheduled_report:
        return

    filter_constraints = helpers.get_filter_constraints(report_job.query["filters"])

    filtered_sources = []
    if filter_constraints.get("sources"):
        filtered_sources = dash.views.helpers.get_filtered_sources(filter_constraints.get("sources", []))

    view, breakdowns = helpers.extract_view_breakdown(report_job)
    ad_group_name, campaign_name, account_name = helpers.extract_entity_names(report_job.user, filter_constraints)

    utils.email_helper.send_async_report_fail(
        user=report_job.user,
        recipients=helpers.get_option(report_job, "recipients"),
        start_date=filter_constraints["start_date"],
        end_date=filter_constraints["end_date"],
        filtered_sources=filtered_sources,
        show_archived=helpers.get_option(report_job, "show_archived", False),
        show_blacklisted_publishers=helpers.get_option(
            report_job, "show_blacklisted_publishers", dash.constants.PublisherBlacklistFilter.SHOW_ALL
        ),
        view=view,
        breakdowns=breakdowns,
        columns=helpers.extract_column_names(report_job.query["fields"]),
        include_totals=helpers.get_option(report_job, "include_totals"),
        ad_group_name=ad_group_name,
        campaign_name=campaign_name,
        account_name=account_name,
    )


class JobExecutor(object, metaclass=abc.ABCMeta):
    def __init__(self, job):
        self.job = job

    @abc.abstractmethod
    def execute(self):
        return


class MockJobExecutor(JobExecutor):
    def execute(self):
        pass


class ReportJobExecutor(JobExecutor):
    @metrics_compat.timer("dash.reports.execute")
    def execute(self, **kwargs):
        if self.job.status != constants.ReportJobStatus.IN_PROGRESS:
            logger.info("Running report job in incorrect state: %s" % self.job.status)
            metrics_compat.incr("dash.reports", 1, status="incorrect_state")
            return

        job_age = utils.dates_helper.utc_now() - self.job.created_dt
        if job_age > datetime.timedelta(hours=1):
            logger.info("Running too old report job: %s" % job_age)
            process_report_job_fail(self.job, "too_old", "Service Timeout: Please try again later.")
            return

        self.job.start_dt = datetime.datetime.now()
        self.job.save()
        try:
            csv_report, filename = self.get_report(self.job)

            report_path = self.save_to_s3(csv_report, filename)
            if self.job.scheduled_report_id in settings.FTP_REPORTS.keys():
                report = settings.FTP_REPORTS[self.job.scheduled_report_id]
                self.save_to_ftp(
                    report["config"].get("ftp_server"),
                    report["config"].get("ftp_port"),
                    report["config"].get("ftp_user"),
                    report["config"].get("ftp_password"),
                    report["destination"],
                    "{}-{}.csv".format(
                        report["destination"] or self.job.scheduled_report.name,
                        datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d"),
                    ),
                    csv_report,
                )
            self.send_by_email(self.job, report_path, **kwargs)
            self.job.result = report_path
            self.job.status = constants.ReportJobStatus.DONE
            self.job.end_dt = datetime.datetime.now()
            metrics_compat.incr("dash.reports", 1, status="success")
            self.job.save()
        except utils.exc.BaseError as e:
            process_report_job_fail(self.job, "user_error", str(e), e)
        except SoftTimeLimitExceeded as e:
            process_report_job_fail(
                self.job, "timeout", "Job Timeout: Requested report probably too large. Report job ID is {id}.", e
            )
        except Exception as e:
            process_report_job_fail(
                self.job, "failed", "Internal Error: Please contact support. Report job ID is {id}.", e
            )
            logger.exception("Exception when processing API report job", job=self.job.id)

    @classmethod
    def get_report(cls, job):
        user = job.user

        filter_constraints = helpers.get_filter_constraints(job.query["filters"])
        start_date = filter_constraints["start_date"]
        end_date = filter_constraints["end_date"]
        filtered_sources = dash.views.helpers.get_filtered_sources(filter_constraints.get("sources", []))
        filtered_account_types = dash.views.helpers.get_filtered_account_types(
            filter_constraints.get("account_types", [])
        )
        filtered_agencies = dash.views.helpers.get_filtered_agencies(filter_constraints.get("agencies", []))
        filtered_businesses = filter_constraints.get("businesses", None)

        level = helpers.get_level_from_constraints(filter_constraints)
        breakdown = list(helpers.get_breakdown_from_fields(job.query["fields"][:], level))
        structure_constraints = cls._extract_structure_constraints(filter_constraints)
        all_accounts_in_local_currency = (
            helpers.get_option(job, "all_accounts_in_local_currency")
            and stats.constants.StructureDimension.ACCOUNT in breakdown
        )
        csv_separator, csv_decimal_separator = cls._get_csv_separators(job)

        constraints = stats.api_reports.prepare_constraints(
            user,
            breakdown,
            start_date,
            end_date,
            filtered_sources,
            show_archived=helpers.get_option(job, "show_archived", False),
            show_blacklisted_publishers=helpers.get_option(
                job, "show_blacklisted_publishers", dash.constants.PublisherBlacklistFilter.SHOW_ALL
            ),
            filtered_account_types=filtered_account_types,
            filtered_agencies=filtered_agencies,
            filtered_businesses=filtered_businesses,
            only_used_sources=True,
            **structure_constraints,
        )
        cls._add_include_entity_tags_constraints_if_necessary(job, constraints)
        goals = stats.api_reports.get_goals(constraints, breakdown)

        column_to_field_name_map = utils.columns.custom_column_to_field_name_mapping(
            goals.pixels, goals.conversion_goals, show_publishers_fields=stats.constants.PUBLISHER in breakdown
        )

        order = cls._get_order(job, column_to_field_name_map)
        column_names = helpers.extract_column_names(job.query["fields"])
        cls._append_currency_column_if_necessary(column_names, column_to_field_name_map)
        cls._append_entity_tag_columns_if_necessary(user, constraints, breakdown, column_names)
        helpers.insert_delivery_name_columns_if_necessary(column_names, column_to_field_name_map)

        currency = None
        account_currency_map = None
        if all_accounts_in_local_currency:
            account_currency_map = {account.id: account.currency for account in constraints["allowed_accounts"]}
        else:
            currency = stats.helpers.get_report_currency(user, constraints["allowed_accounts"])

        if not breakdown:
            raise utils.exc.ValidationError("Must include at least one dimension.")

        try:
            columns = [column_to_field_name_map[column_name] for column_name in column_names]
        except KeyError as e:
            raise utils.exc.ValidationError('Invalid field "%s".' % e.args[0])

        output = io.StringIO()
        dashapi_cache = {}

        offset = 0
        while 1:
            rows = stats.api_reports.query(
                user=user,
                breakdown=breakdown,
                constraints=constraints,
                goals=goals,
                order=order,
                offset=offset,
                limit=BATCH_ROWS,
                level=level,
                include_items_with_no_spend=helpers.get_option(job, "include_items_with_no_spend", False),
                dashapi_cache=dashapi_cache,
            )

            if all_accounts_in_local_currency:
                stats.helpers.update_rows_to_contain_local_values(rows)
            else:
                stats.helpers.update_rows_to_contain_values_in_currency(rows, currency)
            helpers.fill_currency_column(rows, columns, currency, account_currency_map)
            helpers.fill_delivery_name_values_if_necessary(rows, breakdown)
            format_helper.format_values(rows, columns, csv_decimal_separator=csv_decimal_separator)

            cls.convert_to_csv(
                job,
                rows,
                column_names,
                column_to_field_name_map,
                output,
                csv_separator,
                header=offset == 0,
                currency=currency,
            )

            if len(rows) < BATCH_ROWS or helpers.get_option(job, "include_items_with_no_spend", False):
                break

            offset += BATCH_ROWS

        if helpers.get_option(job, "include_totals") and not all_accounts_in_local_currency:
            totals_constraints = stats.api_reports.prepare_constraints(
                user,
                breakdown,
                start_date,
                end_date,
                filtered_sources,
                show_archived=True,
                show_blacklisted_publishers=helpers.get_option(
                    job, "show_blacklisted_publishers", dash.constants.PublisherBlacklistFilter.SHOW_ALL
                ),
                filtered_account_types=filtered_account_types,
                filtered_agencies=filtered_agencies,
                filtered_businesses=filtered_businesses,
                only_used_sources=True,
                **structure_constraints,
            )
            totals = stats.api_reports.totals(
                user, helpers.limit_breakdown_to_level(breakdown, level), totals_constraints, goals, level
            )

            stats.helpers.update_rows_to_contain_values_in_currency([totals], currency)
            helpers.fill_currency_column([totals], columns, currency, account_currency_map)
            format_helper.format_values([totals], columns, csv_decimal_separator=csv_decimal_separator)

            cls.convert_to_csv(
                job,
                [totals],
                column_names,
                column_to_field_name_map,
                output,
                csv_separator,
                header=False,
                currency=currency,
            )

        return output.getvalue(), stats.api_reports.get_filename(breakdown, constraints)

    @staticmethod
    def _get_csv_separators(job):
        csv_separator = None
        csv_decimal_separator = None

        entity_permission = (
            job.user.entitypermission_set.filter(permission=Permission.READ, agency__isnull=False)
            .select_related("agency")
            .first()
        )
        agency = entity_permission.agency if entity_permission else None

        if agency:
            csv_separator = agency.default_csv_separator
            csv_decimal_separator = agency.default_csv_decimal_separator

        option_csv_separator = helpers.get_option(job, "csv_separator")
        option_csv_decimal_separator = helpers.get_option(job, "csv_decimal_separator")

        if option_csv_separator:
            csv_separator = option_csv_separator
        if option_csv_decimal_separator:
            csv_decimal_separator = option_csv_decimal_separator

        return csv_separator, csv_decimal_separator

    @staticmethod
    def _append_currency_column_if_necessary(requested_columns, field_name_mapping):
        CURRENCY_COLUMN_NAME = "Currency"

        if CURRENCY_COLUMN_NAME in requested_columns:
            return requested_columns

        for column_name in requested_columns:
            if utils.columns.is_cost_column(column_name, field_name_mapping):
                requested_columns.append(CURRENCY_COLUMN_NAME)
                break

        return requested_columns

    @staticmethod
    def _add_include_entity_tags_constraints_if_necessary(job, constraints):
        include_entity_tags = helpers.get_option(job, "include_entity_tags", None)
        if job.user.has_perm("zemauth.can_include_tags_in_reports"):
            constraints.update({"include_entity_tags": include_entity_tags})

    @staticmethod
    def _append_entity_tag_columns_if_necessary(user, constraints, breakdown, requested_columns):
        if constraints.get("include_entity_tags") is True and user.has_perm("zemauth.can_include_tags_in_reports"):
            if stats.constants.DimensionIdentifierMapping[stats.constants.DimensionIdentifier.ACCOUNT] in breakdown:
                requested_columns.append("Agency Tags")
                requested_columns.append("Account Tags")
            if stats.constants.DimensionIdentifierMapping[stats.constants.DimensionIdentifier.CAMPAIGN] in breakdown:
                requested_columns.append("Campaign Tags")
            if stats.constants.DimensionIdentifierMapping[stats.constants.DimensionIdentifier.AD_GROUP] in breakdown:
                requested_columns.append("Ad Group Tags")
            if stats.constants.DimensionIdentifierMapping[stats.constants.DimensionIdentifier.SOURCE] in breakdown:
                requested_columns.append("Source Tags")

    @classmethod
    def convert_to_csv(
        cls,
        job,
        data,
        column_names,
        field_name_mapping,
        output,
        csv_separator,
        header=True,
        currency=None,
        account_currency_map=None,
    ):
        csv_column_names = column_names
        original_to_dated = {k: k for k in column_names}
        if helpers.get_option(job, "show_status_date"):
            csv_column_names, original_to_dated = cls._date_column_names(csv_column_names)

        rows = cls._get_csv_rows(
            data,
            field_name_mapping,
            column_names,
            original_to_dated,
            currency=currency,
            account_currency_map=account_currency_map,
        )
        output.write(csv_utils.dictlist_to_csv(csv_column_names, rows, writeheader=header, delimiter=csv_separator))

    @classmethod
    def _get_csv_rows(
        cls, data, field_name_mapping, requested_columns, original_to_dated, currency=None, account_currency_map=None
    ):
        for row in data:
            csv_row = {}
            for column_name in requested_columns:
                field_name = field_name_mapping[column_name]
                csv_column = original_to_dated[column_name]
                if field_name in row:
                    csv_row[csv_column] = row[field_name]
                else:
                    csv_row[csv_column] = ""
            yield csv_row

    @classmethod
    def save_to_s3(cls, csv, human_readable_filename):
        filename = cls._generate_random_filename()
        human_readable_filename = human_readable_filename + ".csv" if human_readable_filename else None
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put(filename, csv, human_readable_filename)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @classmethod
    def send_by_email(cls, job, report_path, **kwargs):
        if len(helpers.get_option(job, "recipients")) <= 0:
            return

        filter_constraints = helpers.get_filter_constraints(job.query["filters"])

        filtered_sources = []
        if filter_constraints.get("sources"):
            filtered_sources = dash.views.helpers.get_filtered_sources(filter_constraints.get("sources", []))

        today = utils.dates_helper.local_today()
        expiry_date = today + datetime.timedelta(days=3)

        view, breakdowns = helpers.extract_view_breakdown(job)
        ad_group_name, campaign_name, account_name = helpers.extract_entity_names(job.user, filter_constraints)

        if job.scheduled_report:
            utils.email_helper.send_async_scheduled_report(
                job.user,
                helpers.get_option(job, "recipients"),
                job.scheduled_report.name,
                dash.constants.ScheduledReportSendingFrequency.get_text(job.scheduled_report.sending_frequency),
                report_path,
                expiry_date,
                filter_constraints["start_date"],
                filter_constraints["end_date"],
                filtered_sources,
                helpers.get_option(job, "show_archived", False),
                helpers.get_option(
                    job, "show_blacklisted_publishers", dash.constants.PublisherBlacklistFilter.SHOW_ALL
                ),
                helpers.get_option(job, "include_totals"),
                view,
                breakdowns,
                helpers.extract_column_names(job.query["fields"]),
                ad_group_name,
                campaign_name,
                account_name,
                **kwargs,
            )
        else:
            utils.email_helper.send_async_report(
                job.user,
                helpers.get_option(job, "recipients"),
                report_path,
                filter_constraints["start_date"],
                filter_constraints["end_date"],
                expiry_date,
                filtered_sources,
                helpers.get_option(job, "show_archived", False),
                helpers.get_option(
                    job, "show_blacklisted_publishers", dash.constants.PublisherBlacklistFilter.SHOW_ALL
                ),
                view,
                breakdowns,
                helpers.extract_column_names(job.query["fields"]),
                helpers.get_option(job, "include_totals"),
                ad_group_name,
                campaign_name,
                account_name,
                **kwargs,
            )

    @staticmethod
    def _extract_structure_constraints(constraints):
        structure_constraints = {}
        for field in constants.STRUCTURE_CONSTRAINTS_FIELDS:
            if field in constraints:
                structure_constraints[field + "s"] = [constraints[field]]
            elif field + "_list" in constraints:
                structure_constraints[field + "s"] = constraints[field + "_list"]
        return structure_constraints

    @staticmethod
    def _generate_random_filename():
        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64)) + ".csv"

    @staticmethod
    def _date_column_names(names):
        dated_columns = []
        original_to_dated_columns = {}
        for name in names:
            dated_name = name
            if utils.columns.get_field_name(name, raise_exception=False) in constants.DATED_COLUMNS:
                dated_name = utils.columns.add_date_to_name(name)
            dated_columns.append(dated_name)
            original_to_dated_columns[name] = dated_name
        return dated_columns, original_to_dated_columns

    @staticmethod
    def _get_order(job, column_to_field_map):
        order = helpers.get_option(job, "order")
        if not order:
            return constants.DEFAULT_ORDER

        prefix, column_name = utils.sort_helper.dissect_order(order)
        if column_name not in column_to_field_map:
            return constants.DEFAULT_ORDER

        return prefix + column_to_field_map[column_name]

    @staticmethod
    def save_to_ftp(server, port, ftp_user, ftp_password, destination, filename, report):
        with ftplib.FTP() as ftp:
            ftp.connect(server, port)
            ftp.login(ftp_user, ftp_password)
            ftp.cwd(destination)
            to_file = io.BytesIO(report.encode("utf-8"))
            ftp.storbinary("STOR {}".format(filename), to_file)
