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
from convapi import helpers

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
    from pudb import set_trace; set_trace()


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


def reprocess_report_logs(report_logs):

    for rl in report_logs:
        helpers.check_report_log_for_reprocess(rl)

    received_date = datetime.datetime.today()
    sender = "Reprocess report logs script"

    # if all checks completed successfully attempt reprocess
    for rl in report_logs:
        _reprocess_report_log(rl, sender=sender, received_date=received_date)


def _reprocess_report_log(report_log, sender, received_date):
    """
    Reprocess existing report log. Creates a new report log as a result. Uses existing
    s3 object keys of stored report files.

    report_log  - can be either GAReportLog or ReportLog instance.
    is_omniture - denotes whether this is an Omniture or GA report.
                  It can not be determined automatically.
    """

    logger.info('Reprocessing report log %s', report_log.pk)

    helpers.check_report_log_for_reprocess(report_log)

    content_type = _extract_content_type(report_log.s3_key)
    attachment_name = report_log.get_report_filename()

    report_task = GAReportTask.from_report_log(
        report_log, received_date, sender, attachment_name, content_type)

    process_report_task(report_task)


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

    s3_key = None
    attachment_name = ''
    report_task = None
    try:

        csvreport_date_raw = email.utils.parsedate(request.POST.get('Date'))
        csvreport_date = datetime.datetime.fromtimestamp(time.mktime(csvreport_date_raw))

        attachment_name, content = _first_valid_report_attachment(request.FILES)
        content_type = _extract_content_type(attachment_name)

        logger.info("Storing to S3 {date}-{att_name}-{cl}".format(
            date=csvreport_date_raw or '',
            att_name=attachment_name or '',
            cl=len(content) if content else 0
        ))
        s3_key = store_to_s3(csvreport_date, attachment_name, content)

        report_task = GAReportTask.from_request(request, s3_key, attachment_name, content_type)
    except Exception:
        post_params = request.POST.dict()

        # strip away secrets
        del post_params['signature']
        del post_params['token']

        msg = "Unable to fetch parameters needed to create parsing task, POST {}".format(post_params)

        failed_report_log = models.ReportLog(
            state=constants.ReportState.FAILED,
            errors=msg
        )
        failed_report_log.save()
        logger.exception(msg)

    if report_task:
        process_report_task(report_task)

    return HttpResponse(status=200)


def process_report_task(report_task):
    try:
        tasks.process_ga_report.apply_async(
            (report_task, ),
            queue=settings.CELERY_DEFAULT_CONVAPI_QUEUE
        )
    except Exception as e:
        report_task.create_failed_report_log(models.GAReportLog, e)
        logger.exception(e.message)

    try:
        if report_task.is_omniture_report():
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
        report_task.create_failed_report_log(models.ReportLog, e)
        logger.exception(e.message)


class GAReportTask:
    """
    Holds data needed to parse a GA or Omniture report. It is assumend to be
    read only after initialization.
    """

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

    def is_omniture_report(self):
        return OMNITURE_REPORT_MAIL in self.recipient

    def create_failed_report_log(self, report_log_class, ex):
        report_log = report_log_class(state=constants.ReportState.FAILED)

        report_log.datetime = self.date
        report_log.email_subject = self.subject
        report_log.from_address = self.from_address
        report_log.recipient = self.recipient
        report_log.s3_key = self.attachment_s3_key

        if hasattr(report_log, 'csv_filename'):
            report_log.csv_filename = self.attachment_name
        else:
            report_log.report_filename = self.attachment_name

        report_log.add_error(ex.message)
        report_log.save()

    @classmethod
    def from_report_log(cls, report_log, received_date, sender, attachment_name, content_type):
        report_task = GAReportTask(
            subject=report_log.email_subject,
            date=received_date,
            sender=sender,
            recipient=report_log.recipient,
            from_address=report_log.from_address,
            text=None,
            attachment_s3_key=report_log.s3_key,
            attachment_name=attachment_name,
            attachments_count=1,
            attachment_content_type=content_type
        )
        return report_task

    @classmethod
    def from_request(cls, request, s3_key, attachment_name, content_type):
        report_task = GAReportTask(
            request.POST.get('subject'),
            request.POST.get('Date'),
            request.POST.get('sender'),
            request.POST.get('recipient'),
            request.POST.get('from'),
            None,
            s3_key,
            attachment_name,
            request.POST.get('attachment-count', 0),
            content_type
        )
        return report_task
