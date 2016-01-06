import logging
import utils.s3helpers

from convapi import constants

S3_REPORT_KEY_FORMAT = 'conversionreports/{date}/{filename}'

logger = logging.getLogger(__name__)


def get_from_s3(key):
    try:
        return utils.s3helpers.S3Helper().get(key)
    except Exception:
        logger.exception('Error while getting conversion report to s3')

    return None


def store_to_s3(date, filename, content):
    key = S3_REPORT_KEY_FORMAT.format(
        date=date.strftime('%Y%m%d'),
        filename=utils.s3helpers.generate_safe_filename(filename, content)
    )

    try:
        utils.s3helpers.S3Helper().put(key, content)
        return key
    except Exception:
        logger.exception('Error while saving conversion report to s3')
    return None


def check_report_log_for_reprocess(report_log):
    if report_log.state != constants.ReportState.FAILED:
        raise Exception("Only failed report logs can be reprocessed, id={}".format(
            report_log.id))

    mandatory_attrs = ('email_subject', 'recipient', 'from_address', 's3_key')

    missing_values = [x for x in mandatory_attrs if not getattr(report_log, x)]

    if not report_log.get_report_filename():
        missing_values.append('report_filename')

    if missing_values:
        raise Exception("Can't reprocess - missing values. Report log id={}, missing values={}".format(
            report_log.id, missing_values))
