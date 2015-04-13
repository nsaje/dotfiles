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
        logger.exception(e.message)

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
            return HttpResponse(status=406)

        csvreport_date = csvreport.get_date()
        store_to_s3(csvreport_date, filename, content)

        if len(csvreport.get_entries()) == 0:
            logger.warning('Report is empty (has no entries)')
            statsd_incr('convapi.aggregated_emails')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.GAReportState.EMPTY_REPORT
            report_log.save()
            return HttpResponse(status=200)

        report_log.sender = request.POST['sender']
        report_log.email_subject = request.POST['subject']
        report_log.for_date = csvreport_date
        report_log.save()

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

class TriggerReportAggregateThread(Thread):

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
            logger.info("GA-aggregate - started")
            for ad_group_report in self.csvreport.split_by_ad_group():
                time.sleep(0)  # Makes greenlet yield control to prevent blocking
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
                logger.info("GA-aggregate - before")
                report_email.aggregate()
                logger.info("GA-aggregate - after")

            statsd_incr('convapi.aggregated_emails')
            self.report_log.state = constants.GAReportState.SUCCESS
            self.report_log.save()
            logger.info("GA-aggregate - finished")
        except BaseException as e:
            logger.exception('Base exception occured')
            raise
        except Exception as e:
            self.report_log.add_error(e.message)
            self.report_log.state = constants.GAReportState.FAILED
            self.report_log.save()
