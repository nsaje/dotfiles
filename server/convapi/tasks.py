from __future__ import absolute_import
import logging
import reports

from django.conf import settings
from django.db import transaction

from server.celery import app
from convapi import exc
from convapi import models
from convapi import constants
from convapi.parse import CsvReport
from convapi import parse_v2
from convapi.aggregate import ReportEmail
from convapi.helpers import get_from_s3

from reports import api_contentads

from utils.statsd_helper import statsd_incr, statsd_timer

logger = logging.getLogger(__name__)


def too_many_errors(*errors):
    errors_count = 0
    for error_list in errors:
        errors_count += len(error_list)
    return errors_count > constants.ALLOWED_ERRORS_COUNT

def ad_group_specified_errors(csvreport):
    errors = []
    is_ad_group_specified, ad_group_not_specified = csvreport.is_ad_group_specified()
    if not is_ad_group_specified:
        errors.extend(ad_group_not_specified)
    return errors

def content_ad_specified_errors(csvreport):
    errors = []
    is_content_ad_specified, content_ad_not_specified = csvreport.is_content_ad_specified()
    if not is_content_ad_specified:
        errors.extend(content_ad_not_specified)
    return errors

def media_source_specified_errors(csvreport):
    errors = []
    is_media_source_specified, media_source_not_specified = csvreport.is_media_source_specified()
    if not is_media_source_specified:
        errors.extend(media_source_not_specified)
    return errors

@statsd_timer('convapi', 'report_aggregate')
def report_aggregate(csvreport, sender, recipient, subject, date, text, report_log):
    try:
        for ad_group_report in csvreport.split_by_ad_group():
            report_log.add_ad_group_id(ad_group_report.get_ad_group_id())

            report_email = ReportEmail(
                sender=sender,
                recipient=recipient,
                subject=subject,
                date=date,
                text=text,
                report=ad_group_report,
                report_log=report_log
            )
            report_email.save_raw()
            report_email.aggregate()

        statsd_incr('convapi.aggregated_emails')
        report_log.state = constants.GAReportState.SUCCESS
        report_log.save()
    except BaseException as e:
        logger.exception('Base exception occured')
        raise
    except Exception as e:
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.FAILED
        report_log.save()

@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_ga_report(ga_report_task):
    try:
        report_log = models.GAReportLog()
        report_log.email_subject = ga_report_task.subject
        report_log.from_address = ga_report_task.from_address
        report_log.state = constants.GAReportState.RECEIVED

        if int(ga_report_task.attachment_count) != 1:
            logger.warning('ERROR: single attachment expected')
            report_log.add_error('ERROR: single attachment expected')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        content = get_from_s3(ga_report_task.attachment_s3_key)
        if content is None:
            logger.warning('ERROR: Get attachment from s3 failed')
            report_log.add_error('ERROR: Get attachment from s3 failed')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        if ga_report_task.attachment_content_type != 'text/csv':
            logger.warning('ERROR: content type is not CSV')
            report_log.add_error('ERROR: content type is not CSV')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        filename = ga_report_task.attachment_name
        report_log.csv_filename = filename

        csvreport = CsvReport(content, report_log)

        ad_group_errors = ad_group_specified_errors(csvreport)
        media_source_errors = media_source_specified_errors(csvreport)

        message = ''
        if len(ad_group_errors) > 0:
            message += '\nERROR: not all landing page urls have a valid ad_group specified:\n'
            for landing_url in ad_group_errors:
                message += landing_url + '\n'

        if len(media_source_errors) > 0:
            message += '\nERROR: not all landing page urls have a media source specified: \n'
            for landing_url in media_source_errors:
                message += landing_url + '\n'

        if too_many_errors(ad_group_errors, media_source_errors):
            logger.warning("Too many errors in ad_group_errors and media_source_errors lists.")
            report_log.add_error("Too many errors in urls. Cannot recognize adgroup and media sources for some urls:\n %s \n\n %s" % ('\n'.join(ad_group_errors), '\n'.join(media_source_errors)))
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        if len(csvreport.get_entries()) == 0:
            logger.warning('Report is empty (has no entries)')
            statsd_incr('convapi.aggregated_emails')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.GAReportState.EMPTY_REPORT
            report_log.save()

        report_log.sender = ga_report_task.sender
        report_log.email_subject = ga_report_task.subject
        report_log.for_date = csvreport.get_date()
        report_log.save()

        report_aggregate(
            csvreport=csvreport,
            sender=ga_report_task.sender,
            recipient=ga_report_task.recipient,
            subject=ga_report_task.subject,
            date=ga_report_task.date,
            text=None,
            report_log=report_log
        )
    except exc.EmptyReportException as e:
        logger.warning(e.message)
        statsd_incr('convapi.aggregated_emails')
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.EMPTY_REPORT
        report_log.save()
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.FAILED
        report_log.save()


@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_ga_report_v2(ga_report_task):
    try:
        report_log = models.GAReportLog()
        report_log.email_subject = ga_report_task.subject
        report_log.from_address = ga_report_task.from_address
        report_log.state = constants.GAReportState.RECEIVED

        if int(ga_report_task.attachment_count) != 1:
            logger.warning('ERROR: single attachment expected')
            report_log.add_error('ERROR: single attachment expected')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        content = get_from_s3(ga_report_task.attachment_s3_key)
        if content is None:
            logger.warning('ERROR: Get attachment from s3 failed')
            report_log.add_error('ERROR: Get attachment from s3 failed')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        if ga_report_task.attachment_content_type != 'text/csv':
            logger.warning('ERROR: content type is not CSV')
            report_log.add_error('ERROR: content type is not CSV')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        filename = ga_report_task.attachment_name
        report_log.csv_filename = filename

        csvreport = parse_v2.CsvReport(content)
        # parse will throw exceptions in case of errors
        csvreport.parse()
        report_log.for_date = csvreport.get_date()
        report_log.state = constants.GAReportState.PARSED

        content_ad_errors = content_ad_specified_errors(csvreport)
        media_source_errors = media_source_specified_errors(csvreport)

        message = ''
        if len(content_ad_errors) > 0:
            message += '\nERROR: not all landing page urls have a valid content ad specified:\n'
            for err in content_ad_errors:
                message += err + '\n'

        if len(media_source_errors) > 0:
            message += '\nERROR: not all landing page urls have a media source specified: \n'
            for landing_url in media_source_errors:
                message += landing_url + '\n'

        if too_many_errors(content_ad_errors, media_source_errors):
            logger.warning("Too many errors in content_ad_errors and media_source_errors lists.")
            report_log.add_error("Too many errors in urls. Cannot recognize content ad and media sources for some urls:\n %s \n\n %s" % ('\n'.join(content_ad_errors), '\n'.join(media_source_errors)))
            report_log.state = constants.GAReportState.FAILED
            statsd_incr('convapi_v2.too_many_errors')
            report_log.save()

        if csvreport.is_empty():
            logger.warning('Report is empty (has no entries)')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.GAReportState.EMPTY_REPORT
            statsd_incr('convapi_v2.empty_report')
            report_log.save()

        report_log.sender = ga_report_task.sender
        report_log.email_subject = ga_report_task.subject
        report_log.for_date = csvreport.get_date()
        report_log.save()

        # serialize report - this happens even if report is failed/empty
        api_contentads.process_report(csvreport.entries, reports.constants.ReportType.GOOGLE_ANALYTICS)

    except exc.EmptyReportException as e:
        logger.warning(e.message)
        statsd_incr('convapi_v2.empty_report')
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.EMPTY_REPORT
        report_log.save()
        raise
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.FAILED
        report_log.save()
        raise
