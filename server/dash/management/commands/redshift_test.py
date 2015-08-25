import logging
import random

from django.core.management.base import BaseCommand
from django.db import connections, transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Testing Redshift connection')
        self.setupTables()

    @transaction.atomic
    def setupTables(self, max_lines=10000):
        # this can take quite some time
        query =\
        """
        DROP TABLE IF EXISTS contentadstats;
        CREATE TABLE contentadstats (
            id integer IDENTITY PRIMARY KEY,
            datetime timestamp,
            content_ad_id integer,
            adgroup_id integer,
            source_id integer,
            campaign_id integer,
            account_id integer,

            impressions integer,
            clicks integer,
            cost_cc integer,
            data_cost_cc integer,

            visits integer,
            new_visits integer,
            bounced_visits integer,
            pageviews integer,
            total_time_on_site integer,

            conversions varchar(256),
            touchpoints varchar(256)
        )
        DISTSTYLE EVEN
        SORTKEY (datetime);
        """

        insert_data_queries = []
        for i in xrange(max_lines):
            q = "INSERT INTO contentadstats (datetime,content_ad_id,adgroup_id,source_id,campaign_id,account_id,impressions,clicks,cost_cc,data_cost_cc,visits,new_visits,bounced_visits,pageviews,total_time_on_site,conversions,touchpoints) \
                VALUES ('{dt}', {caid}, {adgid}, {sid}, {cid}, {aid}, {imp}, {clicks}, \
                {ccc}, {datacc}, {visits}, {new_visits}, {bounced_visits}, {pageviews}, {ttos}, '{conversions}', '{touchpoints}') \
            ".format(dt="2015-01-01",
                caid=random.randint(1, 1000),
                adgid=1,
                sid=1,
                cid=1,
                aid=1,
                imp=random.randint(1, 10000),
                clicks=random.randint(1, 100),
                ccc=random.randint(1, 10000000),
                datacc=random.randint(1, 100),
                visits=random.randint(1, 1000),
                new_visits=random.randint(1, 100),
                bounced_visits=random.randint(1,100),
                pageviews=random.randint(1, 1000000),
                ttos=random.randint(1, 60),
                conversions="test",
                touchpoints="test"
            )
            insert_data_queries.append("{q};".format(q=q))

        cursor = connections['redshift'].cursor()
        cursor.execute(query)
        for i in xrange(len(insert_data_queries) / 1000):
            queries = "\n".join(insert_data_queries[i:i+1000])
            print queries
            cursor.execute(queries)
