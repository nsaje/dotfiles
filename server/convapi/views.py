import logging
import time
from threading import Thread

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db import transaction
from django.conf import settings

from auth import MailGunRequestAuth, GASourceAuth
from parse import CsvReport
from aggregate import ReportEmail, store_to_s3
from utils.statsd_helper import statsd_incr
from convapi import exc
from convapi import models
from convapi import constants
from convapi import tasks

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


@csrf_exempt
@transaction.atomic
def mailgun_gareps(request):
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
    try:
        ga_report_task = GAReportTask(request.POST.get('subject'),
                                             request.POST.get('Date'),
                                             request.POST.get('sender'),
                                             request.POST.get('recipient'),
                                             request.POST.get('from'),
                                             None,
                                             request.FILES.get('attachment-1'),
                                             request.FILES.get('attachment-1').name,
                                             request.POST.get('attachment-count', 0))

        tasks.process_ga_report.apply_async((ga_report_task, ),
                                             queue=settings.CELERY_DEFAULT_CONVAPI_QUEUE)
    except Exception as e:
        report_log = models.GAReportLog()
        report_log.email_subject = ga_report_task.subject
        report_log.from_address = ga_report_task.from_address
        report_log.csv_filename = request.FILES.get('attachment-1').name
        report_log.state = constants.GAReportState.FAILED
        report_log.save()
        logger.exception(e.message)

    return HttpResponse(status=200)


class GAReportTask():
    def __init__(self, subject, date, sender, recipient, from_address, text,
                 attachment, attachment_name, attachments_count):
        self.subject = subject
        self.date = date
        self.sender = sender
        self.recipient = recipient
        self.from_address = from_address
        self.text = text
        self.attachment = attachment
        self.attachment_name = attachment_name
        self.attachment_count = attachments_count
