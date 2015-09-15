#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import datetime
import logging
import reports
import StringIO
import unicodecsv
import re
import xlrd

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

from reports import update

from utils.compression import unzip
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
        report_log.state = constants.ReportState.SUCCESS
        report_log.save()
    except BaseException as e:
        logger.exception('Base exception occured')
        raise
    except Exception as e:
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.FAILED
        report_log.save()


@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_ga_report(ga_report_task):
    try:
        report_log = models.GAReportLog()
        report_log.email_subject = ga_report_task.subject
        report_log.from_address = ga_report_task.from_address
        report_log.state = constants.ReportState.RECEIVED

        if int(ga_report_task.attachment_count) != 1:
            logger.warning('ERROR: single attachment expected')
            report_log.add_error('ERROR: single attachment expected')
            report_log.state = constants.ReportState.FAILED
            report_log.save()

        content = get_from_s3(ga_report_task.attachment_s3_key)
        if content is None:
            logger.warning('ERROR: Get attachment from s3 failed')
            report_log.add_error('ERROR: Get attachment from s3 failed')
            report_log.state = constants.ReportState.FAILED
            report_log.save()

        if ga_report_task.attachment_name.endswith('.xls'):
            content = _convert_ga_omniture(content, ga_report_task.attachment_name)

        if ga_report_task.attachment_content_type != 'text/csv':
            # assume content is omniture and convert it to GA report
            logger.warning('ERROR: content type is not CSV')
            report_log.add_error('ERROR: content type is not CSV')
            report_log.state = constants.ReportState.FAILED
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
            report_log.state = constants.ReportState.FAILED
            report_log.save()

        if len(csvreport.get_entries()) == 0:
            logger.warning('Report is empty (has no entries)')
            statsd_incr('convapi.aggregated_emails')
            report_log.add_error('Report is empty (has no entries)')
            report_log.state = constants.ReportState.EMPTY_REPORT
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
        report_log.state = constants.ReportState.EMPTY_REPORT
        report_log.save()
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.FAILED
        report_log.save()


def _report_atoi(raw_str):
    # TODO: Implement locale specific parsing
    ret_str = raw_str.replace(',', '')
    dot_loc = ret_str.find('.')
    return int(ret_str[:dot_loc])


def _report_atof(raw_str):
    # TODO: Implement locale specific parsing
    ret_str = raw_str.replace(',', '')
    return float(ret_str)


# TODO: Remove after we switch to new parser w Redshift
# temporary conversion from Omniture to GA report type
def _convert_ga_omniture(content, attachment_name):
    csv_file = StringIO.StringIO()
    writer = unicodecsv.writer(csv_file, encoding='utf-8')

    workbook = xlrd.open_workbook(file_contents=content) #, encoding_override="utf-8")

    header = _parse_omniture_header(workbook)
    date_raw = header.get('Date', '')
    start_date = _extract_omniture_date(date_raw)
    ga_date = start_date.strftime("%Y%m%d")

    # write the header manually as it is different than keys in the dict
    writer.writerows([
        ("# ----------------------------------------",),
        ("# Automatic Omni to GA Conversion - {}".format(attachment_name),),
        ("# Keywords",),
        ("# {dt}-{dt}".format(dt=ga_date),),
        ("# ----------------------------------------",),
        tuple(),
    ])

    # write header
    writer.writerow((
        "Keyword", "Sessions", "% New Sessions", "New Users",
        "Bounce Rate", "Pages / Session",
        "Avg. Session Duration", "Pageviews",)
    )
    body_found = False

    all_columns = []
    sheet = workbook.sheet_by_index(0)
    for row_idx in range(0, sheet.nrows):
        line = []
        for col_idx in range(0, sheet.ncols):
            raw_val = sheet.cell_value(row_idx, col_idx)
            value = (unicode(raw_val).encode('utf-8') or '').strip()
            line.append(value)

        if not body_found:
            if not 'tracking code' in ' '.join(line).lower():
                continue
            else:
                body_found = True
                all_columns = line
                continue

        # valid data is data with known column name(many columns are empty
        # in sample omniture reports)
        keys = [idxel[1] for idxel in enumerate(all_columns) if idxel[1] != '']
        values = [line[idxel[0]] for idxel in enumerate(all_columns) if idxel[1] != '']
        omniture_row_dict = dict(zip(keys, values))

        if 'Total' in line:  # footer with summary
            sessions = _report_atoi(omniture_row_dict['Visits'])
            # write GA footer
            writer.writerows([
                ('', sessions),
                tuple(),
                ('Day Index', 'Sessions',),
                (start_date.strftime("%d/%m/%y"), sessions,),
                ('', sessions,),
            ])
            break

        report_row = _omniture_dict_to_ga_report_row(omniture_row_dict)
        if report_row is None:
            continue
        writer.writerow(report_row)

    return csv_file.getvalue()


