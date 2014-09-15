import exc
import json
import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from auth import MailGunRequestAuth, GASourceAuth
from parse import CsvReport
from models import ReportEmail


logger = logging.getLogger(__name__)


@csrf_exempt
def mailgun_gareps(request):
    if request.method != 'POST':
        logger.error('ERROR: only POST is supported')
        return HttpResponse(status=406)
    if not MailGunRequestAuth(request).is_authorised():
        logger.error('ERROR: authenticity of request could not be verified')
        return HttpResponse(status=406)

    recipient = request.POST['recipient']
    
    if not GASourceAuth(recipient).is_authorised():
        logger.error('ERROR: sender is not authorised')
        return HttpResponse(status=406)

    if int(request.POST.get('attachment-count', 0)) != 1:
        logger.error('ERROR: single attachment expected, several received')
        return HttpResponse(status=406)

    attachment = request.FILES['attachment-1']
    if attachment.content_type != 'text/csv':
        logger.error('ERROR: content type is not CSV')
        return HttpResponse(status=406)

    csvreport = CsvReport(attachment.read())

    report_email = ReportEmail(
        sender=request.POST['sender'],
        recipient=recipient,
        subject=request.POST['subject'],
        date=request.POST['Date'],
        text=None,
        report=csvreport
    )

    if not report_email.is_ad_group_consistent():
        logger.error('ERROR: ad group not consistent')
        return HttpResponse(status=406)

    if not report_email.is_media_source_specified():
        logger.error('ERROR: not all landing page urls have a media source specified')
        return HttpResponse(status=406)

    report_email.save_raw()
    report_email.aggregate()
    
    return HttpResponse(status=200)
