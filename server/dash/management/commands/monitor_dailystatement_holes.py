import logging
import datetime

from django.db import connection

from etl import daily_statements_k1
from utils.command_helpers import ExceptionCommand
import influx

logger = logging.getLogger(__name__)


DAYS_TO_CHECK = 90


class Command(ExceptionCommand):

    help = "Checks that all budgets have daily statements for all their valid dates"

    def handle(self, *args, **options):
        date_since = datetime.date.today() - datetime.timedelta(days=DAYS_TO_CHECK)
        first_unprocessed_dates = self.get_first_unprocessed_dates(date_since)
        if first_unprocessed_dates:
            influx.gauge("dailystatement.holes", len(first_unprocessed_dates))
            for campaign_id, date in first_unprocessed_dates.items():
                logger.info("Campaign %s has daily statement hole starting on %s" % (campaign_id, date))
            raise Exception("Daily statement holes found! Has to be looked at immediately!")

    @staticmethod
    def get_first_unprocessed_dates(date_since):
        campaigns = daily_statements_k1.get_campaigns_with_spend(date_since)
        # for each budget associate daily statement for each date from start to end
        # return first date for which daily statement does not exist for each campaign
        query = """
            select
                campaign_id, MIN(b.date)
            FROM (
                SELECT
                    id, campaign_id,
                    generate_series(start_date, end_date, '1 day'::interval) date
                FROM dash_budgetlineitem
                WHERE campaign_id = ANY(%s)
            ) b
            LEFT OUTER JOIN dash_budgetdailystatement s
            ON s.budget_id=b.id AND b.date=s.date
            WHERE s.id IS NULL
            GROUP BY campaign_id
        """
        data = {}
        today = datetime.date.today()
        with connection.cursor() as c:
            c.execute(query, [list(campaigns.values_list("id", flat=True))])
            for campaign_id, first_unprocessed_date in c:
                date = first_unprocessed_date.date()
                if date < today:
                    data[campaign_id] = first_unprocessed_date.date()
        return data
