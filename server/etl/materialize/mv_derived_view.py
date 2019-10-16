from django.utils.functional import cached_property

import backtosql
import structlog
from etl import derived_views
from etl import models
from etl import redshift
from redshiftapi import db

from .materialize import Materialize
from .mv_conversions import MVConversions
from .mv_master import MasterView
from .mv_master_publishers import MasterPublishersView
from .mv_touchpoint_conversions import MVTouchpointConversions

logger = structlog.get_logger(__name__)

DEPENDENT_COLUMNS = {"agency_id", "account_id", "campaign_id", "ad_group_id", "content_ad_id"}


class MasterDerivedView(Materialize):
    SOURCE_VIEW = MasterView.TABLE_NAME
    TEMPLATE = "etl/migrations/redshift/mv_master.sql"
    IS_TEMPORARY_TABLE = False
    IS_DERIVED_VIEW = True

    @classmethod
    def create(cls, table_name, breakdown, sortkey, distkey=None, diststyle="key"):
        class Derived(cls):
            TABLE_NAME = table_name
            BREAKDOWN = breakdown
            SORTKEY = sortkey
            DISTKEY = distkey
            DISTSTYLE = diststyle

        return Derived

    @cached_property
    def model(self):
        return models.MVMaster()

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:

                logger.info(
                    "Create materialized view table if not exists",
                    table=self.TABLE_NAME,
                    breakdown=self.BREAKDOWN,
                    job_id=self.job_id,
                )  # noqa
                sql = self.prepare_create_table()
                c.execute(sql)

                c.execute("SELECT count(1) FROM {}".format(self.TABLE_NAME))
                count = c.fetchone()[0]

                if not count:
                    logger.info(
                        "Fill empty materialized view",
                        table=self.TABLE_NAME,
                        breakdown=self.BREAKDOWN,
                        job_id=self.job_id,
                    )  # noqa
                    sql, params = self.prepare_insert_query(None, None)
                    c.execute(sql, params)
                else:
                    logger.info(
                        "Deleting data from table",
                        table=self.TABLE_NAME,
                        date_from=self.date_from,
                        date_to=self.date_to,
                        job_id=self.job_id,
                    )
                    sql, params = redshift.prepare_date_range_delete_query(
                        self.TABLE_NAME, self.date_from, self.date_to, self.account_id
                    )
                    c.execute(sql, params)

                    logger.info(
                        "Inserting data into table",
                        table=self.TABLE_NAME,
                        date_from=self.date_from,
                        date_to=self.date_to,
                        job_id=self.job_id,
                    )
                    sql, params = self.prepare_insert_query(self.date_from, self.date_to)
                    c.execute(sql, params)

    @classmethod
    def prepare_create_table(cls):
        with open(cls.TEMPLATE) as rs:
            sql = derived_views.generate_table_definition(
                cls.TABLE_NAME, rs, cls.BREAKDOWN, cls.SORTKEY, distkey=cls.DISTKEY, diststyle=cls.DISTSTYLE
            )
        return sql

    @classmethod
    def prepare_create_table_postgres(cls):
        template = cls.TEMPLATE.replace("/redshift/", "/postgres/")
        with open(template) as rs:
            assert cls.SORTKEY[0] == "date"
            index = cls.SORTKEY[1:] + ["date"]
            dependencies = [col for col in cls.SORTKEY if col in DEPENDENT_COLUMNS]
            sql = derived_views.generate_table_definition_postgres(
                cls.TABLE_NAME, rs, cls.BREAKDOWN, index, dependencies
            )
        return sql

    def prepare_insert_query(self, date_from, date_to):
        constraints = {}
        if date_from:
            constraints["date__gte"] = date_from

        if date_to:
            constraints["date__lte"] = date_to

        # if date range is not defined reprocess for all accounts as the table was just created
        if date_from and date_to:
            constraints = self._add_account_id_param(constraints)

        constraints = backtosql.Q(self.model, **constraints)

        sql = backtosql.generate_sql(
            "etl_select_insert.sql",
            {
                "breakdown": self.model.get_breakdown(self.BREAKDOWN),
                "aggregates": self.model.get_ordered_aggregates(),
                "destination_table": self.TABLE_NAME,
                "source_table": self.SOURCE_VIEW,
                "constraints": constraints,
                "order": self.model.select_columns(subset=self.SORTKEY),
            },
        )

        return sql, constraints.get_params()


class MasterPublishersDerivedView(MasterDerivedView):
    SOURCE_VIEW = MasterPublishersView.TABLE_NAME
    TEMPLATE = "etl/migrations/redshift/mv_publishers_master.sql"

    @cached_property
    def model(self):
        return models.MVPublishers()


class ConversionsDerivedView(MasterDerivedView):
    SOURCE_VIEW = MVConversions.TABLE_NAME
    TEMPLATE = "etl/migrations/redshift/mv_conversions.sql"

    @cached_property
    def model(self):
        return models.MVConversions()


class TouchpointConversionsDerivedView(MasterDerivedView):
    SOURCE_VIEW = MVTouchpointConversions.TABLE_NAME
    TEMPLATE = "etl/migrations/redshift/mv_touchpointconversions.sql"

    @cached_property
    def model(self):
        return models.MVTouchpointConversions()
