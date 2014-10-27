import logging
import threading

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db import transaction

from auth import MailGunRequestAuth, GASourceAuth
from parse import CsvReport
from aggregate import ReportEmail, store_to_s3
from utils.statsd_helper import statsd_incr
from convapi import exc


logger = logging.getLogger(__name__)


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

    if int(request.POST.get('attachment-count', 0)) != 1:
        logger.warning('ERROR: single attachment expected, several received')
        return HttpResponse(status=406)

    attachment = request.FILES['attachment-1']
    if attachment.content_type != 'text/csv':
        logger.warning('ERROR: content type is not CSV')
        return HttpResponse(status=406)

    filename = request.FILES['attachment-1'].name
    content = attachment.read()

    try:
        csvreport = CsvReport(content)
    except exc.CsvParseException as e:
        logger.warning(e.message)
        return HttpResponse(status=406)

    store_to_s3(csvreport.get_date(), filename, content)

    if not csvreport.is_ad_group_specified():
        logger.warning('ERROR: not all landing page urls have an ad_group specified')

    if not csvreport.is_media_source_specified():
        logger.warning('ERROR: not all landing page urls have a media source specified')

    TriggerReportAggregateThread(
        csvreport=csvreport,
        sender=request.POST['sender'],
        recipient=recipient,
        subject=request.POST['subject'],
        date=request.POST['Date'],
        text=None
    ).start()

    return HttpResponse(status=200)


class TriggerReportAggregateThread(threading.Thread):

    def __init__(self, csvreport, sender, recipient, subject, date, text):
        super(TriggerReportAggregateThread, self).__init__()
        self.csvreport = csvreport
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.date = date
        self.text = text

    def run(self):
        for ad_group_report in self.csvreport.split_by_ad_group():
            report_email = ReportEmail(
                sender=self.sender,
                recipient=self.recipient,
                subject=self.subject,
                date=self.date,
                text=self.text,
                report=ad_group_report
            )

            report_email.save_raw()
            report_email.aggregate()
        statsd_incr('convapi.aggregated_emails')
