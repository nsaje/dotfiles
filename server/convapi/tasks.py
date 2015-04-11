from __future__ import absolute_import
import logging

from server.celery import app
from convapi import exc
from convapi import models
from convapi import constants
from convapi.parse import CsvReport
from convapi.aggregate import ReportEmail, store_to_s3
from utils.statsd_helper import statsd_incr

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

def media_source_specified_errors(csvreport):
    errors = []
    is_media_source_specified, media_source_not_specified = csvreport.is_media_source_specified()
    if not is_media_source_specified:
        errors.extend(media_source_not_specified)
    return errors

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

@app.task
def process_ga_report(request):
    try:
        report_log = models.GAReportLog()
        report_log.email_subject = request.POST['subject']
        report_log.from_address = request.POST['from']
        report_log.state = constants.GAReportState.RECEIVED

        if int(request.POST.get('attachment-count', 0)) != 1:
            logger.warning('ERROR: single attachment expected')
            report_log.add_error('ERROR: single attachment expected')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        attachment = request.FILES['attachment-1']
        if attachment.content_type != 'text/csv':
            logger.warning('ERROR: content type is not CSV')
            report_log.add_error('ERROR: content type is not CSV')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()

        filename = request.FILES['attachment-1'].name
        report_log.csv_filename = filename

        content = attachment.read()
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

        csvreport_date = csvreport.get_date()
        store_to_s3(csvreport_date, filename, content)

        if len(csvreport.get_entries()) == 0:
            logger.warning('Report is empty (has no entries)')
            statsd_incr('convapi.aggregated_emails')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.GAReportState.EMPTY_REPORT
            report_log.save()

        report_log.sender = request.POST['sender']
        report_log.email_subject = request.POST['subject']
        report_log.for_date = csvreport_date
        report_log.save()

        report_aggregate(
            csvreport=csvreport,
            sender=request.POST['sender'],
            recipient=request.POST['recipient'],
            subject=request.POST['subject'],
            date=request.POST['Date'],
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
