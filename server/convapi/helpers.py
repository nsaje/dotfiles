import logging
import utils.s3helpers

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
