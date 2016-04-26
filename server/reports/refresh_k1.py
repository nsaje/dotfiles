import logging

from reports import daily_statements_k1

logger = logging.getLogger(__name__)


def refresh_k1_reports(update_since):
    daily_statements_k1.reprocess_daily_statements(update_since.date())
