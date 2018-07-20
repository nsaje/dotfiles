import redshiftapi
from utils.command_helpers import ExceptionCommand
from utils import dates_helper
from utils import s3helpers

select_query = """
SELECT publisher, exchange, sum(bid_reqs) AS num_bid_req
FROM supply_stats
WHERE date >= %s
GROUP BY exchange, publisher
ORDER BY num_bid_req DESC
"""

unload_query = """
UNLOAD (%s)
TO %s
DELIMITER AS %s
ADDQUOTES
GZIP
PARALLEL OFF
CREDENTIALS AS %s
"""

bucket = "z1-publishers"
filename = "publishers-%s.csv.gz"
time_format = "%Y-%m-%d_%H_%M_%S"


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        today = dates_helper.utc_today()
        date_from = dates_helper.days_before(today, 7)
        s3 = s3helpers.S3Helper(bucket)
        with redshiftapi.db.get_stats_cursor() as cur:
            subquery = cur.mogrify(select_query, (date_from,)).decode("utf-8")
            cur.execute(unload_query, (subquery, "s3://%s/tmp.csv" % bucket, ",", s3helpers.get_credentials_string()))
            dest_file = filename % dates_helper.utc_now().strftime(time_format)
            s3.move("tmp.csv000.gz", dest_file)
