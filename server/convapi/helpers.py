import logging
import os
import hashlib
import utils.s3helpers

S3_REPORT_KEY_FORMAT = 'conversionreports/{date}/{filename}'

logger = logging.getLogger(__name__)


def get_from_s3(key):
    try:
        helper = utils.s3helpers.S3Helper()
        return helper.get(key)
    except Exception:
        logger.exception('Error while saving conversion report to s3')

    return None


def store_to_s3(date, filename, content):
    key = _generate_s3_report_key(date, filename, content)
    try:
        helper = utils.s3helpers.S3Helper()
        return helper.put(key, content)
    except Exception:
        logger.exception('Error while saving conversion report to s3')
    return None


def _generate_s3_report_key(date, filename, content):
    filename = filename.lower().replace(' ', '_')
    basefnm, extension = os.path.splitext(filename)
    digest = hashlib.md5(content).hexdigest() + str(len(content))
    key = S3_REPORT_KEY_FORMAT.format(
        date=date.strftime('%Y%m%d'),
        filename=basefnm + '_' + digest + extension
    )
    return key