def _omniture_dict_to_ga_report_row(omniture_row_dict):
    # "Keyword", "Sessions", "% New Sessions", "New Users", "Bounce Rate",
    # "Pages / Session", "Avg. Session Duration", "Pageviews",))
    sessions = str(_report_atoi(omniture_row_dict['Visits']))
    new_users = str(_report_atoi(omniture_row_dict['Unique Visitors']))
    percent_new_sessions = "{:.2f}%".format(
        _report_atof(omniture_row_dict['Visits']) / _report_atof(omniture_row_dict['Unique Visitors'])
    )
    bounce_rate = "{:.2f}%".format(_report_atof(omniture_row_dict['Bounces']) / _report_atof(sessions) * 100)
    pages_per_session = "{:.2f}".format(_report_atof(omniture_row_dict['Page Views']) / _report_atof(sessions))

    tts = _report_atoi(omniture_row_dict['Total Seconds Spent'])
    hours = tts/3600
    minutes = (tts - hours * 3600) / 60
    seconds = (tts - hours * 3600) % 60
    avg_session_duration = "{hours:02d}:{minutes:02d}:{seconds:02d}".format(
        hours=hours,
        minutes=minutes,
        seconds=seconds
    )
    pageviews = omniture_row_dict['Page Views']

    keyword = None
    for key in omniture_row_dict:
        if 'tracking code' in key.lower():
            keyword = omniture_row_dict[key]

    # if tracking code contains our keyword param then substitute everything
    # with that keyword param
    pattern = re.compile('.*(z1[0-9]*.*1z).*')
    result = pattern.match(keyword)
    if result:
        keyword = result.group(1)

    if keyword is None:
        return None

    return (
        keyword,
        sessions,
        percent_new_sessions,
        new_users,
        bounce_rate,
        pages_per_session,
        avg_session_duration,
        pageviews,
    )


# TODO: Remove after we switch to new parser w Redshift
def _parse_omniture_header(workbook):
    header = {}
    sheet = workbook.sheet_by_index(0)
    for row_idx in range(0, sheet.nrows):
        line = []
        for col_idx in range(0, sheet.ncols):
            raw_val = sheet.cell_value(row_idx, col_idx)
            value = (unicode(raw_val).encode('utf-8') or '').strip()
            if not value:
                break
            line.append(value)
        if len(line) == 1 and ':' in line[0]:
            keyvalue = [(kv or '').strip() for kv in line[0].split(':')]
            header[keyvalue[0]] = ''.join(keyvalue[1:])

    return header


# TODO: Remove after we switch to new parser w Redshift
def _extract_omniture_date(date_raw):
    # Example date: Fri. 4 Sep. 2015
    date_raw_split = date_raw.replace('.', '').split(' ')
    date_raw_split = [date_part.strip() for date_part in date_raw_split if date_part.strip() != '']
    date_prefix = ' '.join(date_raw_split[:4])
    return datetime.datetime.strptime(date_prefix, '%a %d %b %Y')


@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_ga_report_v2(ga_report_task):
    process_report_v2(ga_report_task, reports.constants.ReportType.GOOGLE_ANALYTICS)

@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_omniture_report_v2(ga_report_task):
    process_report_v2(ga_report_task, reports.constants.ReportType.OMNITURE)

def process_report_v2(report_task, report_type):
    try:
        report_log = models.ReportLog()
        # create report log and validate incoming task
        content = _update_and_validate_report_log_v2(report_task, report_log)

        # omniture parsing for now
        report = None

        attachment_name = report_task.attachment_name
        if attachment_name.endswith('.zip'):
            files = unzip(content)
            for filename in files:
                if filename.endswith('.xls') or filename.endswith('.csv'):
                    attachment_name = filename
                    content = files[filename]
                    break

        if report_type == reports.constants.ReportType.OMNITURE:
            report = parse_v2.OmnitureReport(content)
            report.parse()
        else:
            report = parse_v2.GAReport(content)
            # parse will throw exceptions in case of errors
            report.parse()

        _update_report_log_after_parsing(report, report_log, report_task)

        # serialize report - this happens even if report is failed/empty
        valid_entries = report.valid_entries()
        update.process_report(
            report.get_date(),
            valid_entries,
            report_type
        )

        report_log.visits_imported = report.imported_visits()
        report_log.visits_reported = report.reported_visits()
        report_log.state = constants.ReportState.SUCCESS
        report_log.save()
    except exc.EmptyReportException as e:
        logger.warning(e.message)
        statsd_incr('convapi_v2.empty_report')
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.EMPTY_REPORT
        report_log.save()
        raise
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.FAILED
        report_log.save()
        raise


