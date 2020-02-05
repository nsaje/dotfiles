from django.conf import settings

import redshiftapi
from utils import dates_helper
from utils import s3helpers
from utils.command_helpers import Z1Command

select_query = """
SELECT publisher, exchange, sum(bid_reqs) AS bid_reqs, sum(slots) AS slots, sum(zuid_reqs) AS zuid_reqs
FROM supply_stats
WHERE date >= %s AND blacklisted = false AND adstxt_status != 'HasAdstxt'
GROUP BY exchange, publisher
HAVING sum(bid_reqs) > %s
ORDER BY bid_reqs DESC
"""

unload_query = """
UNLOAD (%s)
TO %s
DELIMITER AS %s
ADDQUOTES
ESCAPE
GZIP
PARALLEL OFF
CREDENTIALS AS %s
"""

bucket = "z1-publishers"
filename = "publishers-%s.csv.gz"
time_format = "%Y-%m-%d_%H_%M_%S"

min_bid_req = 100
num_days = 7


class Command(Z1Command):
    def handle(self, *args, **options):
        today = dates_helper.utc_today()
        date_from = dates_helper.days_before(today, num_days)
        s3 = s3helpers.S3Helper(bucket)
        with redshiftapi.db.get_stats_cursor(db_alias=STATS_DB_HOT_CLUSTER) as cur:
            subquery = cur.mogrify(select_query, (date_from, min_bid_req)).decode("utf-8")
            cur.execute(unload_query, (subquery, "s3://%s/tmp.csv" % bucket, ",", s3helpers.get_credentials_string()))
            dest_file = filename % dates_helper.utc_now().strftime(time_format)
            s3.move("tmp.csv000.gz", dest_file)
