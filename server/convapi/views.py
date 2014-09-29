import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db import transaction

from auth import MailGunRequestAuth, GASourceAuth
from parse import CsvReport
from aggregate import ReportEmail, store_to_s3
from utils.statsd_helper import statsd_incr


logger = logging.getLogger(__name__)


@csrf_exempt
@transaction.atomic
def mailgun_gareps(request):
    if request.method != 'POST':
        logger.error('ERROR: only POST is supported')
        return HttpResponse(status=406)
    if not MailGunRequestAuth(request).is_authorised():
        logger.error('ERROR: authenticity of request could not be verified')
        statsd_incr('convapi.invalid_request_signature')
        return HttpResponse(status=406)

    recipient = request.POST['recipient']

    if not GASourceAuth(recipient).is_authorised():
        logger.error('ERROR: sender is not authorised')
        statsd_incr('convapi.invalid_email_sender')
        return HttpResponse(status=406)

    statsd_incr('convapi.accepted_emails')

    if int(request.POST.get('attachment-count', 0)) != 1:
        logger.error('ERROR: single attachment expected, several received')
        return HttpResponse(status=406)

    attachment = request.FILES['attachment-1']
    if attachment.content_type != 'text/csv':
        logger.error('ERROR: content type is not CSV')
        return HttpResponse(status=406)

    filename = request.FILES['attachment-1'].name
    content = attachment.read()

    csvreport = CsvReport(content)

    store_to_s3(csvreport.get_date(), filename, content)

    if not csvreport.is_ad_group_specified():
        logger.error('ERROR: not all landing page urls have an ad_group specified')
        #return HttpResponse(status=406)

    if not csvreport.is_media_source_specified():
        logger.error('ERROR: not all landing page urls have a media source specified')
        #return HttpResponse(status=406)

    for ad_group_report in csvreport.split_by_ad_group():
        report_email = ReportEmail(
            sender=request.POST['sender'],
            recipient=recipient,
            subject=request.POST['subject'],
            date=request.POST['Date'],
            text=None,
            report=ad_group_report
        )

        report_email.save_raw()
        report_email.aggregate()

    statsd_incr('convapi.aggregated_emails')

    return HttpResponse(status=200)
