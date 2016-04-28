import logging
import os.path
import io
import csv

from django.conf import settings

from utils import s3helpers

from reports import daily_statements_k1
from reports import materialize_k1

logger = logging.getLogger(__name__)


MATERIALIZED_VIEWS = [
    materialize_k1.ContentAdStats(),
]

MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = 'view.csv'


def refresh_k1_reports(update_since):
    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())
    generate_views(effective_spend_factors)


def generate_views(effective_spend_factors):
    for date, campaigns in effective_spend_factors.iteritems():
        for mv in MATERIALIZED_VIEWS:
            _generate_table(date, mv, effective_spend_factors[date])


def _generate_table(date, materialized_view, campaign_factors):
    logger.info("Materializing table %s for date %s", materialized_view.table_name(), date)

    s3path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        materialized_view.table_name(),
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME,
    )

    bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

    with io.BytesIO() as csvfile:
        writer = csv.writer(csvfile, dialect='excel')

        for line in materialized_view.generate_rows(date, campaign_factors):
            writer.writerow(line)

        bucket.put(s3path, csvfile.getvalue())

    # TODO load to redshift
