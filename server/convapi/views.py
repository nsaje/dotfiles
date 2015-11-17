import datetime
import logging
import time
import email.utils

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

import newrelic.agent

from auth import MailGunRequestAuth, GASourceAuth
from helpers import store_to_s3
from utils.statsd_helper import statsd_incr
from convapi import models
from convapi import constants
from convapi import tasks

logger = logging.getLogger(__name__)

OMNITURE_REPORT_MAIL = 'omniture-reports@mailapi.zemanta.com'


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


def _first_valid_report_attachment(files):
    valid_suffixes = ['.csv', '.xls', '*.zip']
    for key in files:
        attachment = files[key].name
        if attachment is None or attachment == '':
            continue
        if any(attachment.endswith(valid_suffix) for valid_suffix in valid_suffixes):
            content = files.get(key).read()
            return attachment, content

    return None, None


def _extract_content_type(name):
    if not name:
        return 'text/plain'

    if name.endswith('.csv'):
        return 'text/csv'
    elif name.endswith('.zip'):
        return 'application/zip'
    elif name.endswith('.xls'):
        return 'application/vnd.ms-excel'

    return 'text/plain'


@csrf_exempt
def mailgun_gareps(request):
    newrelic.agent.set_background_task(flag=True)
    if request.method != 'POST':
        logger.warning('ERROR: only POST is supported')
        return HttpResponse(status=406)
    if not MailGunRequestAuth(request).is_authorised():
        logger.warning('ERROR: authenticity of request could not be verified')
        statsd_incr('convapi.invalid_request_signature')
        return HttpResponse(status=406)

    recipient = request.POST['recipient']

    if not GASourceAuth(recipient).is_authorised():
        logger.warning('ERROR: sender is not authorised')
        statsd_incr('convapi.invalid_email_sender')
        return HttpResponse(status=406)


    statsd_incr('convapi.accepted_emails')
    key = None

    attachment_name = ''
    ga_report_task = None
    try:

        csvreport_date_raw = email.utils.parsedate(request.POST.get('Date'))
        csvreport_date = datetime.datetime.fromtimestamp(time.mktime(csvreport_date_raw))

        attachment_name, content = _first_valid_report_attachment(request.FILES)
        content_type = _extract_content_type(attachment_name)

        key = store_to_s3(csvreport_date, attachment_name, content)
        logger.info("Storing to S3 {date}-{att_name}-{cl}".format(
               date=csvreport_date_raw or '',
               att_name=attachment_name or '',
               cl=len(content) if content else 0
           ))

        ga_report_task = GAReportTask(
            request.POST.get('subject'),
            request.POST.get('Date'),
            request.POST.get('sender'),
            request.POST.get('recipient'),
            request.POST.get('from'),
            None,
            key,
            attachment_name,
            request.POST.get('attachment-count', 0),
            content_type
        )

        tasks.process_ga_report.apply_async(
            (ga_report_task, ),
            queue=settings.CELERY_DEFAULT_CONVAPI_QUEUE
        )

    except Exception as e:
        report_log = models.GAReportLog()
        report_log.email_subject = ga_report_task.subject if ga_report_task is not None else None
        report_log.from_address = ga_report_task.from_address if ga_report_task is not None else None
        report_log.csv_filename = request.FILES.get('attachment-1').name if request.FILES.get('attachment-1') is not None else None
        report_log.state = constants.ReportState.FAILED
        report_log.save()
        logger.exception(e.message)

    report_task = None
    try:
        content_type = _extract_content_type(attachment_name)
        report_task = GAReportTask(
            request.POST.get('subject'),
            request.POST.get('Date'),
            request.POST.get('sender'),
            request.POST.get('recipient'),
            request.POST.get('from'),
            None,
            key,
            attachment_name,
            request.POST.get('attachment-count', 0),
            content_type)

        if OMNITURE_REPORT_MAIL in request.POST.get('recipient'):
            tasks.process_omniture_report_v2.apply_async(
                (report_task, ),
                queue=settings.CELERY_DEFAULT_CONVAPI_V2_QUEUE
            )
        else:
            tasks.process_ga_report_v2.apply_async(
                (report_task, ),
                queue=settings.CELERY_DEFAULT_CONVAPI_V2_QUEUE
            )
    except Exception as e:
        report_log = models.ReportLog()
        report_log.email_subject = report_task.subject if report_task is not None else None
        report_log.from_address = report_task.from_address if report_task is not None else None
        report_log.report_filename = request.FILES.get('attachment-1').name if request.FILES.get('attachment-1') is not None else None
        report_log.state = constants.ReportState.FAILED
        report_log.save()
        logger.exception(e.message)

    return HttpResponse(status=200)


class GAReportTask:
    def __init__(self, subject, date, sender, recipient, from_address, text,
                 attachment_s3_key, attachment_name, attachments_count, attachment_content_type):
        self.subject = subject
        self.date = date
        self.sender = sender
        self.recipient = recipient
        self.from_address = from_address
        self.text = text
        self.attachment_content_type = attachment_content_type
        self.attachment = attachment_s3_key
        self.attachment_s3_key = attachment_s3_key
        self.attachment_name = attachment_name
        self.attachment_count = attachments_count
