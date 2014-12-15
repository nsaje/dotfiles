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
from convapi import models
from convapi import constants


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

    try:
        report_log = models.GAReportLog()
        report_log.email_subject = request.POST['subject']

        if int(request.POST.get('attachment-count', 0)) != 1:
            logger.warning('ERROR: single attachment expected, several received')
            report_log.add_error('ERROR: single attachment expected, several received')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()
            return HttpResponse(status=406)

        attachment = request.FILES['attachment-1']
        if attachment.content_type != 'text/csv':
            logger.warning('ERROR: content type is not CSV')
            report_log.add_error('ERROR: content type is not CSV')
            report_log.state = constants.GAReportState.FAILED
            report_log.save()
            return HttpResponse(status=406)

        filename = request.FILES['attachment-1'].name

        report_log.csv_filename = filename

        content = attachment.read()

        csvreport = CsvReport(content, report_log)

        if not csvreport.is_ad_group_specified():
            message = 'ERROR: not all landing page urls have a valid ad_group specified'
            logger.warning(message)
            report_log.add_error(message)
            report_log.state = constants.GAReportState.FAILED
            report_log.save()
            return HttpResponse(status=406)

        if not csvreport.is_media_source_specified():
            message = 'ERROR: not all landing page urls have a media source specified'
            logger.warning(message)
            report_log.add_error(message)
            report_log.state = constants.GAReportState.FAILED
            report_log.save()
            return HttpResponse(status=406)

        store_to_s3(csvreport.get_date(), filename, content)

        if len(csvreport.get_entries()) == 0:
            logger.warning('Report is empty (has no entries)')
            statsd_incr('convapi.aggregated_emails')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.GAReportState.EMPTY_REPORT
            report_log.save()
            return HttpResponse(status=200)

        TriggerReportAggregateThread(
            csvreport=csvreport,
            sender=request.POST['sender'],
            recipient=recipient,
            subject=request.POST['subject'],
            date=request.POST['Date'],
            text=None,
            report_log=report_log
        ).start()
    except exc.EmptyReportException as e:
        logger.warning(e.message)
        statsd_incr('convapi.aggregated_emails')
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.EMPTY_REPORT
        report_log.save()
        return HttpResponse(status=200)
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.GAReportState.FAILED
        report_log.save()
        return HttpResponse(status=406)

    return HttpResponse(status=200)


class TriggerReportAggregateThread(threading.Thread):

    def __init__(self, csvreport, sender, recipient, subject, date, text, report_log):
        super(TriggerReportAggregateThread, self).__init__()
        self.csvreport = csvreport
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.date = date
        self.text = text
        self.report_log = report_log

    def run(self):
        try:
            for ad_group_report in self.csvreport.split_by_ad_group():
                self.report_log.add_ad_group_id(ad_group_report.get_ad_group_id())

                report_email = ReportEmail(
                    sender=self.sender,
                    recipient=self.recipient,
                    subject=self.subject,
                    date=self.date,
                    text=self.text,
                    report=ad_group_report,
                    report_log=self.report_log
                )

                report_email.save_raw()

                report_email.aggregate()
            statsd_incr('convapi.aggregated_emails')
            self.report_log.state = constants.GAReportState.SUCCESS
            self.report_log.save()
        except Exception as e:
            self.report_log.add_error(e.message)
            self.report_log.state = constants.GAReportState.FAILED
            self.report_log.save()