@app.task(max_retries=settings.CELERY_TASK_MAX_RETRIES,
          default_retry_delay=settings.CELERY_TASK_RETRY_DEPLAY)
@transaction.atomic
def process_omniture_report(ga_report_task):
    try:
        report_log = models.GAReportLog()
        # create report log and validate incoming task
        content = _update_and_validate_report_log(ga_report_task, report_log)

        report = parse_v2.OmnitureReport(content)
        # parse will throw exceptions in case of errors
        report.parse()

        _update_report_log_after_parsing(report, report_log, ga_report_task)

        # serialize report - this happens even if report is failed/empty
        valid_entries = report.valid_entries()
        update.process_report(report.get_date(), valid_entries, reports.constants.ReportType.OMNITURE)

        report_log.state = constants.ReportState.SUCCESS
        report_log.save()
    except exc.EmptyReportException as e:
        logger.warning(e.message)
        statsd_incr('convapi_v2.empty_report')
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.EMPTY_REPORT
        report_log.save()
        raise
    except Exception as e:
        logger.warning(e.message)
        report_log.add_error(e.message)
        report_log.state = constants.ReportState.FAILED
        report_log.save()
        raise


def _update_and_validate_report_log(ga_report_task, report_log):
    report_log.email_subject = '{subj}_v2'.format(subj=ga_report_task.subject)
    report_log.from_address = ga_report_task.from_address
    report_log.state = constants.ReportState.RECEIVED

    if int(ga_report_task.attachment_count) != 1:
        logger.warning('ERROR: single attachment expected')
        report_log.add_error('ERROR: single attachment expected')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    content = get_from_s3(ga_report_task.attachment_s3_key)
    if content is None:
        logger.warning('ERROR: Get attachment from s3 failed')
        report_log.add_error('ERROR: Get attachment from s3 failed')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    if ga_report_task.attachment_content_type != 'text/csv':
        logger.warning('ERROR: content type is not CSV')
        report_log.add_error('ERROR: content type is not CSV')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    filename = ga_report_task.attachment_name
    report_log.csv_filename = filename
    return content


def _update_and_validate_report_log_v2(ga_report_task, report_log):
    report_log.email_subject = '{subj}_v2'.format(subj=ga_report_task.subject)
    report_log.from_address = ga_report_task.from_address
    report_log.state = constants.ReportState.RECEIVED

    if int(ga_report_task.attachment_count) != 1:
        logger.warning('ERROR: single attachment expected')
        report_log.add_error('ERROR: single attachment expected')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    content = get_from_s3(ga_report_task.attachment_s3_key)
    if content is None:
        logger.warning('ERROR: Get attachment from s3 failed')
        report_log.add_error('ERROR: Get attachment from s3 failed')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    if ga_report_task.attachment_content_type != 'text/csv':
        logger.warning('ERROR: content type is not CSV')
        report_log.add_error('ERROR: content type is not CSV')
        report_log.state = constants.ReportState.FAILED
        report_log.save()

    filename = ga_report_task.attachment_name
    report_log.report_filename = filename
    return content


def _update_report_log_after_parsing(csvreport, report_log, ga_report_task):
    report_log.for_date = csvreport.get_date()
    report_log.state = constants.ReportState.PARSED

    content_ad_errors = content_ad_specified_errors(csvreport)
    media_source_errors = media_source_specified_errors(csvreport)

    message = ''
    if len(content_ad_errors) > 0:
        message += '\nERROR: not all landing page urls have a valid content ad specified:\n'
        for err in content_ad_errors:
            message += err or '' + '\n'

    if len(media_source_errors) > 0:
        message += '\nERROR: not all landing page urls have a media source specified: \n'
        for landing_url in media_source_errors:
            message += landing_url or '' + '\n'

    if too_many_errors(content_ad_errors, media_source_errors):
        logger.warning("Too many errors in content_ad_errors and media_source_errors lists.")
        report_log.add_error("Too many errors in urls. Cannot recognize content ad and media sources for some urls:\n %s \n\n %s" % ('\n'.join(content_ad_errors), '\n'.join(media_source_errors)))
        report_log.state = constants.ReportState.FAILED
        statsd_incr('convapi_v2.too_many_errors')
        report_log.save()

    if csvreport.is_empty():
        logger.warning('Report is empty (has no entries)')
        report_log.add_error('Report is empty (has no entries)')
        report_log.state = constants.ReportState.EMPTY_REPORT
        statsd_incr('convapi_v2.empty_report')
        report_log.save()

    report_log.sender = ga_report_task.sender
    report_log.email_subject = ga_report_task.subject
    report_log.for_date = csvreport.get_date()
    report_log.save()

