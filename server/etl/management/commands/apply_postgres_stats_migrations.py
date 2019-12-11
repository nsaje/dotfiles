import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from etl import maintenance
from etl import materialize
from etl.materialize import MATERIALIZED_VIEWS
from utils import zlogging

logger = zlogging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for db_name in settings.STATS_DB_POSTGRES:
            for mv_class in self._required_views():
                logger.info(
                    "Inserting (if not exists) table definition, indexes & statistics", table=mv_class.TABLE_NAME
                )
                self._create_table(db_name, mv_class)
                maintenance.analyze(mv_class.TABLE_NAME, db_name=db_name)

    def _required_views(self):
        for mv_class in MATERIALIZED_VIEWS:
            if mv_class.IS_TEMPORARY_TABLE:
                continue
            if mv_class in (materialize.MasterView, materialize.MasterPublishersView):
                # do not copy mv_master and mv_master_pubs into postgres, too large
                continue
            yield mv_class

    def _create_table(self, db_name, mv_class):
        if mv_class.IS_DERIVED_VIEW:
            sql = mv_class.prepare_create_table_postgres()
        else:
            migration_file = os.path.join(
                os.path.dirname(__file__), "../../../etl/migrations/postgres/", mv_class.TABLE_NAME + ".sql"
            )
            with open(migration_file) as f:
                sql = f.read()
        with connections[db_name].cursor() as cursor:
            cursor.execute(sql)
